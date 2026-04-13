"""
Generador de comparativas formateadas para WhatsApp.
Toma cotizaciones y genera un mensaje legible y visual.
"""
import json
import logging
from anthropic import Anthropic
from app.config import settings
from app.prompts.generar_comparativa import SYSTEM_PROMPT_COMPARATIVA

logger = logging.getLogger(__name__)

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

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
    Genera la comparativa USANDO Claude para un formato mas natural.
    Usa mas tokens pero da mejor resultado para pedidos complejos.
    """
    if not cotizaciones:
        return "X No encontre proveedores disponibles para tu pedido."

    cotizaciones_json = json.dumps(cotizaciones, ensure_ascii=False, indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT_COMPARATIVA,
        messages=[{
            "role": "user",
            "content": f"Genera la comparativa para WhatsApp.\n\nPedido: {pedido_resumen}\n\nCotizaciones:\n{cotizaciones_json}"
        }]
    )

    return response.content[0].text


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
