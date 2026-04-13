"""
Servicio principal del agente de IA.
Usa Claude para interpretar pedidos de materiales de construccion.
Persiste historial de conversacion en la base de datos.
"""
import json
import logging
from anthropic import Anthropic
from sqlalchemy.orm import Session
from app.config import settings
from app.prompts.interpretar_pedido import SYSTEM_PROMPT_INTERPRETAR
from app.models.mensaje_historico import MensajeHistorico

logger = logging.getLogger(__name__)

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


async def interpretar_mensaje(db: Session, telefono: str, mensaje: str) -> dict:
    """
    Recibe un mensaje de WhatsApp y lo interpreta usando Claude.
    Persiste el historial en la BD para sobrevivir reinicios
    y permitir conversaciones multi-turno de larga duracion.
    """

    # Cargar historial reciente de la BD (max 20 mensajes)
    historico = db.query(MensajeHistorico).filter(
        MensajeHistorico.telefono == telefono,
    ).order_by(MensajeHistorico.created_at.asc()).limit(20).all()

    mensajes = [{"role": m.role, "content": m.content} for m in historico]

    # Agregar mensaje actual del usuario
    mensajes.append({"role": "user", "content": mensaje})

    # Guardar mensaje del usuario en BD
    db.add(MensajeHistorico(telefono=telefono, role="user", content=mensaje))
    db.flush()

    # Llamar a Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT_INTERPRETAR,
        messages=mensajes
    )

    # Extraer respuesta
    respuesta_texto = response.content[0].text

    # Guardar respuesta del asistente en BD
    db.add(MensajeHistorico(telefono=telefono, role="assistant", content=respuesta_texto))
    db.commit()

    # Intentar parsear el JSON de la respuesta
    try:
        inicio = respuesta_texto.find('{')
        fin = respuesta_texto.rfind('}') + 1
        if inicio != -1 and fin > inicio:
            pedido_data = json.loads(respuesta_texto[inicio:fin])
            return pedido_data
    except json.JSONDecodeError:
        logger.warning(f"No se pudo parsear JSON de la respuesta: {respuesta_texto[:200]}")

    # Si no hay JSON, devolver el mensaje como respuesta conversacional
    return {
        "status": "conversacion",
        "mensaje_usuario": respuesta_texto
    }


async def interpretar_imagen(image_bytes: bytes) -> str:
    """
    Analiza una imagen usando Claude Vision para extraer lista de materiales.
    Soporta fotos de listas escritas a mano, planos, notas, capturas de pantalla.
    Retorna texto descriptivo del pedido que se procesa como mensaje normal.
    """
    import base64
    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analiza esta imagen de una obra de construccion o lista de materiales. "
                            "Extrae TODOS los materiales, cantidades, unidades y especificaciones que veas. "
                            "Responde en espanol como si fueras un residente de obra pidiendo estos materiales. "
                            "Ejemplo: 'Necesito 15m3 de concreto fc250, 200 varillas del 3/8 y 50 bultos de cemento gris'. "
                            "Si no puedes identificar materiales, describe lo que ves."
                        )
                    }
                ]
            }]
        )
        texto = response.content[0].text
        logger.info(f"Imagen interpretada: {texto[:200]}")
        return texto
    except Exception as e:
        logger.error(f"Error interpretando imagen: {e}")
        return ""


async def limpiar_conversacion(db: Session, telefono: str):
    """Limpia el historial cuando se completa un ciclo de pedido."""
    db.query(MensajeHistorico).filter(
        MensajeHistorico.telefono == telefono,
    ).delete()
    db.commit()


def obtener_historial(db: Session, telefono: str) -> list[dict]:
    """Devuelve el historial de conversacion de un telefono."""
    historico = db.query(MensajeHistorico).filter(
        MensajeHistorico.telefono == telefono,
    ).order_by(MensajeHistorico.created_at.asc()).all()
    return [{"role": m.role, "content": m.content} for m in historico]
