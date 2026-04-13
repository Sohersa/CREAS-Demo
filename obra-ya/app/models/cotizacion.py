"""
Modelo de cotizaciones (una por cada proveedor que responde a un pedido).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from app.database import Base


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    status = Column(String(20), default="enviada")
    # Status posibles: enviada, respondida, sin_respuesta, rechazada
    items = Column(Text)  # JSON array con precio por cada item
    subtotal = Column(Float, default=0)
    costo_flete = Column(Float, default=0)
    total = Column(Float, default=0)
    tiempo_entrega = Column(String(50))
    vigencia = Column(DateTime)
    notas_proveedor = Column(Text)
    enviada_at = Column(DateTime, default=datetime.utcnow)
    respondida_at = Column(DateTime)


class Comparativa(Base):
    __tablename__ = "comparativas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    cotizaciones_ids = Column(Text)  # JSON array de IDs de cotizaciones
    tabla_comparativa = Column(Text)  # Texto formateado para WhatsApp
    recomendacion = Column(Text)
    enviada_at = Column(DateTime)
    elegida_cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"))
