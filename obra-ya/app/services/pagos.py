"""
Servicio de pagos — Stripe Checkout + comision ObraYa 2%.

Modelo de negocio:
  Cliente paga a ObraYa con tarjeta (Stripe).
  ObraYa retiene 2% de comision.
  ObraYa paga al proveedor el 98% restante.
"""
import logging
from datetime import datetime

import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.models.orden import Orden

logger = logging.getLogger(__name__)

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

COMISION_PORCENTAJE = 0.02  # 2%


# ─── Utilidades ────────────────────────────────────────────────────

def calcular_desglose(total: float) -> dict:
    """
    Calcula el desglose de pago.
    Returns: {subtotal, comision_2pct, total_con_comision}
    """
    comision = round(total * COMISION_PORCENTAJE, 2)
    total_con_comision = round(total + comision, 2)
    return {
        "subtotal": round(total, 2),
        "comision_2pct": comision,
        "total_con_comision": total_con_comision,
    }


# ─── Stripe Checkout ──────────────────────────────────────────────

def crear_sesion_pago(orden_id: int, total: float, base_url: str = "http://localhost:8000") -> dict:
    """
    Crea una sesion de Stripe Checkout para cobrar al cliente.
    El monto cobrado incluye la comision de 2%.
    Retorna {session_id, url} para redirigir al cliente.
    """
    desglose = calcular_desglose(total)
    monto_centavos = int(desglose["total_con_comision"] * 100)  # Stripe usa centavos

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "mxn",
                    "unit_amount": monto_centavos,
                    "product_data": {
                        "name": f"ObraYa - Orden #{orden_id}",
                        "description": f"Materiales de construccion (incluye 2% comision de servicio)",
                    },
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{base_url}/pagos/exito?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/pagos/cancelado",
        metadata={
            "orden_id": str(orden_id),
            "subtotal": str(desglose["subtotal"]),
            "comision": str(desglose["comision_2pct"]),
        },
    )

    logger.info(f"Sesion Stripe creada para orden {orden_id}: {session.id}")
    return {"session_id": session.id, "url": session.url}


# ─── Confirmar pago ───────────────────────────────────────────────

def confirmar_pago(db: Session, stripe_session_id: str) -> Orden | None:
    """
    Confirma el pago en la BD tras recibir confirmacion de Stripe.
    Actualiza la orden con los datos del pago.
    """
    # Recuperar sesion de Stripe
    session = stripe.checkout.Session.retrieve(stripe_session_id)
    orden_id = int(session.metadata["orden_id"])

    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        logger.error(f"Orden {orden_id} no encontrada al confirmar pago")
        return None

    if orden.pagado:
        logger.warning(f"Orden {orden_id} ya estaba marcada como pagada")
        return orden

    desglose = calcular_desglose(orden.total)

    orden.pagado = True
    orden.metodo_pago = "tarjeta"
    orden.stripe_payment_id = session.payment_intent
    orden.fecha_pago = datetime.utcnow()
    orden.comision_obraya = desglose["comision_2pct"]
    orden.monto_proveedor = orden.total  # proveedor recibe el total original
    orden.pago_proveedor_status = "pendiente"

    db.commit()
    db.refresh(orden)
    logger.info(f"Pago confirmado para orden {orden_id} — Stripe PI: {session.payment_intent}")

    # Actualizar credit scoring del usuario
    _actualizar_credit_scoring(db, orden)

    return orden


def _actualizar_credit_scoring(db: Session, orden: Orden):
    """Actualiza el score crediticio del usuario tras un pago exitoso."""
    try:
        from app.services.credit_scoring import actualizar_score_tras_pago
        actualizar_score_tras_pago(db, orden.usuario_id, orden.id)
    except ImportError:
        logger.debug("Credit scoring no disponible aun")
    except Exception as e:
        logger.error(f"Error actualizando credit scoring: {e}")


# ─── Pago a proveedor ─────────────────────────────────────────────

def registrar_pago_proveedor(db: Session, orden_id: int) -> Orden | None:
    """
    Marca el pago al proveedor como realizado.
    En produccion esto se conectaria con SPEI o transferencia bancaria.
    """
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        logger.error(f"Orden {orden_id} no encontrada")
        return None

    if not orden.pagado:
        logger.error(f"Orden {orden_id} no ha sido pagada por el cliente aun")
        return None

    orden.pago_proveedor_status = "pagado"
    orden.pago_proveedor_fecha = datetime.utcnow()

    db.commit()
    db.refresh(orden)
    logger.info(f"Pago a proveedor registrado para orden {orden_id}: ${orden.monto_proveedor}")
    return orden


# ─── Simulacion (testing) ─────────────────────────────────────────

def simular_pago(db: Session, orden_id: int) -> Orden | None:
    """
    Simula un pago exitoso sin pasar por Stripe.
    Solo para testing / desarrollo.
    """
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        logger.error(f"Orden {orden_id} no encontrada para simular pago")
        return None

    if orden.pagado:
        logger.warning(f"Orden {orden_id} ya estaba pagada")
        return orden

    desglose = calcular_desglose(orden.total)

    orden.pagado = True
    orden.metodo_pago = "simulado"
    orden.stripe_payment_id = f"sim_{orden_id}_{int(datetime.utcnow().timestamp())}"
    orden.fecha_pago = datetime.utcnow()
    orden.comision_obraya = desglose["comision_2pct"]
    orden.monto_proveedor = orden.total
    orden.pago_proveedor_status = "pendiente"

    db.commit()
    db.refresh(orden)
    logger.info(f"Pago SIMULADO para orden {orden_id}")

    # Actualizar credit scoring del usuario
    _actualizar_credit_scoring(db, orden)

    return orden
