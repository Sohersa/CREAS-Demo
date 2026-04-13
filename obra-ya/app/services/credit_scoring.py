"""
Servicio de credit scoring para usuarios de ObraYa.
Calcula un score de 0-100 basado en historial de compras y pagos.
Pensado para futuro lending/credito a constructoras.
"""
import logging
from datetime import datetime

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.models.orden import Orden

logger = logging.getLogger(__name__)

# ─── Constantes de ponderacion ────────────────────────────────────

PESO_HISTORIAL_PAGOS = 0.40
PESO_VOLUMEN_COMPRAS = 0.20
PESO_FRECUENCIA = 0.15
PESO_ANTIGUEDAD = 0.10
PESO_DIVERSIDAD_PROVEEDORES = 0.10
PESO_METODO_PAGO = 0.05

# Umbrales de normalizacion
VOLUMEN_MAX_REFERENCIA = 500_000.0   # $500k MXN = score maximo en volumen
PEDIDOS_MAX_REFERENCIA = 50          # 50 pedidos = score maximo en frecuencia
ANTIGUEDAD_MAX_DIAS = 365            # 1 anio = score maximo en antiguedad
PROVEEDORES_MAX_REFERENCIA = 10      # 10 proveedores distintos = score maximo

DIAS_PAGO_A_TIEMPO = 7  # Hasta 7 dias = pago a tiempo


# ─── 1. Calcular score principal ──────────────────────────────────

def calcular_score(db: Session, usuario_id: int) -> float:
    """
    Calcula el score crediticio (0-100) de un usuario.

    Componentes:
      - Historial de pagos (40%): ratio pagos a tiempo vs tarde
      - Volumen de compras (20%): total_gastado normalizado
      - Frecuencia (15%): pedidos completados
      - Antiguedad (10%): dias desde registro
      - Diversidad proveedores (10%): proveedores diferentes usados
      - Metodo de pago (5%): tarjeta > transferencia > efectivo
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return 0.0

    # --- Historial de pagos (40%) ---
    total_pagos = (usuario.pedidos_pagados_a_tiempo or 0) + (usuario.pedidos_pagados_tarde or 0)
    if total_pagos > 0:
        ratio_a_tiempo = (usuario.pedidos_pagados_a_tiempo or 0) / total_pagos
        score_pagos = ratio_a_tiempo * 100
    else:
        score_pagos = 50.0  # Sin historial = neutral

    # --- Volumen de compras (20%) ---
    total_gastado = usuario.total_gastado or 0
    score_volumen = min((total_gastado / VOLUMEN_MAX_REFERENCIA) * 100, 100)

    # --- Frecuencia de pedidos (15%) ---
    pedidos = usuario.total_pedidos_completados or 0
    score_frecuencia = min((pedidos / PEDIDOS_MAX_REFERENCIA) * 100, 100)

    # --- Antiguedad (10%) ---
    if usuario.created_at:
        dias_registro = (datetime.utcnow() - usuario.created_at).days
        score_antiguedad = min((dias_registro / ANTIGUEDAD_MAX_DIAS) * 100, 100)
    else:
        score_antiguedad = 0.0

    # --- Diversidad de proveedores (10%) ---
    proveedores_distintos = db.query(
        func.count(distinct(Orden.proveedor_id))
    ).filter(
        Orden.usuario_id == usuario_id,
        Orden.status == "entregada",
    ).scalar() or 0
    score_diversidad = min((proveedores_distintos / PROVEEDORES_MAX_REFERENCIA) * 100, 100)

    # --- Metodo de pago preferido (5%) ---
    metodo_favorito = db.query(
        Orden.metodo_pago,
        func.count(Orden.id).label("cnt"),
    ).filter(
        Orden.usuario_id == usuario_id,
        Orden.pagado == True,  # noqa: E712
    ).group_by(Orden.metodo_pago).order_by(func.count(Orden.id).desc()).first()

    if metodo_favorito and metodo_favorito[0]:
        metodo = metodo_favorito[0].lower()
        if metodo == "tarjeta":
            score_metodo = 100
        elif metodo == "transferencia":
            score_metodo = 70
        else:  # efectivo, simulado, etc.
            score_metodo = 40
    else:
        score_metodo = 50  # Sin datos

    # --- Score compuesto ---
    score = (
        score_pagos * PESO_HISTORIAL_PAGOS
        + score_volumen * PESO_VOLUMEN_COMPRAS
        + score_frecuencia * PESO_FRECUENCIA
        + score_antiguedad * PESO_ANTIGUEDAD
        + score_diversidad * PESO_DIVERSIDAD_PROVEEDORES
        + score_metodo * PESO_METODO_PAGO
    )

    # Clamp 0-100
    score = max(0.0, min(100.0, round(score, 2)))

    logger.info(f"Score calculado para usuario {usuario_id}: {score} "
                f"(pagos={score_pagos:.0f}, vol={score_volumen:.0f}, "
                f"freq={score_frecuencia:.0f}, ant={score_antiguedad:.0f}, "
                f"div={score_diversidad:.0f}, met={score_metodo:.0f})")

    return score


# ─── 2. Actualizar score tras pago ────────────────────────────────

def actualizar_score_tras_pago(db: Session, usuario_id: int, orden_id: int) -> float:
    """
    Llamar despues de confirmar un pago.
    Actualiza metricas del usuario y recalcula el score.

    Returns:
        El nuevo score_credito del usuario.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        logger.warning(f"Usuario {usuario_id} no encontrado para actualizar score")
        return 0.0

    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        logger.warning(f"Orden {orden_id} no encontrada para actualizar score")
        return usuario.score_credito or 50.0

    # Actualizar total gastado
    usuario.total_gastado = (usuario.total_gastado or 0) + (orden.total or 0)

    # Incrementar pedidos completados
    usuario.total_pedidos_completados = (usuario.total_pedidos_completados or 0) + 1

    # Calcular dias para pagar
    fecha_creacion = orden.created_at or orden.confirmada_at
    fecha_pago = orden.fecha_pago or datetime.utcnow()
    if fecha_creacion:
        days_to_pay = (fecha_pago - fecha_creacion).days
    else:
        days_to_pay = 0

    # Actualizar promedio de dias de pago (running average)
    n = usuario.total_pedidos_completados  # Ya fue incrementado arriba
    promedio_anterior = usuario.promedio_dias_pago or 0
    if n <= 1:
        usuario.promedio_dias_pago = float(days_to_pay)
    else:
        usuario.promedio_dias_pago = round(
            promedio_anterior + (days_to_pay - promedio_anterior) / n, 2
        )

    # Clasificar pago: a tiempo o tarde
    if days_to_pay <= DIAS_PAGO_A_TIEMPO:
        usuario.pedidos_pagados_a_tiempo = (usuario.pedidos_pagados_a_tiempo or 0) + 1
    else:
        usuario.pedidos_pagados_tarde = (usuario.pedidos_pagados_tarde or 0) + 1

    # Recalcular score
    nuevo_score = calcular_score(db, usuario_id)
    usuario.score_credito = nuevo_score

    db.commit()

    logger.info(f"Score actualizado para usuario {usuario_id} tras orden {orden_id}: "
                f"{nuevo_score} (dias_pago={days_to_pay}, "
                f"promedio={usuario.promedio_dias_pago})")

    return nuevo_score


# ─── 3. Obtener perfil crediticio ─────────────────────────────────

def obtener_perfil_crediticio(db: Session, usuario_id: int) -> dict:
    """
    Retorna el perfil crediticio completo de un usuario.

    Returns:
        dict con score, nivel, metricas, limite_credito_sugerido, riesgo.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return {"error": "Usuario no encontrado"}

    score = usuario.score_credito or 50.0
    total_pedidos = usuario.total_pedidos_completados or 0
    total_gastado = usuario.total_gastado or 0

    # Determinar nivel
    if total_pedidos == 0:
        nivel = "sin_historial"
    elif score >= 85:
        nivel = "excelente"
    elif score >= 70:
        nivel = "bueno"
    elif score >= 50:
        nivel = "regular"
    else:
        nivel = "malo"

    # Determinar riesgo
    if score >= 75:
        riesgo = "bajo"
    elif score >= 50:
        riesgo = "medio"
    else:
        riesgo = "alto"

    # Calcular limite de credito sugerido
    if total_pedidos < 5 or score < 65:
        limite_credito_sugerido = 0.0
    else:
        limite_credito_sugerido = round(score * total_gastado * 0.1 / 100, 2)

    # Proveedores usados
    proveedores_usados = db.query(
        func.count(distinct(Orden.proveedor_id))
    ).filter(
        Orden.usuario_id == usuario_id,
        Orden.status == "entregada",
    ).scalar() or 0

    return {
        "usuario_id": usuario_id,
        "nombre": usuario.nombre,
        "empresa": usuario.empresa,
        "score": score,
        "nivel": nivel,
        "riesgo": riesgo,
        "total_gastado": total_gastado,
        "total_pedidos_completados": total_pedidos,
        "promedio_dias_pago": usuario.promedio_dias_pago,
        "pedidos_pagados_a_tiempo": usuario.pedidos_pagados_a_tiempo or 0,
        "pedidos_pagados_tarde": usuario.pedidos_pagados_tarde or 0,
        "proveedores_usados": proveedores_usados,
        "limite_credito_sugerido": limite_credito_sugerido,
        "miembro_desde": usuario.created_at.isoformat() if usuario.created_at else None,
    }


# ─── 4. Evaluar elegibilidad de credito ──────────────────────────

def evaluar_elegibilidad_credito(db: Session, usuario_id: int, monto: float) -> dict:
    """
    Evalua si un usuario es elegible para credito por un monto dado.

    Requisitos minimos:
      - Score >= 65
      - Al menos 5 pedidos completados
      - Monto solicitado <= limite calculado

    Returns:
        dict {elegible, motivo, score, limite_disponible}
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return {
            "elegible": False,
            "motivo": "Usuario no encontrado",
            "score": 0,
            "limite_disponible": 0,
        }

    score = usuario.score_credito or 50.0
    total_pedidos = usuario.total_pedidos_completados or 0
    total_gastado = usuario.total_gastado or 0

    # Calcular limite: score * total_gastado * 0.1 / 100
    # Es decir, 10% del gasto historico ponderado por score (normalizado 0-1)
    if total_pedidos >= 5 and score >= 65:
        limite_disponible = round(score * total_gastado * 0.1 / 100, 2)
    else:
        limite_disponible = 0.0

    # Evaluar requisitos
    if total_pedidos < 5:
        return {
            "elegible": False,
            "motivo": f"Se requieren al menos 5 pedidos completados. Tienes {total_pedidos}.",
            "score": score,
            "limite_disponible": limite_disponible,
        }

    if score < 65:
        return {
            "elegible": False,
            "motivo": f"Score minimo requerido: 65. Tu score actual es {score}.",
            "score": score,
            "limite_disponible": limite_disponible,
        }

    if monto > limite_disponible:
        return {
            "elegible": False,
            "motivo": (
                f"Monto solicitado (${monto:,.2f}) excede tu limite "
                f"disponible (${limite_disponible:,.2f})."
            ),
            "score": score,
            "limite_disponible": limite_disponible,
        }

    return {
        "elegible": True,
        "motivo": "Cumples todos los requisitos para credito.",
        "score": score,
        "limite_disponible": limite_disponible,
        "monto_solicitado": monto,
    }


# ─── 5. Ranking de usuarios por score ─────────────────────────────

def ranking_usuarios_por_score(db: Session, limit: int = 20) -> list:
    """
    Retorna los top N usuarios ordenados por score crediticio.
    """
    usuarios = (
        db.query(Usuario)
        .filter(Usuario.total_pedidos_completados > 0)
        .order_by(Usuario.score_credito.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "usuario_id": u.id,
            "nombre": u.nombre,
            "empresa": u.empresa,
            "score": u.score_credito or 0,
            "total_gastado": u.total_gastado or 0,
            "total_pedidos": u.total_pedidos_completados or 0,
            "promedio_dias_pago": u.promedio_dias_pago,
        }
        for u in usuarios
    ]
