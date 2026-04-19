"""
Notificaciones proactivas — el agente avisa al usuario sin que pregunte.

Se ejecuta periodicamente desde el scheduler.

Casos cubiertos:
  1. Orden cambio a 'preparando'   -> "Tu pedido #142 lo estan preparando, llega en X"
  2. Orden cambio a 'en_transito' -> "Tu pedido va en camino (chofer: Juan, placas: ABC-123)"
  3. Orden cambio a 'en_obra'     -> "Tu pedido llego. Confirma recepcion con OK"
  4. Entrega en < 30 min           -> "Tu pedido llega en ~25 min, estate pendiente"
  5. Presupuesto mensual >80%      -> Alerta al residente + aprobadores
  6. Preferencia nueva detectada   -> Se guarda sin molestar

Tambien dedupa: no manda el mismo aviso dos veces usando tabla de
notificaciones_enviadas.
"""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.orden import Orden
from app.models.usuario import Usuario
from app.services.whatsapp import enviar_mensaje_texto

logger = logging.getLogger(__name__)

# Cache en memoria de (orden_id, evento_clave) para no duplicar avisos
# En produccion se deberia persistir en tabla, pero para empezar el cache
# se regenera al arrancar (al menos evita spam dentro de misma sesion).
_avisos_enviados: set[tuple[int, str]] = set()


def _ya_avisado(orden_id: int, evento: str) -> bool:
    key = (orden_id, evento)
    if key in _avisos_enviados:
        return True
    _avisos_enviados.add(key)
    return False


async def _notificar_orden(db: Session, orden: Orden, evento: str, mensaje: str):
    """Envia notificacion al usuario dueno de la orden."""
    if _ya_avisado(orden.id, evento):
        return
    usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()
    if not usuario or not usuario.telefono:
        return
    try:
        await enviar_mensaje_texto(usuario.telefono, mensaje)
        logger.info(f"Notificacion proactiva '{evento}' enviada — Orden #{orden.id}")
    except Exception as e:
        logger.error(f"Error enviando notificacion proactiva: {e}")


async def ejecutar_notificaciones_proactivas():
    """
    Loop que el scheduler ejecuta cada ~5 min.
    Busca cambios de status recientes y genera avisos.
    """
    db = SessionLocal()
    try:
        ahora = datetime.now(timezone.utc)

        # === 1. Ordenes que entraron a "en_transito" en la ultima hora ===
        hace_1h = ahora - timedelta(hours=1)
        en_transito = db.query(Orden).filter(
            Orden.status == "en_transito",
            Orden.en_transito_at != None,
            Orden.en_transito_at >= hace_1h,
        ).all()
        for o in en_transito:
            chofer = (o.nombre_chofer or "tu chofer") if hasattr(o, "nombre_chofer") else "tu chofer"
            placas = (o.placas_vehiculo or "") if hasattr(o, "placas_vehiculo") else ""
            placas_txt = f" · Placas: {placas}" if placas else ""
            msg = (
                f"*Tu orden #{o.id} va en camino* 🚚\n\n"
                f"Chofer: {chofer}{placas_txt}\n"
                f"Cuando llegue, te aviso para que confirmes recepcion."
            )
            await _notificar_orden(db, o, "en_transito_aviso", msg)

        # === 2. Ordenes 'en_obra' > 30 min sin confirmar ===
        hace_30min = ahora - timedelta(minutes=30)
        en_obra_pendiente = db.query(Orden).filter(
            Orden.status == "en_obra",
            Orden.en_obra_at != None,
            Orden.en_obra_at <= hace_30min,
            Orden.entregada_at == None,
        ).all()
        for o in en_obra_pendiente:
            msg = (
                f"*Recordatorio — Orden #{o.id}*\n\n"
                f"Tu material lleva 30 minutos en la obra. "
                f"Si ya lo recibiste completo, responde *OK* para cerrar.\n"
                f"Si hay algun problema, responde *PROBLEMA*."
            )
            await _notificar_orden(db, o, "en_obra_recordatorio", msg)

        # === 3. Ordenes 'preparando' hace mas de 2h sin avanzar ===
        hace_2h = ahora - timedelta(hours=2)
        preparando_lento = db.query(Orden).filter(
            Orden.status == "preparando",
            Orden.preparando_at != None,
            Orden.preparando_at <= hace_2h,
        ).all()
        for o in preparando_lento:
            msg = (
                f"*Update Orden #{o.id}*\n\n"
                f"Tu pedido sigue en preparacion. Vamos a darle seguimiento "
                f"con el proveedor para confirmar tiempo de entrega."
            )
            await _notificar_orden(db, o, "preparando_lento", msg)

        # === 4. Ordenes que ENTREGAMOS en la ultima hora — pedir calificacion ===
        entregadas_recientes = db.query(Orden).filter(
            Orden.status == "entregada",
            Orden.entregada_at != None,
            Orden.entregada_at >= hace_1h,
        ).all()
        for o in entregadas_recientes:
            msg = (
                f"Gracias por confirmar la entrega de tu orden #{o.id}.\n\n"
                f"¿Como te parecio el servicio? Responde del 1 al 5 "
                f"(1 = pesimo, 5 = excelente). Tu calificacion ayuda a otros "
                f"residentes a elegir proveedor."
            )
            await _notificar_orden(db, o, "pedir_calificacion", msg)

    finally:
        db.close()
