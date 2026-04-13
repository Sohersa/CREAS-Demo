"""
Agente Proactivo — el cerebro que conecta todo el flujo de punta a punta.
Ejecuta acciones proactivas: alertas, recordatorios, seguimiento, calificaciones.
Se ejecuta periodicamente via scheduler.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import SessionLocal
from app.models.orden import Orden
from app.models.pedido import Pedido
from app.models.proveedor import Proveedor
from app.models.usuario import Usuario
from app.models.solicitud_proveedor import SolicitudProveedor
from app.models.calificacion import CalificacionProveedor
from app.services.whatsapp import enviar_mensaje_texto

logger = logging.getLogger(__name__)


async def ejecutar_ciclo_agente():
    """Ciclo principal del agente proactivo. Ejecutar cada 10-15 minutos."""
    db = SessionLocal()
    try:
        await alertar_proveedores_entrega_proxima(db)
        await alertar_obra_recepcion(db)
        await pedir_confirmacion_entrega(db)
        await recordar_proveedor_compromiso(db)
        await pedir_calificacion_post_entrega(db)
        await alertar_retraso_entrega(db)
        await escalar_proveedor_fantasma(db)
        await recordar_cotizaciones_pendientes(db)
    except Exception as e:
        logger.error(f"Error en ciclo agente proactivo: {e}")
    finally:
        db.close()


async def alertar_proveedores_entrega_proxima(db: Session):
    """
    Alerta a proveedores que tienen entregas prometidas para HOY o MAÑANA.
    'Recuerda que tienes una entrega pendiente para mañana...'
    """
    ahora = datetime.utcnow()
    manana = ahora + timedelta(days=1)

    ordenes = db.query(Orden).filter(
        Orden.status.in_(["confirmada", "preparando"]),
        Orden.fecha_entrega_prometida.isnot(None),
        Orden.fecha_entrega_prometida <= manana,
        Orden.fecha_entrega_prometida >= ahora - timedelta(hours=2),
    ).all()

    for orden in ordenes:
        proveedor = db.query(Proveedor).filter(Proveedor.id == orden.proveedor_id).first()
        if not proveedor or not proveedor.telefono_whatsapp:
            continue

        # Don't spam — check if we already alerted today (use a simple time check)
        if orden.preparando_at and (ahora - orden.preparando_at).total_seconds() < 3600:
            continue

        fecha_str = orden.fecha_entrega_prometida.strftime("%d/%m a las %H:%M") if orden.fecha_entrega_prometida else "pronto"

        msg = (
            f"📦 *Recordatorio de entrega*\n\n"
            f"Tienes una entrega pendiente:\n"
            f"• Orden #{orden.id}\n"
            f"• Entrega: {fecha_str}\n"
            f"• Dirección: {orden.direccion_entrega or 'Por confirmar'}\n\n"
            f"¿Ya estás preparando el pedido? Responde:\n"
            f"• *PREPARANDO {orden.id}* — si ya lo estás armando\n"
            f"• *PROBLEMA {orden.id}* — si hay algún inconveniente"
        )

        await enviar_mensaje_texto(proveedor.telefono_whatsapp, msg)
        logger.info(f"[Agente] Recordatorio de entrega enviado a proveedor {proveedor.nombre} para orden {orden.id}")


async def alertar_obra_recepcion(db: Session):
    """
    Alerta al personal de obra que un pedido está en camino.
    'Tu pedido está en camino, prepárate para recibir...'
    """
    ordenes = db.query(Orden).filter(
        Orden.status == "en_transito",
    ).all()

    ahora = datetime.utcnow()

    for orden in ordenes:
        # Only alert once when status changed to en_transito (within last 5 min)
        if not orden.en_transito_at:
            continue
        mins_desde_transito = (ahora - orden.en_transito_at).total_seconds() / 60
        if mins_desde_transito > 5:
            continue

        usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()
        if not usuario:
            continue

        chofer_info = ""
        if orden.nombre_chofer:
            chofer_info = f"• Chofer: {orden.nombre_chofer}\n"
        if orden.telefono_chofer:
            chofer_info += f"• Tel chofer: {orden.telefono_chofer}\n"
        if orden.placas_vehiculo:
            chofer_info += f"• Placas: {orden.placas_vehiculo}\n"
        if orden.tipo_vehiculo:
            chofer_info += f"• Vehículo: {orden.tipo_vehiculo}\n"

        msg = (
            f"🚛 *¡Tu pedido va en camino!*\n\n"
            f"Orden #{orden.id} salió del proveedor.\n"
            f"{chofer_info}\n"
            f"📍 Dirección de entrega: {orden.direccion_entrega or 'La indicada'}\n\n"
            f"Prepárate para recibir el material. Cuando llegue, responde:\n"
            f"• *RECIBIDO {orden.id}* — si todo llegó bien\n"
            f"• *PROBLEMA {orden.id}* — si hay algún inconveniente"
        )

        await enviar_mensaje_texto(usuario.telefono, msg)
        logger.info(f"[Agente] Alerta de recepción enviada a {usuario.nombre} para orden {orden.id}")


async def pedir_confirmacion_entrega(db: Session):
    """
    Si la orden lleva más de 2 horas en 'en_obra' sin confirmación,
    insistir al usuario para que confirme.
    """
    ahora = datetime.utcnow()
    hace_2h = ahora - timedelta(hours=2)

    ordenes = db.query(Orden).filter(
        Orden.status == "en_obra",
        Orden.en_obra_at.isnot(None),
        Orden.en_obra_at <= hace_2h,
    ).all()

    for orden in ordenes:
        # Max 2 recordatorios
        # Use a simple heuristic: check hours since en_obra
        horas = (ahora - orden.en_obra_at).total_seconds() / 3600
        if horas > 24:
            continue  # Too old, skip
        if 2 < horas < 2.25 or 6 < horas < 6.25:  # At 2h and 6h marks
            usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()
            if not usuario:
                continue

            msg = (
                f"📋 *¿Recibiste tu pedido?*\n\n"
                f"Orden #{orden.id} fue marcada como entregada en obra hace {int(horas)} horas.\n\n"
                f"Necesito tu confirmación:\n"
                f"• *RECIBIDO {orden.id}* — todo llegó bien\n"
                f"• *PROBLEMA {orden.id}* — hubo algún inconveniente\n\n"
                f"Tu respuesta nos ayuda a calificar al proveedor."
            )

            await enviar_mensaje_texto(usuario.telefono, msg)
            logger.info(f"[Agente] Recordatorio de confirmación para orden {orden.id}")


async def recordar_proveedor_compromiso(db: Session):
    """
    Para órdenes confirmadas donde el proveedor no ha actualizado status
    a 'preparando' después de 4 horas, recordarle.
    """
    ahora = datetime.utcnow()
    hace_4h = ahora - timedelta(hours=4)

    ordenes = db.query(Orden).filter(
        Orden.status == "confirmada",
        Orden.confirmada_at.isnot(None),
        Orden.confirmada_at <= hace_4h,
    ).all()

    for orden in ordenes:
        horas = (ahora - orden.confirmada_at).total_seconds() / 3600
        if horas > 48:
            continue
        # Only at ~4h and ~12h marks
        if not (3.9 < horas < 4.2 or 11.9 < horas < 12.2):
            continue

        proveedor = db.query(Proveedor).filter(Proveedor.id == orden.proveedor_id).first()
        if not proveedor or not proveedor.telefono_whatsapp:
            continue

        msg = (
            f"⏰ *Actualización pendiente*\n\n"
            f"Tienes la orden #{orden.id} confirmada desde hace {int(horas)} horas.\n"
            f"¿Ya estás preparando el pedido?\n\n"
            f"Responde:\n"
            f"• *PREPARANDO {orden.id}* — ya lo estoy armando\n"
            f"• *LISTO {orden.id}* — ya está listo para enviar\n"
            f"• *PROBLEMA {orden.id}* — tengo un inconveniente"
        )

        await enviar_mensaje_texto(proveedor.telefono_whatsapp, msg)
        logger.info(f"[Agente] Recordatorio de compromiso a {proveedor.nombre} para orden {orden.id}")


async def pedir_calificacion_post_entrega(db: Session):
    """
    24 horas después de entrega, pedir calificación al usuario si no la ha dado.
    """
    ahora = datetime.utcnow()
    hace_24h = ahora - timedelta(hours=24)
    hace_25h = ahora - timedelta(hours=25)

    ordenes = db.query(Orden).filter(
        Orden.status == "entregada",
        Orden.entregada_at.isnot(None),
        Orden.entregada_at.between(hace_25h, hace_24h),
    ).all()

    for orden in ordenes:
        # Check if already rated
        cal = db.query(CalificacionProveedor).filter(
            CalificacionProveedor.orden_id == orden.id,
            CalificacionProveedor.estrellas_usuario.isnot(None),
        ).first()
        if cal:
            continue

        usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()
        proveedor = db.query(Proveedor).filter(Proveedor.id == orden.proveedor_id).first()
        if not usuario or not proveedor:
            continue

        msg = (
            f"⭐ *¿Cómo estuvo tu pedido?*\n\n"
            f"Hace 24 horas recibiste la orden #{orden.id} de *{proveedor.nombre}*.\n\n"
            f"¿Cómo calificas la experiencia? (1-5 estrellas)\n"
            f"Responde con un número del 1 al 5:\n"
            f"1 ⭐ Muy mal\n"
            f"2 ⭐⭐ Mal\n"
            f"3 ⭐⭐⭐ Regular\n"
            f"4 ⭐⭐⭐⭐ Bien\n"
            f"5 ⭐⭐⭐⭐⭐ Excelente\n\n"
            f"También puedes agregar un comentario después del número."
        )

        await enviar_mensaje_texto(usuario.telefono, msg)
        logger.info(f"[Agente] Solicitud de calificación enviada para orden {orden.id}")


async def alertar_retraso_entrega(db: Session):
    """
    Si la fecha_entrega_prometida ya pasó y la orden no está entregada,
    alertar a AMBOS: usuario y proveedor.
    """
    ahora = datetime.utcnow()

    ordenes = db.query(Orden).filter(
        Orden.status.in_(["confirmada", "preparando", "en_transito"]),
        Orden.fecha_entrega_prometida.isnot(None),
        Orden.fecha_entrega_prometida < ahora,
    ).all()

    for orden in ordenes:
        retraso_horas = (ahora - orden.fecha_entrega_prometida).total_seconds() / 3600
        if retraso_horas > 72:
            continue  # Too old
        # Alert at 1h, 4h, and 12h marks
        if not (0.9 < retraso_horas < 1.2 or 3.9 < retraso_horas < 4.2 or 11.9 < retraso_horas < 12.2):
            continue

        proveedor = db.query(Proveedor).filter(Proveedor.id == orden.proveedor_id).first()
        usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()

        retraso_str = f"{int(retraso_horas)} hora{'s' if retraso_horas > 1 else ''}"

        # Alert supplier
        if proveedor and proveedor.telefono_whatsapp:
            msg_prov = (
                f"⚠️ *Entrega retrasada*\n\n"
                f"La orden #{orden.id} lleva *{retraso_str}* de retraso.\n"
                f"La entrega estaba prometida para: {orden.fecha_entrega_prometida.strftime('%d/%m %H:%M')}\n\n"
                f"¿Qué pasó? Responde con una actualización.\n"
                f"Si no vas a poder entregar, avísanos para buscar alternativa."
            )
            await enviar_mensaje_texto(proveedor.telefono_whatsapp, msg_prov)

        # Alert buyer
        if usuario:
            msg_user = (
                f"⚠️ *Aviso: retraso en tu pedido*\n\n"
                f"Tu orden #{orden.id} lleva {retraso_str} de retraso.\n"
                f"Ya contactamos al proveedor para una actualización.\n"
                f"Te avisamos en cuanto tengamos respuesta."
            )
            await enviar_mensaje_texto(usuario.telefono, msg_user)

        logger.info(f"[Agente] Alerta de retraso para orden {orden.id} ({retraso_str})")


async def recordar_cotizaciones_pendientes(db: Session):
    """
    Si hay solicitudes a proveedores que llevan >15 min sin respuesta,
    enviar recordatorio (máximo 2).
    """
    ahora = datetime.utcnow()
    hace_15m = ahora - timedelta(minutes=15)

    solicitudes = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.status == "enviada",
        SolicitudProveedor.enviada_at.isnot(None),
        SolicitudProveedor.enviada_at <= hace_15m,
        SolicitudProveedor.recordatorios_enviados < 2,
    ).all()

    for sol in solicitudes:
        minutos = (ahora - sol.enviada_at).total_seconds() / 60
        # Only remind at 15min and 25min marks
        if not (14 < minutos < 16 or 24 < minutos < 26):
            continue

        proveedor = db.query(Proveedor).filter(Proveedor.id == sol.proveedor_id).first()
        if not proveedor or not proveedor.telefono_whatsapp:
            continue

        msg = (
            f"👋 *¿Pudiste revisar la cotización?*\n\n"
            f"Te mandé una solicitud hace {int(minutos)} minutos.\n"
            f"El cliente está esperando. ¿Tienes disponibilidad?\n\n"
            f"Si no manejas estos materiales, responde *NO TENGO*."
        )

        await enviar_mensaje_texto(proveedor.telefono_whatsapp, msg)
        sol.recordatorios_enviados += 1
        sol.recordatorio_at = ahora
        sol.status = "recordatorio_enviado"
        db.commit()

        logger.info(f"[Agente] Recordatorio #{sol.recordatorios_enviados} a {proveedor.nombre}")


async def escalar_proveedor_fantasma(db: Session):
    """
    Detecta ordenes confirmadas donde el proveedor no ha actualizado status.
    Escalacion progresiva:
      - 4h: Alertar al cliente
      - 8h: Segundo aviso al proveedor
      - 24h: Ofrecer al cliente re-cotizar con otro proveedor
    """
    ahora = datetime.utcnow()

    # Ordenes en "confirmada" por mas tiempo del esperado (proveedor no avanza)
    ordenes = db.query(Orden).filter(
        Orden.status == "confirmada",
        Orden.confirmada_at.isnot(None),
    ).all()

    for orden in ordenes:
        horas = (ahora - orden.confirmada_at).total_seconds() / 3600
        if horas < 4 or horas > 48:
            continue

        usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()
        proveedor = db.query(Proveedor).filter(Proveedor.id == orden.proveedor_id).first()

        # 4h mark — alertar cliente
        if 3.9 < horas < 4.2:
            if usuario:
                await enviar_mensaje_texto(
                    usuario.telefono,
                    f"Tu orden #{orden.id}: el proveedor *{proveedor.nombre if proveedor else ''}* "
                    f"aun no confirma que esta preparando tu pedido.\n"
                    f"Estamos dandole seguimiento."
                )

        # 8h mark — segundo aviso al proveedor
        elif 7.9 < horas < 8.2:
            if proveedor and proveedor.telefono_whatsapp:
                await enviar_mensaje_texto(
                    proveedor.telefono_whatsapp,
                    f"URGENTE — Llevas 8 horas sin confirmar la orden #{orden.id}.\n"
                    f"El cliente esta esperando.\n\n"
                    f"Responde *PREPARANDO {orden.id}* si ya lo estas armando,\n"
                    f"o *PROBLEMA {orden.id}* si tienes algun inconveniente."
                )

        # 24h mark — ofrecer alternativa al cliente
        elif 23.9 < horas < 24.2:
            if usuario:
                await enviar_mensaje_texto(
                    usuario.telefono,
                    f"Tu orden #{orden.id} lleva 24 horas sin movimiento del proveedor.\n\n"
                    f"Quieres que contacte a otro proveedor?\n"
                    f"Responde *SI* para re-cotizar con alternativas, o *esperar* para darle mas tiempo."
                )

        logger.info(f"[Agente] Escalacion proveedor fantasma — Orden #{orden.id} ({int(horas)}h)")
