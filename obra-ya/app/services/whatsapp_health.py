"""
Diagnostico de salud de WhatsApp — valida token, phone_id, y templates.

Uso:
  from app.services.whatsapp_health import verificar_whatsapp
  estado = await verificar_whatsapp()

Errores tipicos de Meta:
  - 190 / subcode 463: token expirado
  - 190 / subcode 467: token invalidado (credenciales cambiadas)
  - 190 / subcode 458: usuario deshabilitado
  - 100: parametros mal formados
  - 131026: mensaje bloqueado (el destinatario no es tester)
  - 131047: fuera de la ventana de 24h (requiere template)
"""
import logging
from datetime import datetime, timezone
from typing import TypedDict

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v21.0"


class EstadoWhatsApp(TypedDict):
    ok: bool
    status: str                    # "healthy" | "token_expired" | "token_invalid" | "phone_id_invalid" | "not_configured" | "error"
    mensaje: str
    detalles: dict
    sugerencia: str


async def verificar_whatsapp() -> EstadoWhatsApp:
    """
    Hace una llamada a Meta Graph API para validar token y phone_id.
    No envia mensajes, solo consulta el endpoint de info del numero.
    """
    if settings.WHATSAPP_PROVIDER.lower() == "twilio":
        return await _verificar_twilio()

    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_ID:
        return {
            "ok": False,
            "status": "not_configured",
            "mensaje": "WHATSAPP_TOKEN o WHATSAPP_PHONE_ID no configurados",
            "detalles": {
                "tiene_token": bool(settings.WHATSAPP_TOKEN),
                "tiene_phone_id": bool(settings.WHATSAPP_PHONE_ID),
            },
            "sugerencia": "Setea las variables en .env",
        }

    url = f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_ID}"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers)
    except httpx.RequestError as e:
        return {
            "ok": False,
            "status": "error",
            "mensaje": f"No se pudo contactar a Meta Graph API: {e}",
            "detalles": {"exception": str(e)},
            "sugerencia": "Verifica tu conexion a internet o firewall.",
        }

    # 200 = todo bien
    if r.status_code == 200:
        data = r.json()
        return {
            "ok": True,
            "status": "healthy",
            "mensaje": "WhatsApp esta funcionando correctamente",
            "detalles": {
                "phone_number": data.get("display_phone_number", "?"),
                "verified_name": data.get("verified_name", "?"),
                "quality_rating": data.get("quality_rating", "?"),
                "platform_type": data.get("platform_type", "?"),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
            "sugerencia": "",
        }

    # 401 = problema de autenticacion
    if r.status_code == 401:
        try:
            err = r.json().get("error", {})
        except Exception:
            err = {}

        codigo = err.get("code")
        subcodigo = err.get("error_subcode")
        mensaje_meta = err.get("message", r.text)

        # Token expirado (duracion limitada) - caso mas comun
        if codigo == 190 and subcodigo == 463:
            # Extraer la fecha de expiracion del mensaje si esta
            fecha = ""
            if "expired on" in mensaje_meta:
                try:
                    fecha = mensaje_meta.split("expired on")[1].split(".")[0].strip()
                except Exception:
                    pass
            return {
                "ok": False,
                "status": "token_expired",
                "mensaje": f"El token de WhatsApp EXPIRO{' el '+fecha if fecha else ''}",
                "detalles": {
                    "error_code": codigo,
                    "error_subcode": subcodigo,
                    "meta_message": mensaje_meta,
                    "fecha_expiracion": fecha,
                },
                "sugerencia": (
                    "Genera un nuevo token en Meta Business "
                    "(developers.facebook.com > tu app > WhatsApp > API Setup). "
                    "Para evitar esto, configura un System User con token permanente: "
                    "business.facebook.com > Settings > System Users > crea uno 'Admin' > "
                    "genera token con permisos whatsapp_business_messaging + whatsapp_business_management. "
                    "Ese token NO expira nunca."
                ),
            }

        # Token invalidado manualmente (credenciales cambiadas)
        if codigo == 190 and subcodigo == 467:
            return {
                "ok": False,
                "status": "token_invalid",
                "mensaje": "El token fue invalidado (posible cambio de credenciales)",
                "detalles": {"error_code": codigo, "error_subcode": subcodigo, "meta_message": mensaje_meta},
                "sugerencia": "Regenera el token desde Meta Business Portal.",
            }

        # Otros errores de auth
        return {
            "ok": False,
            "status": "token_invalid",
            "mensaje": f"Token invalido: {mensaje_meta[:200]}",
            "detalles": {"error_code": codigo, "error_subcode": subcodigo, "raw": mensaje_meta},
            "sugerencia": "Verifica que el WHATSAPP_TOKEN sea valido y no haya sido revocado.",
        }

    # 404 = phone_id incorrecto
    if r.status_code == 404:
        return {
            "ok": False,
            "status": "phone_id_invalid",
            "mensaje": f"WHATSAPP_PHONE_ID ({settings.WHATSAPP_PHONE_ID}) no existe",
            "detalles": {"response": r.text[:300]},
            "sugerencia": "Copia el phone_id correcto desde Meta Business > WhatsApp > API Setup.",
        }

    # Cualquier otro error
    return {
        "ok": False,
        "status": "error",
        "mensaje": f"Meta API respondio {r.status_code}",
        "detalles": {"response": r.text[:300], "status_code": r.status_code},
        "sugerencia": "Revisa el log de Meta Business Portal.",
    }


async def _verificar_twilio() -> EstadoWhatsApp:
    """Valida credenciales de Twilio (proveedor alternativo)."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return {
            "ok": False,
            "status": "not_configured",
            "mensaje": "Twilio configurado como provider pero faltan credenciales",
            "detalles": {},
            "sugerencia": "Setea TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en .env",
        }

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}.json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            )
    except httpx.RequestError as e:
        return {
            "ok": False, "status": "error",
            "mensaje": f"No se pudo contactar Twilio: {e}",
            "detalles": {}, "sugerencia": "",
        }

    if r.status_code == 200:
        data = r.json()
        return {
            "ok": True,
            "status": "healthy",
            "mensaje": "Twilio funcionando",
            "detalles": {
                "account_status": data.get("status", "?"),
                "from_number": settings.TWILIO_WHATSAPP_NUMBER,
            },
            "sugerencia": "",
        }

    return {
        "ok": False,
        "status": "token_invalid",
        "mensaje": f"Twilio respondio {r.status_code}",
        "detalles": {"response": r.text[:300]},
        "sugerencia": "Verifica TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN.",
    }
