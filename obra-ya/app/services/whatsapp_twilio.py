"""
Servicio de integracion con WhatsApp via Twilio.
Alternativa a la API de Meta Cloud — misma interfaz publica.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


async def enviar_mensaje_texto(telefono: str, mensaje: str) -> dict:
    """
    Envia un mensaje de texto por WhatsApp via Twilio.
    telefono: numero con codigo de pais (ej: 5213312345678)
    mensaje: texto del mensaje
    """
    # Twilio tiene limite de ~1600 caracteres por mensaje
    if len(mensaje) > 1600:
        partes = partir_mensaje(mensaje, 1600)
        resultados = []
        for parte in partes:
            resultado = await _enviar_texto(telefono, parte)
            resultados.append(resultado)
        return resultados[-1]

    return await _enviar_texto(telefono, mensaje)


async def _enviar_texto(telefono: str, mensaje: str) -> dict:
    """Envio interno de un solo mensaje via Twilio."""
    url = TWILIO_API_URL.format(sid=settings.TWILIO_ACCOUNT_SID)
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Normalize: strip any existing + prefix to avoid double-plus
    tel_clean = telefono.lstrip("+")
    data = {
        "From": settings.TWILIO_WHATSAPP_NUMBER,
        "To": f"whatsapp:+{tel_clean}",
        "Body": mensaje,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, auth=auth)
        if response.status_code in (200, 201):
            logger.info(f"[Twilio] Mensaje enviado a {telefono}")
            return response.json()
        else:
            logger.error(f"[Twilio] Error enviando mensaje: {response.status_code} - {response.text}")
            return {"error": response.text}


async def marcar_como_leido(message_id: str) -> dict:
    """
    No-op para Twilio — la API de Twilio no soporta marcar como leido.
    """
    logger.debug(f"[Twilio] marcar_como_leido es no-op (message_id={message_id})")
    return {"status": "ok"}


async def descargar_audio(media_url: str) -> bytes:
    """
    Descarga un archivo de audio de Twilio.
    Twilio envia la URL del media directamente en el webhook (MediaUrl0),
    a diferencia de Meta que envia un media_id.
    """
    if not media_url:
        logger.error("[Twilio] URL de audio vacia")
        return b""

    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    async with httpx.AsyncClient() as client:
        response = await client.get(media_url, auth=auth, follow_redirects=True)
        if response.status_code == 200:
            return response.content
        else:
            logger.error(f"[Twilio] Error descargando audio: {response.status_code}")
            return b""


def parsear_webhook_twilio(form_data: dict) -> dict | None:
    """
    Parsea el cuerpo del webhook de Twilio (form-urlencoded) y extrae la info relevante.
    Devuelve dict con: telefono, nombre, tipo_mensaje, contenido, message_id
    O None si no es un mensaje valido.

    Campos de Twilio:
      From: "whatsapp:+521XXXXXXXXXX"
      Body: "the message text"
      MessageSid: unique message ID
      ProfileName: sender name
      NumMedia: "0" or "1"
      MediaUrl0: URL of media if NumMedia > 0
      MediaContentType0: "audio/ogg" etc
    """
    try:
        from_field = form_data.get("From", "")
        body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        profile_name = form_data.get("ProfileName", "")
        num_media = int(form_data.get("NumMedia", "0"))

        if not from_field or not message_sid:
            return None

        # Extraer numero de telefono: "whatsapp:+521XXXXXXXXXX" -> "521XXXXXXXXXX"
        telefono = from_field.replace("whatsapp:", "").replace("+", "").strip()

        resultado = {
            "telefono": telefono,
            "nombre": profile_name,
            "message_id": message_sid,
            "timestamp": "",
            "source": "twilio",
        }

        if num_media > 0:
            content_type = form_data.get("MediaContentType0", "")
            media_url = form_data.get("MediaUrl0", "")

            if "audio" in content_type:
                resultado["tipo_mensaje"] = "audio"
                resultado["contenido"] = media_url
            elif "image" in content_type:
                resultado["tipo_mensaje"] = "imagen"
                resultado["contenido"] = media_url
            else:
                resultado["tipo_mensaje"] = "otro"
                resultado["contenido"] = media_url
        else:
            resultado["tipo_mensaje"] = "texto"
            resultado["contenido"] = body

        return resultado

    except Exception as e:
        logger.error(f"[Twilio] Error parseando webhook: {e}")
        return None


def partir_mensaje(texto: str, max_chars: int = 1600) -> list[str]:
    """Parte un mensaje largo en pedazos respetando saltos de linea."""
    if len(texto) <= max_chars:
        return [texto]

    partes = []
    while texto:
        if len(texto) <= max_chars:
            partes.append(texto)
            break

        # Buscar el ultimo salto de linea antes del limite
        corte = texto.rfind("\n", 0, max_chars)
        if corte == -1:
            corte = max_chars

        partes.append(texto[:corte])
        texto = texto[corte:].lstrip("\n")

    return partes
