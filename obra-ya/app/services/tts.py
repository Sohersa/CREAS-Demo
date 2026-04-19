"""
Text-to-speech para mensajes de voz por WhatsApp.

Por default usa ElevenLabs (mejor calidad en espanol mexicano).
Fallback a OpenAI TTS si no hay ELEVENLABS_API_KEY.

Se integra al webhook: cuando el usuario prefiere audios (preferencia guardada
via memory tool), el agente responde con nota de voz en vez de texto.

REQUIERE:
  ELEVENLABS_API_KEY (en .env) — https://elevenlabs.io/app/settings/api-keys
  o
  OPENAI_API_KEY (en .env) — si no tienes ElevenLabs
"""
import os
import logging
import asyncio
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# Voz por default — Rachel (ElevenLabs, neutral espanol)
# Para voz mexicana: "piTKgcLEGmPE4e6mEKli" (Male MX) o crear custom voice clone.
ELEVEN_VOICE_ID_DEFAULT = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "nova")  # nova / alloy / echo / fable / onyx / shimmer


async def texto_a_audio(texto: str, provider: Optional[str] = None) -> Optional[bytes]:
    """
    Convierte texto a audio MP3. Retorna bytes del audio o None si falla.

    provider: 'elevenlabs' | 'openai' | None (auto-detecta)
    """
    if not texto or not texto.strip():
        return None

    if provider is None:
        provider = "elevenlabs" if ELEVEN_API_KEY else "openai"

    if provider == "elevenlabs" and ELEVEN_API_KEY:
        return await _tts_elevenlabs(texto)
    if provider == "openai" and OPENAI_API_KEY:
        return await _tts_openai(texto)
    logger.warning("TTS no configurado — faltan ELEVENLABS_API_KEY u OPENAI_API_KEY")
    return None


async def _tts_elevenlabs(texto: str) -> Optional[bytes]:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID_DEFAULT}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": texto[:4000],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.2,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                return r.content
            logger.error(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    except httpx.RequestError as e:
        logger.error(f"ElevenLabs request error: {e}")
    return None


async def _tts_openai(texto: str) -> Optional[bytes]:
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "tts-1",
        "voice": OPENAI_TTS_VOICE,
        "input": texto[:4000],
        "response_format": "mp3",
    }
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                return r.content
            logger.error(f"OpenAI TTS error {r.status_code}: {r.text[:200]}")
    except httpx.RequestError as e:
        logger.error(f"OpenAI TTS error: {e}")
    return None


async def enviar_audio_por_whatsapp(telefono: str, audio_bytes: bytes) -> dict:
    """
    Envia un audio MP3 por WhatsApp Cloud API.

    Flujo:
    1. Sube media a Meta (POST /PHONE_ID/media) con multipart
    2. Recibe media_id
    3. Manda mensaje type=audio con ese media_id
    """
    if not audio_bytes:
        return {"error": "sin audio"}

    url_media = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_ID}/media"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            # 1. Upload
            files = {
                "file": ("response.mp3", audio_bytes, "audio/mpeg"),
                "type": (None, "audio/mpeg"),
                "messaging_product": (None, "whatsapp"),
            }
            r_up = await c.post(url_media, headers=headers, files=files)
            if r_up.status_code != 200:
                logger.error(f"Error subiendo audio: {r_up.status_code} {r_up.text[:200]}")
                return {"error": "upload_failed", "detail": r_up.text}
            media_id = r_up.json().get("id")

            # 2. Send message with media
            url_msg = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_ID}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": telefono,
                "type": "audio",
                "audio": {"id": media_id},
            }
            r_send = await c.post(
                url_msg,
                headers={**headers, "Content-Type": "application/json"},
                json=payload,
            )
            if r_send.status_code == 200:
                logger.info(f"Audio enviado a {telefono}")
                return r_send.json()
            return {"error": "send_failed", "detail": r_send.text[:200]}

    except Exception as e:
        logger.error(f"Error enviando audio: {e}")
        return {"error": str(e)}


async def responder_con_voz(telefono: str, texto: str) -> bool:
    """
    Shortcut: genera audio con TTS y lo envia por WhatsApp.
    Retorna True si el audio se envio correctamente.
    """
    audio = await texto_a_audio(texto)
    if not audio:
        return False
    resultado = await enviar_audio_por_whatsapp(telefono, audio)
    return "error" not in resultado
