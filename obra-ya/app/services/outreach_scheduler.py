"""
Scheduler paced para outreach — envia mensajes a prospectos respetando:
- Horario habil (9am-7pm hora Mexico)
- Rate limit (default 20 mensajes/hora para no triggerear anti-spam de Meta)
- Quality rating: si Meta empieza a bajarlo, pausamos automaticamente

Se llama desde el scheduler global cada N minutos.
"""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import SessionLocal
from app.models.prospecto import ProspectoProveedor

logger = logging.getLogger(__name__)

# Hora Mexico Central (UTC-6 casi todo el ano, UTC-5 con horario de verano)
# No usamos zoneinfo para evitar dependencia de tzdata en Windows
TZ_MX_OFFSET_HOURS = -6

# Configuracion de outreach (se puede mover a Settings)
OUTREACH_RATE_PER_HOUR = 20
HORA_INICIO = 9   # 9 AM
HORA_FIN = 19     # 7 PM


def _en_horario_habil() -> bool:
    """True si estamos en horario habil Mexico (lun-vie 9am-7pm)."""
    ahora_mx = datetime.now(timezone.utc) + timedelta(hours=TZ_MX_OFFSET_HOURS)
    if ahora_mx.weekday() >= 5:  # sabado, domingo
        return False
    return HORA_INICIO <= ahora_mx.hour < HORA_FIN


async def _verificar_quality_ok() -> bool:
    """Verifica que el quality rating de Meta no este en RED/YELLOW."""
    from app.services.whatsapp_health import verificar_whatsapp
    estado = await verificar_whatsapp()
    if not estado.get("ok"):
        return False
    quality = estado.get("detalles", {}).get("quality_rating", "").upper()
    # GREEN es seguro. YELLOW ya es warning, pausamos outreach.
    return quality == "GREEN"


async def ejecutar_ciclo_outreach():
    """
    Tarea del scheduler. Cada ciclo:
    1. Valida horario habil + quality rating
    2. Calcula cuantos mensajes podemos enviar (rate limit)
    3. Toma prospectos en status 'pendiente' (los mas antiguos primero)
    4. Envia a cada uno, marca como 'contactado'
    """
    if not _en_horario_habil():
        return  # silencioso, no loguea cada vez

    if not await _verificar_quality_ok():
        logger.warning("Outreach pausado — WhatsApp quality rating no es GREEN")
        return

    db = SessionLocal()
    try:
        # Cuantos mandamos este ciclo (el scheduler corre cada 5 min -> 20/hora = ~2 por ciclo)
        # Ajustar si cambia el intervalo del scheduler
        cupo_por_ciclo = max(1, OUTREACH_RATE_PER_HOUR // 12)

        ahora = datetime.now(timezone.utc)
        prospectos = db.query(ProspectoProveedor).filter(
            ProspectoProveedor.activo == True,
            ProspectoProveedor.status == "pendiente",
        ).order_by(ProspectoProveedor.created_at.asc()).limit(cupo_por_ciclo).all()

        if not prospectos:
            return  # nada que hacer

        logger.info(f"Outreach: procesando {len(prospectos)} prospectos")

        from app.services.outreach_agent import enviar_contacto_inicial
        enviados = 0
        for p in prospectos:
            ok = await enviar_contacto_inicial(db, p)
            if ok:
                enviados += 1

        logger.info(f"Outreach ciclo: {enviados}/{len(prospectos)} enviados")

        # Follow-up automatico: prospectos contactados hace 3 dias sin respuesta
        # marcarlos como sin_respuesta (para que el reporte lo sepa)
        limite_sin_resp = ahora - timedelta(days=3)
        sin_resp = db.query(ProspectoProveedor).filter(
            ProspectoProveedor.status == "contactado",
            ProspectoProveedor.mensajes_recibidos == 0,
            ProspectoProveedor.ultimo_contacto_at < limite_sin_resp,
        ).all()
        for p in sin_resp:
            p.status = "sin_respuesta"
        if sin_resp:
            db.commit()
            logger.info(f"Outreach: {len(sin_resp)} prospectos marcados sin_respuesta")

    finally:
        db.close()
