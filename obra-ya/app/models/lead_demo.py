"""
LeadDemo — tracking de usuarios que probaron el demo sin darse de alta.
Para despues invitarlos a unirse a ObraYa.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index

from app.database import Base


class LeadDemo(Base):
    __tablename__ = "leads_demo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telefono = Column(String(20), index=True)
    nombre = Column(String(150))
    email = Column(String(150))
    empresa = Column(String(150))

    # Que hizo en el demo
    mensaje_inicial = Column(Text)           # Lo que escribio para probar
    origen = Column(String(50))              # landing, playground, etc.
    user_agent = Column(String(300))
    ip = Column(String(50))
    referer = Column(String(300))

    # Estado del lead
    status = Column(String(30), default="nuevo")
    # nuevo, contactado, respondio, convertido, descartado

    mensajes_recibidos = Column(Integer, default=0)
    mensajes_enviados = Column(Integer, default=0)
    ultimo_contacto = Column(DateTime)

    notas = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_lead_demo_tel_origen", "telefono", "origen"),
    )
