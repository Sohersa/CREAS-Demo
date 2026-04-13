"""
Modelo de seguimiento — log de eventos de cada orden.
Cada cambio de status genera un registro aqui (como un timeline).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.database import Base


class SeguimientoEntrega(Base):
    __tablename__ = "seguimiento_entregas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False)

    status_anterior = Column(String(20))
    status_nuevo = Column(String(20), nullable=False)

    # Quien disparo el cambio: sistema, proveedor, usuario, admin
    origen = Column(String(20), default="sistema")
    nota = Column(Text)

    # Tracking de WhatsApp
    mensaje_enviado = Column(Text)                  # Mensaje que se mando al usuario
    whatsapp_message_id = Column(String(100))       # ID de Meta para confirmar lectura

    created_at = Column(DateTime, default=datetime.utcnow)
