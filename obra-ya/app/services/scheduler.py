"""
Scheduler de tareas en background — mantiene ObraYa vivo sin intervención humana.

Usa asyncio puro (sin APScheduler) para correr tareas periódicas:
1. Recordatorios a proveedores que no contestan (cada 10 min)
2. Auto-construcción de comparativa cuando hay suficientes respuestas (cada 5 min)
3. Recordatorio de confirmación de entrega (cada 30 min)
4. Alertas de órdenes estancadas (cada 1 hora)
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.database import SessionLocal
from app.models.pedido import Pedido
from app.models.orden import Orden
from app.models.solicitud_proveedor import SolicitudProveedor
from app.services.cotizacion_activa import (
    enviar_recordatorios,
    hay_suficientes_respuestas,
    tiempo_agotado,
    marcar_sin_respuesta,
)
from app.services.comparativa_activa import generar_comparativa_desde_respuestas
from app.services.notificaciones import notificar_recordatorio_confirmacion
from app.services.whatsapp import enviar_mensaje_texto
from app.services.agente_proactivo import ejecutar_ciclo_agente
from app.services.outreach_scheduler import ejecutar_ciclo_outreach

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def _get_db():
    """Crea una sesión de BD standalone (fuera del ciclo request/response)."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


async def _loop(nombre: str, intervalo_segundos: int, fn):
    """Ejecuta fn() en loop con el intervalo dado. Nunca muere."""
    logger.info(f"Scheduler: tarea '{nombre}' iniciada (cada {intervalo_segundos}s)")
    while True:
        await asyncio.sleep(intervalo_segundos)
        try:
            await fn()
        except Exception as e:
            logger.error(f"Scheduler [{nombre}]: error — {e}", exc_info=True)


# ============================================================
# 1. RECORDATORIOS A PROVEEDORES (cada 10 min)
# ============================================================

async def _tarea_recordatorios_proveedores():
    """
    Busca pedidos en status 'cotizando' con solicitudes pendientes
    que llevan 10+ minutos sin respuesta. Envía recordatorios (max 2).
    """
    db = _get_db()
    try:
        pedidos_cotizando = db.query(Pedido).filter(
            Pedido.status == "cotizando",
        ).all()

        for pedido in pedidos_cotizando:
            # Verificar si hay solicitudes pendientes con 10+ min
            pendientes = db.query(SolicitudProveedor).filter(
                SolicitudProveedor.pedido_id == pedido.id,
                SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"]),
                SolicitudProveedor.recordatorios_enviados < 2,
            ).all()

            if not pendientes:
                continue

            resumen = pedido.mensaje_original[:100] if pedido.mensaje_original else f"Pedido #{pedido.id}"
            await enviar_recordatorios(db, pedido.id, pedido_resumen=resumen)

        logger.info(f"Recordatorios: revisados {len(pedidos_cotizando)} pedidos en cotización")
    finally:
        db.close()


# ============================================================
# 2. AUTO-BUILD COMPARATIVA (cada 5 min)
# ============================================================

async def _tarea_auto_comparativa():
    """
    Revisa pedidos en status 'cotizando'. Si ya hay suficientes respuestas
    o se agotó el timeout, arma la comparativa y la envía al usuario.
    """
    db = _get_db()
    try:
        pedidos_cotizando = db.query(Pedido).filter(
            Pedido.status == "cotizando",
        ).all()

        for pedido in pedidos_cotizando:
            suficientes = hay_suficientes_respuestas(db, pedido.id)
            timeout = tiempo_agotado(db, pedido.id)

            if not suficientes and not timeout:
                continue

            # Si es timeout, marcar las pendientes como sin_respuesta
            if timeout and not suficientes:
                marcar_sin_respuesta(db, pedido.id)
                # Revisar de nuevo — puede que no haya NINGUNA respuesta
                from app.services.cotizacion_activa import obtener_respuestas
                respuestas = obtener_respuestas(db, pedido.id)
                if not respuestas:
                    logger.warning(
                        f"Pedido #{pedido.id}: timeout sin ninguna respuesta de proveedores"
                    )
                    # Notificar al usuario que nadie contestó
                    if pedido.usuario_id:
                        from app.models.usuario import Usuario
                        usuario = db.query(Usuario).filter(Usuario.id == pedido.usuario_id).first()
                        if usuario and usuario.telefono:
                            try:
                                await enviar_mensaje_texto(
                                    usuario.telefono,
                                    f"Pedido #{pedido.id}: ningún proveedor respondió a tiempo. "
                                    f"Quieres que intente con otros proveedores? Responde *SI* para reintentar."
                                )
                            except Exception as e:
                                logger.error(f"Error notificando timeout sin respuestas: {e}")
                    pedido.status = "sin_respuesta"
                    db.commit()
                    continue
            elif timeout:
                marcar_sin_respuesta(db, pedido.id)

            # Generar comparativa
            comparativa_texto = generar_comparativa_desde_respuestas(db, pedido.id)
            if not comparativa_texto:
                continue

            # Enviar al usuario por WhatsApp
            if pedido.usuario_id:
                from app.models.usuario import Usuario
                usuario = db.query(Usuario).filter(Usuario.id == pedido.usuario_id).first()
                if usuario and usuario.telefono:
                    try:
                        await enviar_mensaje_texto(usuario.telefono, comparativa_texto)
                        logger.info(f"Comparativa enviada al usuario — Pedido #{pedido.id}")
                    except Exception as e:
                        logger.error(f"Error enviando comparativa: {e}")

            # Actualizar status del pedido — usar "enviado" (unificado con webhook)
            pedido.status = "enviado"
            db.commit()

            motivo = "suficientes respuestas" if suficientes else "timeout"
            logger.info(f"Auto-comparativa generada — Pedido #{pedido.id} ({motivo})")

    finally:
        db.close()


# ============================================================
# 3. RECORDATORIO CONFIRMACIÓN DE ENTREGA (cada 30 min)
# ============================================================

async def _tarea_recordatorio_entrega():
    """
    Busca órdenes en status 'en_obra' por más de 2 horas.
    Envía recordatorio al usuario para que confirme recepción.
    """
    db = _get_db()
    try:
        ahora = datetime.now(timezone.utc)
        limite = ahora - timedelta(hours=2)

        ordenes_en_obra = db.query(Orden).filter(
            Orden.status == "en_obra",
            Orden.en_obra_at != None,
        ).all()

        enviados = 0
        for orden in ordenes_en_obra:
            en_obra_at = orden.en_obra_at
            if en_obra_at.tzinfo is None:
                en_obra_at = en_obra_at.replace(tzinfo=timezone.utc)

            if en_obra_at > limite:
                continue  # Todavía no cumple las 2 horas

            # Enviar recordatorio
            try:
                notificar_recordatorio_confirmacion(db, orden)
                enviados += 1
                logger.info(f"Recordatorio de entrega enviado — Orden #{orden.id}")
            except Exception as e:
                logger.error(f"Error enviando recordatorio entrega Orden #{orden.id}: {e}")

        if enviados:
            logger.info(f"Recordatorios de entrega: {enviados} enviados")
    finally:
        db.close()


# ============================================================
# 4. ALERTAS DE ÓRDENES ESTANCADAS (cada 1 hora)
# ============================================================

async def _tarea_ordenes_estancadas():
    """
    Busca órdenes en 'confirmada' o 'preparando' por más de 24 horas.
    Registra warning en logs para seguimiento operativo.
    """
    db = _get_db()
    try:
        ahora = datetime.now(timezone.utc)
        limite_24h = ahora - timedelta(hours=24)

        # Órdenes confirmadas hace más de 24h
        ordenes_confirmadas = db.query(Orden).filter(
            Orden.status == "confirmada",
            Orden.confirmada_at != None,
        ).all()

        for orden in ordenes_confirmadas:
            confirmada_at = orden.confirmada_at
            if confirmada_at.tzinfo is None:
                confirmada_at = confirmada_at.replace(tzinfo=timezone.utc)
            if confirmada_at <= limite_24h:
                horas = int((ahora - confirmada_at).total_seconds() / 3600)
                logger.warning(
                    f"ORDEN ESTANCADA — Orden #{orden.id} en 'confirmada' hace {horas}h "
                    f"(proveedor_id={orden.proveedor_id}, usuario_id={orden.usuario_id})"
                )

        # Órdenes preparando hace más de 24h
        ordenes_preparando = db.query(Orden).filter(
            Orden.status == "preparando",
            Orden.preparando_at != None,
        ).all()

        for orden in ordenes_preparando:
            preparando_at = orden.preparando_at
            if preparando_at.tzinfo is None:
                preparando_at = preparando_at.replace(tzinfo=timezone.utc)
            if preparando_at <= limite_24h:
                horas = int((ahora - preparando_at).total_seconds() / 3600)
                logger.warning(
                    f"ORDEN ESTANCADA — Orden #{orden.id} en 'preparando' hace {horas}h "
                    f"(proveedor_id={orden.proveedor_id}, usuario_id={orden.usuario_id})"
                )

    finally:
        db.close()


# ============================================================
# INICIAR SCHEDULER
# ============================================================

async def iniciar_scheduler():
    """
    Lanza todas las tareas en background como asyncio tasks.
    Se llama desde el startup de FastAPI.
    """
    logger.info("Iniciando scheduler de tareas en background...")

    asyncio.create_task(_loop(
        "recordatorios_proveedores",
        intervalo_segundos=600,  # 10 minutos
        fn=_tarea_recordatorios_proveedores,
    ))

    asyncio.create_task(_loop(
        "auto_comparativa",
        intervalo_segundos=300,  # 5 minutos
        fn=_tarea_auto_comparativa,
    ))

    asyncio.create_task(_loop(
        "recordatorio_entrega",
        intervalo_segundos=1800,  # 30 minutos
        fn=_tarea_recordatorio_entrega,
    ))

    asyncio.create_task(_loop(
        "ordenes_estancadas",
        intervalo_segundos=3600,  # 1 hora
        fn=_tarea_ordenes_estancadas,
    ))

    asyncio.create_task(_loop(
        "agente_proactivo",
        intervalo_segundos=600,  # 10 minutos
        fn=ejecutar_ciclo_agente,
    ))

    asyncio.create_task(_loop(
        "outreach",
        intervalo_segundos=300,  # 5 minutos (2 prospectos por ciclo, max 20/hora)
        fn=ejecutar_ciclo_outreach,
    ))

    logger.info("Scheduler: 6 tareas en background activas")
