"""
Genera comparativas desde respuestas REALES de proveedores (no de BD estatica).
Toma las SolicitudProveedor con status=respondida y arma la tabla para WhatsApp.
"""
import json
import logging
from sqlalchemy.orm import Session

from app.models.solicitud_proveedor import SolicitudProveedor
from app.models.proveedor import Proveedor
from app.models.pedido import Pedido
from app.models.cotizacion import Cotizacion, Comparativa

logger = logging.getLogger(__name__)


def generar_comparativa_desde_respuestas(db: Session, pedido_id: int) -> dict | None:
    """
    Genera la comparativa formateada para WhatsApp usando
    las respuestas reales de proveedores.
    Tambien guarda las cotizaciones en la tabla de Cotizaciones para
    mantener compatibilidad con el flujo de ordenes.

    Retorna dict con:
      - texto: mensaje corto para WhatsApp
      - opciones: lista de dicts para botones/lista interactiva
      - num_opciones: cantidad de proveedores
    O None si no hay respuestas.
    """
    # Obtener respuestas ordenadas por precio
    solicitudes = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.pedido_id == pedido_id,
        SolicitudProveedor.status == "respondida",
        SolicitudProveedor.precio_total != None,
        SolicitudProveedor.precio_total > 0,
    ).order_by(SolicitudProveedor.precio_total.asc()).all()

    if not solicitudes:
        return None

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()

    # === GUARDAR COMO COTIZACIONES (compatibilidad con flujo de ordenes) ===
    cotizacion_ids = []
    for sol in solicitudes:
        cotizacion = Cotizacion(
            pedido_id=pedido_id,
            proveedor_id=sol.proveedor_id,
            status="respondida",
            items=sol.precio_desglose or "[]",
            subtotal=sol.precio_total - (sol.costo_flete or 0),
            costo_flete=sol.costo_flete or 0,
            total=sol.precio_total,
            tiempo_entrega=sol.tiempo_entrega or "",
            notas_proveedor=sol.notas or "",
            respondida_at=sol.respondida_at,
        )
        db.add(cotizacion)
        db.flush()
        cotizacion_ids.append(cotizacion.id)

    # === GENERAR MENSAJE WHATSAPP (formato corto) ===
    lineas = [f"*Tu pedido #{pedido_id} — {len(solicitudes)} opciones:*", ""]

    opciones_interactivas = []
    for i, sol in enumerate(solicitudes[:5]):
        prov = db.query(Proveedor).filter(Proveedor.id == sol.proveedor_id).first()
        nombre = prov.nombre if prov else f"Proveedor #{sol.proveedor_id}"
        calif = f"⭐{prov.calificacion}" if prov and prov.calificacion else ""

        # Info de flete compacta
        if sol.incluye_flete:
            flete_txt = "Flete inc."
        elif sol.costo_flete:
            flete_txt = f"Flete ${sol.costo_flete:,.0f}"
        else:
            flete_txt = "Sin flete"

        tiempo_txt = sol.tiempo_entrega or "—"

        # Etiqueta de mejor precio
        etiqueta = "✓ MÁS BARATO\n   " if i == 0 and len(solicitudes) > 1 else ""

        lineas.append(f"{i+1}. {etiqueta}{nombre} — *${sol.precio_total:,.0f}*")
        lineas.append(f"   {flete_txt} · {tiempo_txt} · {calif}")
        lineas.append("")

        # Datos para botones/lista interactiva
        opciones_interactivas.append({
            "id": f"prov_{sol.proveedor_id}_{pedido_id}",
            "title": f"{nombre[:17]}",  # Max 20 chars para boton
            "description": f"${sol.precio_total:,.0f} · {flete_txt} · {tiempo_txt}",
            "proveedor_id": sol.proveedor_id,
        })

    # Ahorro (solo si hay al menos 2)
    if len(solicitudes) >= 2:
        ahorro = solicitudes[-1].precio_total - solicitudes[0].precio_total
        if ahorro > 0:
            lineas.append(f"_Ahorro: ${ahorro:,.0f} MXN_")
            lineas.append("")

    comparativa_texto = "\n".join(lineas)

    # Guardar comparativa
    comp = Comparativa(
        pedido_id=pedido_id,
        cotizaciones_ids=json.dumps(cotizacion_ids),
        tabla_comparativa=comparativa_texto,
        recomendacion=f"Mejor precio: {solicitudes[0].proveedor_id}" if solicitudes else "",
        enviada_at=None,
    )
    db.add(comp)
    db.commit()

    logger.info(f"Comparativa generada — Pedido #{pedido_id}: {len(solicitudes)} cotizaciones reales")
    return {
        "texto": comparativa_texto,
        "opciones": opciones_interactivas,
        "num_opciones": len(solicitudes),
    }


def generar_mensaje_esperando(pedido_id: int, total_enviadas: int) -> str:
    """Mensaje para el usuario mientras esperamos respuestas."""
    return (
        f"*Nico esta cotizando tu pedido #{pedido_id}*\n\n"
        f">Contacte a {total_enviadas} proveedores\n"
        f">Esperando sus respuestas...\n\n"
        f"Te mando la comparativa en cuanto tenga las cotizaciones."
    )


def generar_mensaje_parcial(pedido_id: int, respondidas: int, pendientes: int) -> str:
    """Mensaje de update parcial."""
    return (
        f"Pedido #{pedido_id} — van {respondidas} respuestas de proveedores.\n"
        f"Faltan {pendientes} por contestar. Te aviso en cuanto tenga suficientes para comparar."
    )
