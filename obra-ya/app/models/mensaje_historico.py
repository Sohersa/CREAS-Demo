"""
Modelo para persistir historial de conversaciones WhatsApp.
Reemplaza el dict en memoria de agente_claude.py.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.database import Base


class MensajeHistorico(Base):
    __tablename__ = "mensajes_historicos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telefono = Column(String(20), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # "user" o "assistant"
    content = Column(Text, nullable=False)
    pedido_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_mensajes_telefono_created", "telefono", "created_at"),
    )
