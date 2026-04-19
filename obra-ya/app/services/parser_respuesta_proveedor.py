"""
Parser de respuestas de proveedores — interpreta mensajes de WhatsApp con precios.

Cuando un proveedor responde "te lo dejo a 195 el bulto, manana te lo llevo,
flete son 800 pesos", este servicio usa Claude para extraer:
  - precio_total
  - desglose por producto
  - tiempo de entrega
  - costo de flete
  - disponibilidad
"""
import json
import logging

import anthropic
from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

client = Anthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    max_retries=settings.CLAUDE_MAX_RETRIES,
)

SYSTEM_PROMPT_PARSER = """Eres un asistente que extrae informacion de precios de mensajes de proveedores de materiales de construccion en Mexico.

El proveedor esta respondiendo a una solicitud de cotizacion. Tu trabajo es extraer los datos estructurados de su respuesta.

DEBES responder UNICAMENTE con un JSON valido, sin texto adicional, con esta estructura:

{
  "tiene_precio": true/false,
  "sin_stock": true/false,
  "precio_total": 12345.00,
  "desglose": [
    {"producto": "Cemento gris CPC 30R", "precio_unitario": 195, "cantidad": 50, "unidad": "bultos", "subtotal": 9750}
  ],
  "incluye_flete": true/false,
  "costo_flete": 800,
  "tiempo_entrega": "manana a las 7am",
  "disponibilidad": "inmediata",
  "condiciones": "pago contra entrega",
  "notas": "cualquier otra info relevante"
}

Reglas:
- Si el proveedor da precio por unidad, calcula el subtotal por la cantidad solicitada
- Si dice "flete incluido", pon incluye_flete: true y costo_flete: 0
- Si dice que no tiene stock o no maneja el producto, pon sin_stock: true
- Si la respuesta es ambigua o no tiene precio, pon tiene_precio: false
- precio_total es la suma de todos los subtotales + costo_flete
- Interpreta jerga mexicana: "baro" = dinero, "te lo dejo en" = precio, "va con todo" = flete incluido
"""


async def parsear_respuesta_proveedor(
    texto_proveedor: str,
    contexto_pedido: str = "",
) -> dict:
    """
    Usa Claude para parsear la respuesta de un proveedor.

    Args:
        texto_proveedor: Mensaje de WhatsApp del proveedor
        contexto_pedido: Resumen de lo que se le pidio (para contexto)

    Returns:
        Dict con precio_total, desglose, tiempo_entrega, etc.
    """
    mensaje_usuario = f"""El proveedor respondio este mensaje:

"{texto_proveedor}"

"""
    if contexto_pedido:
        mensaje_usuario += f"""Contexto — esto es lo que se le habia pedido:
{contexto_pedido}
"""

    mensaje_usuario += "\nExtrae los datos de precio y entrega. Responde SOLO con JSON."

    # System prompt con cache — el prompt es estable y se envia en cada parseo
    system_block = [{"type": "text", "text": SYSTEM_PROMPT_PARSER}]
    if settings.CLAUDE_USE_PROMPT_CACHE:
        system_block[0]["cache_control"] = {"type": "ephemeral"}

    texto_respuesta = ""
    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL_PARSER,  # Haiku 4.5 — rapido y barato para extraccion
            max_tokens=1000,
            system=system_block,
            messages=[{"role": "user", "content": mensaje_usuario}],
        )

        texto_respuesta = response.content[0].text.strip()

        # Limpiar markdown si viene envuelto en ```json
        if texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta.split("\n", 1)[-1]
            texto_respuesta = texto_respuesta.rsplit("```", 1)[0]
            texto_respuesta = texto_respuesta.strip()

        resultado = json.loads(texto_respuesta)
        logger.info(f"Respuesta parseada: precio_total={resultado.get('precio_total')}")
        return resultado

    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e} | Texto: {texto_respuesta[:200]}")
        return {"tiene_precio": False, "error": "No se pudo parsear la respuesta"}

    except anthropic.RateLimitError:
        logger.error("Rate limit en parser de proveedor")
        return {"tiene_precio": False, "error": "rate_limit"}
    except anthropic.APIError as e:
        logger.error(f"Error API Claude en parser: {e}")
        return {"tiene_precio": False, "error": str(e)}


def es_mensaje_de_proveedor(db, telefono: str) -> bool:
    """
    Verifica si un numero de telefono pertenece a un proveedor registrado
    o a un vendedor de un proveedor.
    Esto es clave para distinguir mensajes de usuarios vs proveedores en el webhook.
    Busca con el telefono tal cual Y con la version normalizada.
    """
    from app.models.proveedor import Proveedor
    from app.models.vendedor import Vendedor
    from app.utils.telefono import normalizar_telefono_mx

    tel_normalizado = normalizar_telefono_mx(telefono)

    # Check provider main number
    proveedor = db.query(Proveedor).filter(
        Proveedor.activo == True,
        (Proveedor.telefono_whatsapp == telefono) | (Proveedor.telefono_whatsapp == tel_normalizado),
    ).first()
    if proveedor:
        return True

    # Check individual salespeople (vendedores)
    vendedor = db.query(Vendedor).filter(
        Vendedor.activo == True,
        (Vendedor.telefono_whatsapp == telefono) | (Vendedor.telefono_whatsapp == tel_normalizado),
    ).first()
    return vendedor is not None


def obtener_proveedor_por_telefono(db, telefono: str):
    """
    Busca proveedor por numero de WhatsApp (con normalizacion).
    Also checks vendedores — if the phone belongs to a salesperson,
    returns the parent proveedor.
    """
    from app.models.proveedor import Proveedor
    from app.models.vendedor import Vendedor
    from app.utils.telefono import normalizar_telefono_mx

    tel_normalizado = normalizar_telefono_mx(telefono)

    # Direct provider match
    proveedor = db.query(Proveedor).filter(
        Proveedor.activo == True,
        (Proveedor.telefono_whatsapp == telefono) | (Proveedor.telefono_whatsapp == tel_normalizado),
    ).first()
    if proveedor:
        return proveedor

    # Check vendedores — return their parent proveedor
    vendedor = db.query(Vendedor).filter(
        Vendedor.activo == True,
        (Vendedor.telefono_whatsapp == telefono) | (Vendedor.telefono_whatsapp == tel_normalizado),
    ).first()
    if vendedor:
        return db.query(Proveedor).filter(Proveedor.id == vendedor.proveedor_id).first()

    return None
