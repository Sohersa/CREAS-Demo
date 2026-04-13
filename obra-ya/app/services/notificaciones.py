"""
Servicio de notificaciones WhatsApp — mensajes de seguimiento de ordenes.
Tipo Uber: avisa cada cambio de status con mensajes cortos y accionables.

El residente de obra esta en campo, con polvo, viendo su celular entre colados.
Los mensajes tienen que ser CORTOS, CLAROS, y con accion obvia.
"""
import json
import logging
from app.models.orden import Orden
from app.models.usuario import Usuario
from app.models.proveedor import Proveedor
from app.models.incidencia import IncidenciaEntrega
from app.models.calificacion import CalificacionProveedor
from app.services.whatsapp import enviar_mensaje_texto
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _obtener_telefono(db: Session, usuario_id: int) -> str | None:
    """Obtiene el telefono del usuario."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    return usuario.telefono if usuario else None


def _nombre_proveedor(db: Session, proveedor_id: int) -> str:
    """Nombre del proveedor."""
    prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    return prov.nombre if prov else "Proveedor"


def _resumen_items(items_json: str) -> str:
    """Genera resumen corto de los items de la orden."""
    try:
        items = json.loads(items_json)
        lineas = []
        for item in items[:4]:  # Max 4 items en resumen
            lineas.append(f"  • {item.get('cantidad', '?')} {item.get('unidad', '')} {item.get('producto', '')}")
        if len(items) > 4:
            lineas.append(f"  + {len(items) - 4} mas...")
        return "\n".join(lineas)
    except Exception:
        return "  (ver detalle en la orden)"


def notificar_orden_confirmada(db: Session, orden: Orden):
    """Cuando el usuario elige proveedor y se crea la orden."""
    telefono = _obtener_telefono(db, orden.usuario_id)
    if not telefono:
        return

    proveedor = _nombre_proveedor(db, orden.proveedor_id)
    items = _resumen_items(orden.items)

    mensaje = (
        f"*Pedido confirmado con {proveedor}*\n\n"
        f"Orden #{orden.id}\n"
        f"{items}\n\n"
        f"Total: ${orden.total:,.0f} MXN\n"
        f"Entrega: {orden.direccion_entrega or 'por confirmar'}\n\n"
        f"Te voy avisando el status. Si hay cualquier tema, mandame mensaje."
    )

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: orden_confirmada → {telefono}")


def notificar_orden_confirmada_proveedor(db: Session, orden: Orden):
    """
    Notifica al PROVEEDOR que fue seleccionado y tiene un pedido confirmado.
    CRITICO: Sin esto, el proveedor no sabe que tiene que preparar material.
    Busca primero al vendedor asignado, si no al proveedor principal.
    """
    from app.models.vendedor import Vendedor

    proveedor = db.query(Proveedor).filter(Proveedor.id == orden.proveedor_id).first()
    if not proveedor:
        logger.error(f"Proveedor #{orden.proveedor_id} no encontrado para orden #{orden.id}")
        return

    # Buscar vendedor disponible para este proveedor
    telefono_destino = None
    vendedor = db.query(Vendedor).filter(
        Vendedor.proveedor_id == proveedor.id,
        Vendedor.activo == True,
        Vendedor.disponible == True,
    ).order_by(Vendedor.solicitudes_atendidas.asc()).first()

    if vendedor and vendedor.telefono_whatsapp:
        telefono_destino = vendedor.telefono_whatsapp
    elif proveedor.telefono:
        telefono_destino = proveedor.telefono
    else:
        logger.error(f"Sin telefono para proveedor #{proveedor.id} en orden #{orden.id}")
        return

    items = _resumen_items(orden.items)

    # Obtener nombre del cliente
    usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()
    cliente_nombre = usuario.nombre if usuario else "Cliente"

    mensaje = (
        f"*PEDIDO CONFIRMADO — Orden #{orden.id}*\n\n"
        f"El cliente *{cliente_nombre}* te eligio.\n\n"
        f"Materiales:\n{items}\n\n"
        f"Total: ${orden.total:,.0f} MXN\n"
        f"Entrega en: {orden.direccion_entrega or 'por confirmar'}\n"
    )

    if orden.fecha_entrega_prometida:
        mensaje += f"Fecha prometida: {orden.fecha_entrega_prometida.strftime('%d/%m/%Y %H:%M')}\n"

    mensaje += (
        f"\nResponde:\n"
        f"  *PREPARANDO {orden.id}* → ya estas preparando el pedido\n"
        f"  *EN CAMINO {orden.id}* → ya salio el camion\n"
        f"  *PROBLEMA {orden.id}* → si hay algun inconveniente"
    )

    enviar_mensaje_texto(telefono_destino, mensaje)
    logger.info(f"Notificacion: orden_confirmada_proveedor → {telefono_destino} (Orden #{orden.id})")


def notificar_preparando(db: Session, orden: Orden):
    """Cuando el proveedor empieza a preparar/cargar."""
    telefono = _obtener_telefono(db, orden.usuario_id)
    if not telefono:
        return

    proveedor = _nombre_proveedor(db, orden.proveedor_id)

    mensaje = (
        f"Tu pedido #{orden.id} ya se esta preparando en *{proveedor}*.\n\n"
        f"Te aviso cuando salga el camion."
    )

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: preparando → {telefono}")


def notificar_en_transito(db: Session, orden: Orden):
    """Cuando sale el camion — incluye datos del chofer si los hay."""
    telefono = _obtener_telefono(db, orden.usuario_id)
    if not telefono:
        return

    mensaje = f"*Tu material va en camino!*\n\nPedido #{orden.id}\n"

    if orden.nombre_chofer:
        mensaje += f"Chofer: {orden.nombre_chofer}\n"
    if orden.placas_vehiculo:
        mensaje += f"Placas: {orden.placas_vehiculo}\n"
    if orden.telefono_chofer:
        mensaje += f"Tel chofer: {orden.telefono_chofer}\n"
    if orden.tipo_vehiculo:
        mensaje += f"Vehiculo: {orden.tipo_vehiculo}\n"

    mensaje += "\nTe aviso cuando llegue a tu obra."

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: en_transito → {telefono}")


def notificar_en_obra(db: Session, orden: Orden):
    """Cuando el camion llega a la obra — pide confirmacion."""
    telefono = _obtener_telefono(db, orden.usuario_id)
    if not telefono:
        return

    mensaje = (
        f"*El camion ya llego a tu obra.*\n\n"
        f"Pedido #{orden.id}\n\n"
        f"Verifica el material y responde:\n"
        f"  *OK* → todo bien, confirmo recepcion\n"
        f"  *Problema* → reportar incidencia"
    )

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: en_obra → {telefono}")


def notificar_recordatorio_confirmacion(db: Session, orden: Orden):
    """30 min despues de en_obra, si no ha confirmado."""
    telefono = _obtener_telefono(db, orden.usuario_id)
    if not telefono:
        return

    mensaje = (
        f"Recibiste el material del pedido #{orden.id}?\n\n"
        f"Responde *OK* si todo bien, o dime si hubo algun problema."
    )

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: recordatorio → {telefono}")


def notificar_entrega_completada(db: Session, orden: Orden, calificacion: CalificacionProveedor = None):
    """Confirmacion final con calificacion auto-calculada."""
    telefono = _obtener_telefono(db, orden.usuario_id)
    if not telefono:
        return

    proveedor = _nombre_proveedor(db, orden.proveedor_id)

    mensaje = (
        f"*Entrega completada!*\n\n"
        f"Pedido #{orden.id} — {proveedor}\n"
        f"Total: ${orden.total:,.0f} MXN\n"
    )

    if calificacion:
        puntual = "a tiempo" if calificacion.puntualidad >= 4.0 else "con retraso"
        mensaje += (
            f"\nCalificacion auto: {calificacion.calificacion_total}/5.0\n"
            f"Puntualidad: {puntual}\n"
        )

    if orden.tiempo_entrega_minutos:
        horas = orden.tiempo_entrega_minutos // 60
        mins = orden.tiempo_entrega_minutos % 60
        if horas > 0:
            mensaje += f"Tiempo de entrega: {horas}h {mins}min\n"
        else:
            mensaje += f"Tiempo de entrega: {mins} min\n"

    mensaje += "\nGracias por usar ObraYa!"

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: entrega_completada → {telefono}")


def notificar_incidencia_registrada(db: Session, incidencia: IncidenciaEntrega):
    """Confirma al usuario que su reporte fue registrado."""
    telefono = _obtener_telefono(db, incidencia.usuario_id)
    if not telefono:
        return

    proveedor = _nombre_proveedor(db, incidencia.proveedor_id)

    tipo_legible = {
        "cantidad_incorrecta": "Cantidad incorrecta",
        "especificacion": "Material diferente al pedido",
        "entrega_tarde": "Entrega fuera de horario",
        "material_danado": "Material danado",
        "no_llego": "No llego el pedido",
        "cobro_diferente": "Cobro diferente al cotizado",
        "otro": "Otro problema",
    }.get(incidencia.tipo, incidencia.tipo)

    mensaje = (
        f"*Reporte registrado*\n\n"
        f"Pedido #{incidencia.orden_id} — {proveedor}\n"
        f"Problema: {tipo_legible}\n"
    )

    if incidencia.cantidad_esperada and incidencia.cantidad_recibida:
        mensaje += (
            f"Esperado: {incidencia.cantidad_esperada} {incidencia.unidad or ''}\n"
            f"Recibido: {incidencia.cantidad_recibida} {incidencia.unidad or ''}\n"
        )

    mensaje += (
        f"Severidad: {incidencia.severidad}\n\n"
        f"Ya le damos seguimiento. Se refleja en la calificacion del proveedor."
    )

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: incidencia_registrada → {telefono}")


def notificar_orden_cancelada(db: Session, orden: Orden, motivo: str = ""):
    """Cuando se cancela una orden."""
    telefono = _obtener_telefono(db, orden.usuario_id)
    if not telefono:
        return

    proveedor = _nombre_proveedor(db, orden.proveedor_id)
    mensaje = f"*Orden #{orden.id} cancelada*\nProveedor: {proveedor}\n"
    if motivo:
        mensaje += f"Motivo: {motivo}\n"
    mensaje += "\nSi necesitas re-cotizar, mandame mensaje."

    enviar_mensaje_texto(telefono, mensaje)
    logger.info(f"Notificacion: cancelada → {telefono}")


def enviar_notificacion_por_status(db: Session, orden: Orden, calificacion=None):
    """
    Dispatcher central — envia la notificacion correcta segun el status actual.
    Se llama desde orden_service.avanzar_status().
    """
    dispatch = {
        "confirmada": notificar_orden_confirmada,
        "preparando": notificar_preparando,
        "en_transito": notificar_en_transito,
        "en_obra": notificar_en_obra,
        "cancelada": notificar_orden_cancelada,
    }

    fn = dispatch.get(orden.status)
    if fn:
        try:
            fn(db, orden)
        except Exception as e:
            logger.error(f"Error enviando notificacion {orden.status}: {e}")

    # Entregada tiene logica especial (incluye calificacion)
    if orden.status == "entregada":
        try:
            notificar_entrega_completada(db, orden, calificacion)
        except Exception as e:
            logger.error(f"Error enviando notificacion entrega: {e}")
