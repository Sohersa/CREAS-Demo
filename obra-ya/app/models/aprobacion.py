"""
Modelo de aprobaciones — flujo de autorizacion de compras corporativas.
Cuando una empresa requiere aprobacion, las ordenes pasan por este flujo
antes de procesarse.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from app.database import Base


class Aprobacion(Base):
    __tablename__ = "aprobaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    solicitante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    aprobador_id = Column(Integer, ForeignKey("usuarios.id"))

    status = Column(String(20), default="pendiente")  # pendiente, aprobada, rechazada, expirada
    monto = Column(Float)
    nota_solicitud = Column(Text)
    nota_respuesta = Column(Text)

    solicitada_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    respondida_at = Column(DateTime)
    expira_at = Column(DateTime)  # Auto-expire after 24hrs

    # WhatsApp tracking
    mensaje_enviado_id = Column(String(100))
    recordatorios_enviados = Column(Integer, default=0)
