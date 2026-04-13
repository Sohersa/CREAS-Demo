"""
Servicio de transcripcion de audio (voz a texto).
Usa OpenAI Whisper API via httpx (no requiere SDK de openai).
"""
import io
import os
import logging

import httpx

logger = logging.getLogger(__name__)

OPENAI_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


async def transcribir_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio a texto.
    Intenta OpenAI Whisper primero, luego Groq Whisper como fallback.
    """
    if not audio_bytes:
        logger.warning("Audio vacio recibido — nada que transcribir")
        return ""

    if len(audio_bytes) < 100:
        logger.warning(f"Audio muy corto ({len(audio_bytes)} bytes) — probablemente error de descarga")
        return ""

    logger.info(f"Transcribiendo audio de {len(audio_bytes)} bytes...")

    # Intentar con OpenAI Whisper
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        texto = await _transcribir_whisper(audio_bytes, OPENAI_WHISPER_URL, openai_key, "whisper-1")
        if texto:
            return texto

    # Fallback: Groq Whisper (gratis)
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        texto = await _transcribir_whisper(audio_bytes, GROQ_WHISPER_URL, groq_key, "whisper-large-v3")
        if texto:
            return texto

    logger.error("No hay API key configurada para transcripcion (OPENAI_API_KEY o GROQ_API_KEY)")
    return ""


async def _transcribir_whisper(audio_bytes: bytes, url: str, api_key: str, model: str) -> str:
    """
    Transcribe audio usando cualquier API compatible con Whisper (OpenAI o Groq).
    Envia el audio como multipart/form-data.
    """
    try:
        files = {
            "file": ("audio.ogg", io.BytesIO(audio_bytes), "audio/ogg"),
        }
        data = {
            "model": model,
            "language": "es",
            "response_format": "text",
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, data=data, files=files)

            if response.status_code == 200:
                texto = response.text.strip()
                logger.info(f"Audio transcrito ({len(texto)} chars): {texto[:100]}...")
                return texto
            else:
                logger.error(f"Whisper error {response.status_code}: {response.text[:300]}")
                return ""

    except Exception as e:
        logger.error(f"Error transcribiendo audio: {e}")
        return ""
