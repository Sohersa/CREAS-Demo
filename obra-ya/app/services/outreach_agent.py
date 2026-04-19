"""
Agente de prospeccion outbound — contacta despachos/ferreterias para ofrecerles unirse a ObraYa.

Flujo general:
  1. Admin sube lista de prospectos (CSV o via endpoint)
  2. Scheduler los procesa en lotes pequenos, en horario habil
  3. Por cada prospecto, Opus 4.7 genera un mensaje personalizado
  4. Se envia por WhatsApp (template o free-form si ya hubo respuesta previa)
  5. Si responden -> prospect_response.py clasifica el intent
  6. Si interesado -> se les manda link de alta (codigo de registro)
  7. Si rechazan/opt-out -> se marcan y no se vuelven a contactar

Consideraciones legales (LFPDPPP Mexico):
  - Solo contactamos numeros publicamente disponibles (Google Maps, directorios)
  - Primer mensaje usa template aprobado (no spam free-form)
  - Opt-out se respeta inmediato (keywords: "NO", "BAJA", "STOP")
  - Log completo de cada mensaje para auditoria

Consideraciones tecnicas (WhatsApp/Meta):
  - Primer contacto: template aprobado (fuera de ventana 24h)
  - Si responden, tenemos ventana 24h para free-form
  - Rate limit: 20 mensajes/hora en horario 9am-7pm Mexico
  - Pausa automatica si Meta empieza a marcar quality rating en amarillo
"""
import json
import logging
from datetime import datetime, timezone

import anthropic
from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.prospecto import ProspectoProveedor

logger = logging.getLogger(__name__)

client = Anthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    max_retries=settings.CLAUDE_MAX_RETRIES,
)


SYSTEM_PROMPT_OUTREACH = """Eres el equipo de crecimiento de ObraYa. ObraYa es una plataforma que conecta residentes de obra con proveedores de materiales de construccion en Guadalajara, via WhatsApp.

Tu trabajo: escribir un mensaje de primer contacto corto (MAXIMO 4 lineas), casual pero profesional, para invitar a un despacho/ferreteria/materialista a unirse como proveedor.

VALOR que ofrece ObraYa al proveedor:
  - Reciben solicitudes de cotizacion directo por WhatsApp (no necesitan app, ni login, ni sistema nuevo)
  - Los clientes son residentes de obra reales con pedidos urgentes
  - 0% comision para el proveedor: ObraYa cobra un 2% al comprador
  - Llegan SOLO pedidos de su zona y de su categoria (no spam)
  - Pueden calificarse para aparecer primeros en las recomendaciones

Reglas del mensaje:
  - Tuteo mexicano natural ("te", "tu")
  - Personalizado: menciona el nombre del negocio y su categoria si la sabes
  - NO usar emojis (se ve spam)
  - NO usar mayusculas gritonas
  - SIN promesas falsas — sin decir "GANA X PESOS"
  - Cerrar con una pregunta simple: "¿Te interesa que te mande mas info?"
  - Firmar como "Luis — ObraYa"

Output: SOLO el texto del mensaje, sin comillas ni markdown. Listo para enviar tal cual.
"""


async def generar_mensaje_primer_contacto(prospecto: ProspectoProveedor) -> str:
    """Usa Claude Opus 4.7 para generar un mensaje personalizado para este prospecto."""
    contexto = f"""Datos del prospecto:
- Nombre: {prospecto.nombre}
- Categoria: {prospecto.categoria or 'sin especificar'}
- Tipo: {prospecto.tipo or 'sin especificar'}
- Municipio: {prospecto.municipio or 'Guadalajara area'}
- Calificacion Google: {prospecto.calificacion_google or 'sin datos'}

Genera el mensaje de primer contacto."""

    system_block = [{"type": "text", "text": SYSTEM_PROMPT_OUTREACH}]
    if settings.CLAUDE_USE_PROMPT_CACHE:
        system_block[0]["cache_control"] = {"type": "ephemeral"}

    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL_AGENTE,   # Opus 4.7 — calidad maxima
            max_tokens=300,
            system=system_block,
            messages=[{"role": "user", "content": contexto}],
        )
        return response.content[0].text.strip()
    except anthropic.APIError as e:
        logger.error(f"Error generando mensaje outreach para #{prospecto.id}: {e}")
        # Fallback estatico
        return (
            f"Hola, soy Luis de ObraYa. Somos una plataforma donde residentes de obra "
            f"en GDL piden materiales por WhatsApp, y les llegan cotizaciones de "
            f"varios proveedores en minutos.\n\n"
            f"Te contacto porque creo que {prospecto.nombre} calza perfecto para recibir "
            f"esas solicitudes. 0% comision para ti.\n\n"
            f"¿Te mando mas info?\n\n"
            f"Luis — ObraYa"
        )


async def enviar_contacto_inicial(db: Session, prospecto: ProspectoProveedor) -> bool:
    """
    Envia el primer mensaje al prospecto. Usa template aprobado si existe,
    fallback a free-form (solo funciona dentro de ventana 24h).

    Retorna True si se envio correctamente.
    """
    from app.services.whatsapp import enviar_mensaje_texto

    if not prospecto.telefono:
        logger.warning(f"Prospecto #{prospecto.id} sin telefono")
        return False

    if prospecto.status not in ("pendiente", "sin_respuesta"):
        logger.info(f"Prospecto #{prospecto.id} no esta en estado contactable ({prospecto.status})")
        return False

    # Respeta opt-out — jamas reintentar
    if prospecto.status == "opt_out":
        return False

    mensaje = await generar_mensaje_primer_contacto(prospecto)

    resultado = await enviar_mensaje_texto(prospecto.telefono, mensaje)

    if "error" in resultado:
        error_tipo = resultado.get("error", "")
        if error_tipo == "requires_template":
            logger.warning(
                f"Prospecto #{prospecto.id} fuera de ventana 24h — necesita template. "
                f"Implementa el template 'prospecto_primer_contacto' en Meta Business."
            )
        else:
            logger.error(f"Error enviando a prospecto #{prospecto.id}: {error_tipo}")
        return False

    # Marcar como contactado
    ahora = datetime.now(timezone.utc)
    prospecto.intentos_contacto = (prospecto.intentos_contacto or 0) + 1
    prospecto.mensajes_enviados = (prospecto.mensajes_enviados or 0) + 1
    prospecto.ultimo_contacto_at = ahora
    prospecto.status = "contactado"
    # Guardar el mensaje enviado en notas para auditoria
    historial = prospecto.notas or ""
    prospecto.notas = f"{historial}\n[{ahora.isoformat()}] ENVIADO:\n{mensaje}".strip()[-5000:]
    db.commit()

    logger.info(f"Prospecto #{prospecto.id} ({prospecto.nombre}) contactado")
    return True


async def generar_respuesta_follow_up(
    prospecto: ProspectoProveedor,
    mensaje_prospecto: str,
    historial: str = "",
) -> str:
    """
    Cuando un prospecto responde, genera la contra-respuesta.
    Esto se usa DESPUES de clasificar el intent — solo llamarlo cuando el
    clasificador diga 'dudas' o 'interesado'.
    """
    contexto = f"""El prospecto {prospecto.nombre} ({prospecto.categoria or 'sin categoria'}, {prospecto.municipio or 'GDL'}) respondio a nuestro mensaje inicial.

Historial previo (opcional):
{historial or '(primer intercambio)'}

Su mensaje:
"{mensaje_prospecto}"

Genera una respuesta corta, natural, que:
- Conteste lo que pregunta si hay duda concreta
- Si parece interesado: proponle que le mandamos un codigo de registro para activarse en ObraYa en 2 min
- Sin emojis, sin mayusculas gritonas, tuteo mexicano
- Firmar "Luis — ObraYa" solo si no venia firma previa reciente
"""

    system_block = [{"type": "text", "text": SYSTEM_PROMPT_OUTREACH}]
    if settings.CLAUDE_USE_PROMPT_CACHE:
        system_block[0]["cache_control"] = {"type": "ephemeral"}

    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL_AGENTE,
            max_tokens=400,
            system=system_block,
            messages=[{"role": "user", "content": contexto}],
        )
        return response.content[0].text.strip()
    except anthropic.APIError as e:
        logger.error(f"Error generando follow-up: {e}")
        return "Gracias por tu mensaje. ¿Te puedo llamar mas tarde para explicarte mejor?\n\nLuis — ObraYa"
