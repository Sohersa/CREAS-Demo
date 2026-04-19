"""
Generador de comparativas formateadas para WhatsApp.
Toma cotizaciones y genera un mensaje legible y visual.
"""
import json
import logging

import anthropic
from anthropic import Anthropic

from app.config import settings
from app.prompts.generar_comparativa import SYSTEM_PROMPT_COMPARATIVA

logger = logging.getLogger(__name__)

client = Anthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    max_retries=settings.CLAUDE_MAX_RETRIES,
)

MEDALLAS = ["1.", "2.", "3."]


def generar_comparativa_simple(cotizaciones: list[dict], pedido_resumen: str) -> str:
    """
    Genera la comparativa SIN usar Claude (mas rapido y sin costo).
    Para pedidos simples esta funcion es suficiente.
    """
    if not cotizaciones:
        return "X No encontre proveedores disponibles para tu pedido. Intenta con otros materiales."

    lineas = []
    lineas.append(f"*COMPARATIVA DE COTIZACION*")
    lineas.append(f"Pedido: {pedido_resumen}")
    lineas.append("")

    for i, cot in enumerate(cotizaciones[:5]):  # Maximo 5 proveedores
        medalla = MEDALLAS[i] if i < 3 else f"#{i+1}"
        etiqueta = " *MEJOR PRECIO*" if i == 0 else ""

        lineas.append(f"{medalla}{etiqueta}")
        lineas.append(f"*{cot['proveedor_nombre']}*")

        # Listar items
        for item in cot["items"]:
            precio_fmt = f"${item['precio_unitario']:,.0f}"
            subtotal_fmt = f"${item['subtotal']:,.0f}"
            lineas.append(f"  {item['producto']}: {precio_fmt}/{item['unidad']} x {item['cantidad']} = {subtotal_fmt}")

        # Disponibilidad parcial
        if cot["items_disponibles"] < cot["total_items_pedido"]:
            faltantes = cot["total_items_pedido"] - cot["items_disponibles"]
            lineas.append(f"  *No tiene {faltantes} de {cot['total_items_pedido']} materiales")

        # Flete y total
        if cot["costo_flete"] > 0:
            lineas.append(f"Flete: ${cot['costo_flete']:,.0f}")
        else:
            lineas.append(f"Flete: Incluido")

        lineas.append(f"  *TOTAL: ${cot['total']:,.0f}*")

        # Calificacion
        cal = cot.get("proveedor_calificacion", 4.0)
        pedidos = cot.get("proveedor_total_pedidos", 0)
        lineas.append(f"  Cal:{cal}/5 ({pedidos} entregas) | Entrega: {cot['items'][0].get('disponibilidad', '24h')}")
        lineas.append("")

    # Recomendacion
    if len(cotizaciones) >= 2:
        mejor = cotizaciones[0]
        segundo = cotizaciones[1]
        ahorro = segundo["total"] - mejor["total"]
        if ahorro > 0:
            lineas.append(f">*Recomendacion:* {mejor['proveedor_nombre']} te ahorra ${ahorro:,.0f} vs {segundo['proveedor_nombre']}.")
        else:
            lineas.append(f">*Recomendacion:* Ambos proveedores tienen precios similares. {mejor['proveedor_nombre']} tiene el mejor total.")

    lineas.append("")
    lineas.append("Responde con el *NUMERO* del proveedor que te interesa o escribe *mas info*.")

    return "\n".join(lineas)


async def generar_comparativa_con_ia(cotizaciones: list[dict], pedido_resumen: str) -> str:
    """
    Genera la comparativa USANDO Claude Opus 4.7 con adaptive thinking.
    Razona sobre tradeoffs (precio vs calificacion vs tiempo de entrega) antes
    de escribir la recomendacion final.

    Prompt cacheado: despues de la primera llamada el costo es ~10% del normal.
    """
    if not cotizaciones:
        return "X No encontre proveedores disponibles para tu pedido."

    cotizaciones_json = json.dumps(cotizaciones, ensure_ascii=False, indent=2)

    system_block = [{"type": "text", "text": SYSTEM_PROMPT_COMPARATIVA}]
    if settings.CLAUDE_USE_PROMPT_CACHE:
        system_block[0]["cache_control"] = {"type": "ephemeral"}

    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL_AGENTE,  # Opus 4.7 — razonamiento de tradeoffs
            max_tokens=2500,
            thinking={"type": "adaptive"},  # Piensa antes de recomendar
            system=system_block,
            messages=[{
                "role": "user",
                "content": (
                    f"Genera la comparativa para WhatsApp.\n\n"
                    f"Pedido: {pedido_resumen}\n\n"
                    f"Cotizaciones:\n{cotizaciones_json}"
                ),
            }],
        )
        # Extraer solo el texto (Opus 4.7 puede incluir thinking blocks)
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""
    except anthropic.APIError as e:
        logger.error(f"Error comparativa con IA: {e} — cayendo a modo simple")
        # Fallback a la version sin IA
        return generar_comparativa_simple(cotizaciones, pedido_resumen)


def resumir_pedido(pedido_data: dict) -> str:
    """Genera un resumen corto del pedido para el encabezado de la comparativa."""
    items = pedido_data.get("pedido", {}).get("items", [])
    entrega = pedido_data.get("pedido", {}).get("entrega", {})

    partes = []
    for item in items:
        cantidad = item.get("cantidad", "")
        unidad = item.get("unidad", "")
        producto = item.get("producto", "")
        partes.append(f"{cantidad}{unidad} {producto}")

    resumen = " + ".join(partes)

    direccion = entrega.get("direccion", "")
    fecha = entrega.get("fecha", "")
    if direccion:
        resumen += f"\nEntrega: {direccion}"
    if fecha:
        resumen += f", {fecha}"

    return resumen
