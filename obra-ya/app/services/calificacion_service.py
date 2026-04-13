"""
Servicio de calificaciones — rating auto-calculado de proveedores.
No son estrellas manuales: se calculan de datos reales.

Ejes de evaluacion:
  - Puntualidad (35%): llego a tiempo?
  - Cantidad correcta (25%): llego completo?
  - Especificacion correcta (25%): llego lo que se pidio?
  - Sin incidencias (15%): hubo problemas?
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.orden import Orden
from app.models.calificacion import CalificacionProveedor
from app.models.incidencia import IncidenciaEntrega
from app.models.proveedor import Proveedor

logger = logging.getLogger(__name__)

# Pesos por eje
PESO_PUNTUALIDAD = 0.35
PESO_CANTIDAD = 0.25
PESO_ESPECIFICACION = 0.25
PESO_SIN_INCIDENCIAS = 0.15


def calcular_calificacion(db: Session, orden_id: int) -> CalificacionProveedor:
    """
    Calcula la calificacion de un proveedor para una orden entregada.
    Se llama automaticamente despues de confirmar_entrega().
    """
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise ValueError(f"Orden {orden_id} no existe")

    if orden.status not in ("entregada", "con_incidencia"):
        raise ValueError(f"Orden {orden_id} no esta entregada (status: {orden.status})")

    # Buscar incidencias de esta orden
    incidencias = db.query(IncidenciaEntrega).filter(
        IncidenciaEntrega.orden_id == orden_id,
    ).all()

    # === PUNTUALIDAD ===
    score_puntualidad = 5.0
    if orden.fecha_entrega_prometida and orden.fecha_entrega_real:
        diferencia = orden.fecha_entrega_real - orden.fecha_entrega_prometida
        minutos_tarde = diferencia.total_seconds() / 60
        if minutos_tarde > 0:
            # -1 punto por cada 30 min de retraso
            score_puntualidad = max(1.0, 5.0 - (minutos_tarde / 30))
    elif orden.tiempo_entrega_minutos and orden.tiempo_entrega_minutos > 120:
        # Si no hay fecha prometida pero tardo mas de 2 horas
        score_puntualidad = max(2.0, 5.0 - ((orden.tiempo_entrega_minutos - 60) / 60))

    # === CANTIDAD CORRECTA ===
    score_cantidad = 5.0
    incidencias_cantidad = [i for i in incidencias if i.tipo == "cantidad_incorrecta"]
    if incidencias_cantidad:
        inc = incidencias_cantidad[0]
        if inc.cantidad_esperada and inc.cantidad_recibida and inc.cantidad_esperada > 0:
            ratio = inc.cantidad_recibida / inc.cantidad_esperada
            score_cantidad = max(1.0, 5.0 * ratio)
        else:
            score_cantidad = 2.5  # Penalizacion por default si no hay datos

    # === ESPECIFICACION CORRECTA ===
    score_spec = 5.0
    incidencias_spec = [i for i in incidencias if i.tipo == "especificacion"]
    if incidencias_spec:
        score_spec = 2.0  # Penalizacion fuerte: mandaron algo diferente

    # === SIN INCIDENCIAS ===
    score_sin_incidencias = 5.0
    if incidencias:
        # -1.5 por cada incidencia
        score_sin_incidencias = max(1.0, 5.0 - (len(incidencias) * 1.5))

    # === SCORE COMPUESTO ===
    calificacion_total = (
        score_puntualidad * PESO_PUNTUALIDAD
        + score_cantidad * PESO_CANTIDAD
        + score_spec * PESO_ESPECIFICACION
        + score_sin_incidencias * PESO_SIN_INCIDENCIAS
    )

    # Guardar o actualizar
    calif = db.query(CalificacionProveedor).filter(
        CalificacionProveedor.orden_id == orden_id,
    ).first()

    if not calif:
        calif = CalificacionProveedor(
            orden_id=orden_id,
            proveedor_id=orden.proveedor_id,
            usuario_id=orden.usuario_id,
        )
        db.add(calif)

    calif.puntualidad = round(score_puntualidad, 2)
    calif.cantidad_correcta = round(score_cantidad, 2)
    calif.especificacion_correcta = round(score_spec, 2)
    calif.sin_incidencias = round(score_sin_incidencias, 2)
    calif.calificacion_total = round(calificacion_total, 2)
    calif.auto_calculada = True

    db.flush()
    db.commit()

    logger.info(
        f"Calificacion Orden #{orden_id}: punt={calif.puntualidad}, "
        f"cant={calif.cantidad_correcta}, spec={calif.especificacion_correcta}, "
        f"total={calif.calificacion_total}"
    )

    # Recalcular metricas del proveedor
    recalcular_metricas_proveedor(db, orden.proveedor_id)

    return calif


def recalcular_metricas_proveedor(db: Session, proveedor_id: int):
    """
    Recalcula las metricas agregadas de un proveedor basado en
    todas sus calificaciones (ultimas 50 ordenes).
    """
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return

    # Ultimas 50 calificaciones
    calificaciones = db.query(CalificacionProveedor).filter(
        CalificacionProveedor.proveedor_id == proveedor_id,
    ).order_by(CalificacionProveedor.created_at.desc()).limit(50).all()

    if not calificaciones:
        return

    n = len(calificaciones)

    # Promedio de calificacion total
    proveedor.calificacion = round(
        sum(c.calificacion_total for c in calificaciones) / n, 2
    )

    # Tasas (% de ordenes sin problemas en cada eje)
    proveedor.tasa_puntualidad = round(
        sum(1 for c in calificaciones if c.puntualidad >= 4.0) / n, 2
    )
    proveedor.tasa_cantidad_correcta = round(
        sum(1 for c in calificaciones if c.cantidad_correcta >= 4.5) / n, 2
    )
    proveedor.tasa_especificacion_correcta = round(
        sum(1 for c in calificaciones if c.especificacion_correcta >= 4.5) / n, 2
    )

    # Total incidencias
    total_inc = db.query(IncidenciaEntrega).filter(
        IncidenciaEntrega.proveedor_id == proveedor_id,
    ).count()
    proveedor.total_incidencias = total_inc

    # Total ordenes completadas
    total_completadas = db.query(Orden).filter(
        Orden.proveedor_id == proveedor_id,
        Orden.status == "entregada",
    ).count()
    proveedor.total_ordenes_completadas = total_completadas

    db.commit()
    logger.info(
        f"Metricas Proveedor #{proveedor_id} ({proveedor.nombre}): "
        f"calif={proveedor.calificacion}, punt={proveedor.tasa_puntualidad}, "
        f"completadas={proveedor.total_ordenes_completadas}"
    )
