"""
Modelo de ordenes — ciclo de vida post-cotizacion.
Una Orden se crea cuando el usuario elige un proveedor de la comparativa.
Flujo: confirmada → preparando → en_transito → en_obra → entregada
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from app.database import Base


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Status: confirmada, preparando, en_transito, en_obra, entregada, con_incidencia, cancelada
    status = Column(String(20), default="confirmada")

    # Snapshot del pedido (denormalizado para consultas rapidas)
    items = Column(Text)                # JSON de items de la cotizacion
    total = Column(Float)
    direccion_entrega = Column(String(300))
    municipio_entrega = Column(String(100))
    latitud_entrega = Column(Float)
    longitud_entrega = Column(Float)
    colonia_entrega = Column(String(100))
    codigo_postal_entrega = Column(String(10))

    # Timestamps por etapa (se llenan conforme avanza)
    confirmada_at = Column(DateTime, default=datetime.utcnow)
    preparando_at = Column(DateTime)
    en_transito_at = Column(DateTime)
    en_obra_at = Column(DateTime)
    entregada_at = Column(DateTime)
    cancelada_at = Column(DateTime)

    # Entrega
    fecha_entrega_prometida = Column(DateTime)      # Cuando dijo el proveedor que llegaba
    fecha_entrega_real = Column(DateTime)            # Cuando realmente llego
    tiempo_entrega_minutos = Column(Integer)         # Calculado: en_transito → entregada

    # Info del transporte (proveedor la da)
    nombre_chofer = Column(String(200))
    telefono_chofer = Column(String(20))
    placas_vehiculo = Column(String(20))
    tipo_vehiculo = Column(String(50))               # torton, trailer, camioneta, olla
    notas_proveedor = Column(Text)

    # ─── Pagos ─────────────────────────────────────────────────────────
    pagado = Column(Boolean, default=False)
    metodo_pago = Column(String(30))  # tarjeta, transferencia, efectivo
    stripe_payment_id = Column(String(200))
    fecha_pago = Column(DateTime)
    comision_obraya = Column(Float)  # 2% del total
    monto_proveedor = Column(Float)  # total - comision
    pago_proveedor_status = Column(String(30), default="pendiente")  # pendiente, pagado
    pago_proveedor_fecha = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
