"""
Modelo de pedidos de materiales.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Date, ForeignKey
from app.database import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    status = Column(String(20), default="interpretando")
    # Status posibles: interpretando, cotizando, comparando, enviado, aceptado, entregado, cancelado
    mensaje_original = Column(Text)  # El mensaje tal cual llego
    pedido_interpretado = Column(Text)  # JSON del pedido procesado por Claude
    direccion_entrega = Column(String(300))
    municipio_entrega = Column(String(100))
    fecha_entrega = Column(Date)
    horario_entrega = Column(String(50))
    contacto_obra = Column(Text)  # JSON: nombre + telefono
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
