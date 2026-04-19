"""
Clasificador de respuestas de prospectos (outreach inbound replies).

Cuando un despacho/ferreteria responde a nuestro mensaje de outreach,
esta funcion analiza el mensaje y lo clasifica para decidir el next step.

Usa Claude Haiku 4.5 con structured output (barato y rapido).
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


SYSTEM_PROMPT_CLASIFICADOR = """Eres un clasificador de respuestas comerciales en B2B mexicano.

Recibes el mensaje que un despacho de materiales mando respondiendo a un primer contacto de outreach. Tu trabajo es clasificar el intent del mensaje.

Intents posibles:
- INTERESADO: dice que quiere saber mas, que le interesa, pide info, manda "si", "dale", "cuentame", "mandame", etc.
- DUDAS: hace preguntas concretas sobre el producto/servicio sin comprometerse aun.
- NO_INTERESADO: dice que no le interesa, "gracias pero no", "ya tengo", "no es para mi", sin ser opt-out explicito.
- OPT_OUT: pide explicitamente NO ser contactado de nuevo: "no vuelvan a escribir", "baja", "borrenme", "STOP", "NO MAS MENSAJES".
- YA_ES_PROVEEDOR: dice que ya esta en la plataforma, que ya lo contactaron antes, "ya les vendo", "ya soy proveedor".
- CONTACTO_EQUIVOCADO: dice que no son despacho de materiales, "numero equivocado", "no vendemos eso".
- OTRO: cualquier otra cosa — saludos, smalltalk, off-topic.

Tambien estimas:
- score_interes: numero de 0 a 100 del nivel de interes expresado
- sentimiento: positivo/neutral/negativo"""

SCHEMA_CLASIFICACION = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["INTERESADO", "DUDAS", "NO_INTERESADO", "OPT_OUT",
                     "YA_ES_PROVEEDOR", "CONTACTO_EQUIVOCADO", "OTRO"],
        },
        "score_interes": {"type": "integer"},
        "sentimiento": {"type": "string", "enum": ["positivo", "neutral", "negativo"]},
        "razon": {"type": "string"},
    },
    "required": ["intent", "score_interes", "sentimiento", "razon"],
    "additionalProperties": False,
}


async def clasificar_respuesta(texto: str) -> dict:
    """
    Clasifica un mensaje de respuesta. Retorna {intent, score_interes, sentimiento, razon}.
    """
    system_block = [{"type": "text", "text": SYSTEM_PROMPT_CLASIFICADOR}]
    if settings.CLAUDE_USE_PROMPT_CACHE:
        system_block[0]["cache_control"] = {"type": "ephemeral"}

    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL_PARSER,  # Haiku 4.5
            max_tokens=300,
            system=system_block,
            messages=[{"role": "user", "content": f'Mensaje del prospecto:\n"{texto}"\n\nClasificalo.'}],
            output_config={
                "format": {"type": "json_schema", "schema": SCHEMA_CLASIFICACION},
            },
        )
        return json.loads(response.content[0].text)
    except anthropic.APIError as e:
        logger.error(f"Error clasificando respuesta: {e}")
        return {
            "intent": "OTRO",
            "score_interes": 0,
            "sentimiento": "neutral",
            "razon": f"error: {e}",
        }


async def procesar_respuesta_prospecto(
    db: Session,
    prospecto: ProspectoProveedor,
    mensaje: str,
) -> dict:
    """
    Procesa una respuesta entrante de un prospecto:
    1. Clasifica el intent
    2. Actualiza el status + score
    3. Decide next action (respuesta automatica, opt-out, conversion, etc)
    4. Ejecuta la accion

    Returns: dict con intent y accion ejecutada
    """
    ahora = datetime.now(timezone.utc)
    prospecto.mensajes_recibidos = (prospecto.mensajes_recibidos or 0) + 1
    prospecto.ultima_respuesta = mensaje[:500]
    prospecto.ultima_respuesta_at = ahora

    # Clasificar
    clasificacion = await clasificar_respuesta(mensaje)
    intent = clasificacion["intent"]
    score = clasificacion["score_interes"]
    prospecto.score_interes = max(prospecto.score_interes or 0, score)

    logger.info(
        f"Prospecto #{prospecto.id} ({prospecto.nombre}) — intent={intent} "
        f"score={score} sentimiento={clasificacion['sentimiento']}"
    )

    from app.services.whatsapp import enviar_mensaje_texto

    accion = "ninguna"

    # === OPT OUT (respeta inmediato) ===
    if intent == "OPT_OUT":
        prospecto.status = "opt_out"
        prospecto.activo = False
        prospecto.razon_rechazo = "Opt-out explicito"
        await enviar_mensaje_texto(
            prospecto.telefono,
            "Entendido. No te contactamos mas.\n\nSi en el futuro cambias de opinion, "
            "escribenos a wa.me/5213318526297."
        )
        accion = "opt_out_confirmado"

    # === NO INTERESADO (respetamos pero dejamos puerta) ===
    elif intent == "NO_INTERESADO":
        prospecto.status = "rechazado"
        prospecto.razon_rechazo = clasificacion.get("razon", "")[:200]
        await enviar_mensaje_texto(
            prospecto.telefono,
            "Sin problema, gracias por tu respuesta. Si mas adelante cambias de opinion "
            "o tienes dudas, aqui estamos.\n\nLuis — ObraYa"
        )
        accion = "rechazo_confirmado"

    # === YA ES PROVEEDOR — marcar y cerrar ===
    elif intent == "YA_ES_PROVEEDOR":
        prospecto.status = "descartado"
        prospecto.razon_rechazo = "Ya es proveedor o ya contactado antes"
        await enviar_mensaje_texto(
            prospecto.telefono,
            "Perfecto, gracias por confirmar. Cualquier duda estoy a la orden.\n\nLuis"
        )
        accion = "ya_proveedor"

    elif intent == "CONTACTO_EQUIVOCADO":
        prospecto.status = "invalido"
        prospecto.razon_rechazo = "No es despacho de materiales"
        accion = "invalido"

    # === INTERESADO / DUDAS — sigue conversacion ===
    elif intent in ("INTERESADO", "DUDAS"):
        prospecto.status = "interesado" if intent == "INTERESADO" else "dialogo_activo"

        from app.services.outreach_agent import generar_respuesta_follow_up
        respuesta = await generar_respuesta_follow_up(
            prospecto, mensaje, historial=prospecto.notas or ""
        )

        # Si esta muy interesado (>70), ofrecerle link de registro directo
        if score >= 70:
            # Crear codigo de registro para facilitar onboarding
            from app.models.proveedor import Proveedor
            import secrets
            codigo = secrets.token_hex(3).upper()
            # Pre-crear proveedor stub con codigo de registro
            proveedor_stub = Proveedor(
                nombre=prospecto.nombre,
                tipo=prospecto.tipo or "mediano",
                telefono_whatsapp=prospecto.telefono,
                direccion=prospecto.direccion,
                municipio=prospecto.municipio,
                categorias=f'["{prospecto.categoria}"]' if prospecto.categoria else "[]",
                codigo_registro=codigo,
                activo=False,  # se activa cuando mande REGISTRO codigo
            )
            db.add(proveedor_stub)
            db.flush()
            prospecto.proveedor_id = proveedor_stub.id

            respuesta += (
                f"\n\nPara activar tu cuenta en 1 minuto, solo mandame:\n\n"
                f"*REGISTRO {codigo}*\n\n"
                f"Con eso quedas dentro y empiezas a recibir solicitudes."
            )
            accion = "codigo_enviado"
        else:
            accion = "dudas_respondidas"

        await enviar_mensaje_texto(prospecto.telefono, respuesta)
        prospecto.mensajes_enviados = (prospecto.mensajes_enviados or 0) + 1

    # === OTRO — smalltalk / saludo — responder cortes ===
    else:
        await enviar_mensaje_texto(
            prospecto.telefono,
            "Hola, te contacte hace rato por ObraYa. ¿Te interesa que te mande mas info "
            "sobre como funciona?\n\nLuis"
        )
        accion = "follow_up_generico"

    # Guardar en notas el mensaje recibido + accion tomada
    historial = prospecto.notas or ""
    prospecto.notas = (
        f"{historial}\n[{ahora.isoformat()}] RECIBIDO ({intent}, score={score}):\n"
        f"{mensaje[:300]}\nACCION: {accion}"
    ).strip()[-5000:]
    db.commit()

    return {"intent": intent, "score": score, "accion": accion}
