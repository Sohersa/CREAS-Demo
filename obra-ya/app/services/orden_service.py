"""
Servicio de ordenes — maquina de estados del ciclo de vida post-cotizacion.

Flujo:
  confirmada → preparando → en_transito → en_obra → entregada
                                                   → con_incidencia → entregada
  Cualquier estado → cancelada
"""
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.orden import Orden
from app.models.seguimiento import SeguimientoEntrega
from app.models.cotizacion import Cotizacion
from app.models.pedido import Pedido
from app.models.proveedor import Proveedor

logger = logging.getLogger(__name__)

# Transiciones validas
TRANSICIONES = {
    "pendiente_aprobacion": ["confirmada", "cancelada"],
    "confirmada": ["preparando", "cancelada"],
    "preparando": ["en_transito", "cancelada"],
    "en_transito": ["en_obra", "cancelada"],
    "en_obra": ["entregada", "con_incidencia", "cancelada"],
    "con_incidencia": ["entregada", "cancelada"],
}


def crear_orden(db: Session, cotizacion_id: int, usuario_id: int, status_inicial: str = "confirmada") -> Orden:
    """
    Crea una orden a partir de una cotizacion elegida.
    status_inicial: "confirmada" (normal) o "pendiente_aprobacion" (corporativa).
    """
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not cotizacion:
        raise ValueError(f"Cotizacion {cotizacion_id} no existe")

    pedido = db.query(Pedido).filter(Pedido.id == cotizacion.pedido_id).first()
    if not pedido:
        raise ValueError(f"Pedido {cotizacion.pedido_id} no existe")

    ahora = datetime.now(timezone.utc)

    # Extraer tiempo de entrega de la cotizacion para calcular fecha_entrega_prometida
    fecha_entrega = None
    try:
        if cotizacion.tiempo_entrega:
            from datetime import timedelta
            # Parsear tiempo_entrega (ej: "24 horas", "2 dias", "48h")
            te = cotizacion.tiempo_entrega.lower().strip()
            horas = 0
            import re as _re
            num_match = _re.search(r'(\d+)', te)
            if num_match:
                num = int(num_match.group(1))
                if 'dia' in te or 'day' in te:
                    horas = num * 24
                else:
                    horas = num
            if horas > 0:
                fecha_entrega = ahora + timedelta(hours=horas)
    except Exception:
        pass

    orden = Orden(
        pedido_id=pedido.id,
        cotizacion_id=cotizacion.id,
        proveedor_id=cotizacion.proveedor_id,
        usuario_id=usuario_id,
        status=status_inicial,
        items=cotizacion.items,
        total=cotizacion.total,
        direccion_entrega=pedido.direccion_entrega or "",
        municipio_entrega=pedido.municipio_entrega or "",
        latitud_entrega=pedido.latitud_entrega,
        longitud_entrega=pedido.longitud_entrega,
        colonia_entrega=pedido.colonia_entrega,
        codigo_postal_entrega=pedido.codigo_postal_entrega,
        confirmada_at=ahora if status_inicial == "confirmada" else None,
        fecha_entrega_prometida=fecha_entrega,
    )
    db.add(orden)
    db.flush()

    # Actualizar pedido
    pedido.status = "orden_creada"
    db.flush()

    # Registrar en seguimiento
    seguimiento = SeguimientoEntrega(
        orden_id=orden.id,
        status_anterior=None,
        status_nuevo="confirmada",
        origen="usuario",
        nota=f"Usuario eligio cotizacion #{cotizacion.id} de proveedor #{cotizacion.proveedor_id}",
    )
    db.add(seguimiento)

    # Incrementar contador del proveedor
    proveedor = db.query(Proveedor).filter(Proveedor.id == cotizacion.proveedor_id).first()
    if proveedor:
        proveedor.total_pedidos = (proveedor.total_pedidos or 0) + 1
        db.flush()

    db.commit()
    logger.info(f"Orden #{orden.id} creada — Pedido #{pedido.id}, Proveedor #{cotizacion.proveedor_id}")

    # === AUTO-CONSUMO PRESUPUESTAL ===
    try:
        from app.models.presupuesto import PresupuestoObra

        # Find active budget for this user
        presupuesto = db.query(PresupuestoObra).filter(
            PresupuestoObra.usuario_id == orden.usuario_id,
            PresupuestoObra.activo == True,
        ).first()

        if presupuesto and orden.total:
            presupuesto.gastado_total = (presupuesto.gastado_total or 0) + orden.total
            if presupuesto.presupuesto_total and presupuesto.presupuesto_total > 0:
                presupuesto.porcentaje_consumido = round(
                    (presupuesto.gastado_total / presupuesto.presupuesto_total) * 100, 2
                )
            db.commit()
            logger.info(f"Consumo presupuestal registrado para orden #{orden.id}: ${orden.total:,.0f}")
    except Exception as e:
        logger.error(f"Error registrando consumo presupuestal: {e}")

    return orden


def avanzar_status(
    db: Session,
    orden_id: int,
    nuevo_status: str,
    origen: str = "admin",
    nota: str = "",
    datos_transporte: dict = None,
) -> Orden:
    """
    Avanza el status de una orden. Valida transiciones permitidas.
    datos_transporte: {nombre_chofer, telefono_chofer, placas_vehiculo, tipo_vehiculo}
    """
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise ValueError(f"Orden {orden_id} no existe")

    status_actual = orden.status

    # Validar transicion
    if nuevo_status == "cancelada":
        pass  # Siempre se puede cancelar
    elif nuevo_status not in TRANSICIONES.get(status_actual, []):
        raise ValueError(
            f"No se puede pasar de '{status_actual}' a '{nuevo_status}'. "
            f"Opciones: {TRANSICIONES.get(status_actual, [])}"
        )

    ahora = datetime.now(timezone.utc)
    orden.status = nuevo_status
    orden.updated_at = ahora

    # Registrar timestamp de la etapa
    timestamp_map = {
        "preparando": "preparando_at",
        "en_transito": "en_transito_at",
        "en_obra": "en_obra_at",
        "entregada": "entregada_at",
        "cancelada": "cancelada_at",
    }
    if nuevo_status in timestamp_map:
        setattr(orden, timestamp_map[nuevo_status], ahora)

    # Si entregada, calcular tiempo y fecha real
    if nuevo_status == "entregada":
        orden.fecha_entrega_real = ahora
        if orden.en_transito_at:
            delta = ahora - orden.en_transito_at
            orden.tiempo_entrega_minutos = int(delta.total_seconds() / 60)

    # Si en_transito, guardar datos del transporte
    if nuevo_status == "en_transito" and datos_transporte:
        orden.nombre_chofer = datos_transporte.get("nombre_chofer")
        orden.telefono_chofer = datos_transporte.get("telefono_chofer")
        orden.placas_vehiculo = datos_transporte.get("placas_vehiculo")
        orden.tipo_vehiculo = datos_transporte.get("tipo_vehiculo")

    # Registrar en seguimiento
    seguimiento = SeguimientoEntrega(
        orden_id=orden.id,
        status_anterior=status_actual,
        status_nuevo=nuevo_status,
        origen=origen,
        nota=nota,
    )
    db.add(seguimiento)

    # Si entregada, actualizar proveedor
    if nuevo_status == "entregada":
        proveedor = db.query(Proveedor).filter(Proveedor.id == orden.proveedor_id).first()
        if proveedor:
            proveedor.pedidos_cumplidos = (proveedor.pedidos_cumplidos or 0) + 1
            proveedor.total_ordenes_completadas = (proveedor.total_ordenes_completadas or 0) + 1

    db.commit()
    logger.info(f"Orden #{orden.id}: {status_actual} → {nuevo_status} (por {origen})")
    return orden


def confirmar_entrega(db: Session, orden_id: int) -> Orden:
    """Shortcut: usuario confirma que recibio el material."""
    return avanzar_status(db, orden_id, "entregada", origen="usuario", nota="Usuario confirmo recepcion")


def cancelar_orden(db: Session, orden_id: int, motivo: str = "") -> Orden:
    """Cancela una orden desde cualquier estado."""
    return avanzar_status(db, orden_id, "cancelada", origen="usuario", nota=motivo)


def obtener_ordenes_activas(db: Session, usuario_id: int) -> list[Orden]:
    """Ordenes que no estan entregadas ni canceladas."""
    return db.query(Orden).filter(
        Orden.usuario_id == usuario_id,
        Orden.status.notin_(["entregada", "cancelada"]),
    ).order_by(Orden.created_at.desc()).all()


def obtener_orden_activa_por_usuario(db: Session, usuario_id: int) -> Orden | None:
    """La orden activa mas reciente del usuario (para el flujo de WhatsApp)."""
    return db.query(Orden).filter(
        Orden.usuario_id == usuario_id,
        Orden.status.notin_(["entregada", "cancelada"]),
    ).order_by(Orden.created_at.desc()).first()


def obtener_timeline(db: Session, orden_id: int) -> list[dict]:
    """Devuelve el timeline completo de una orden."""
    eventos = db.query(SeguimientoEntrega).filter(
        SeguimientoEntrega.orden_id == orden_id
    ).order_by(SeguimientoEntrega.created_at).all()

    return [{
        "id": e.id,
        "status_anterior": e.status_anterior,
        "status_nuevo": e.status_nuevo,
        "origen": e.origen,
        "nota": e.nota,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    } for e in eventos]
