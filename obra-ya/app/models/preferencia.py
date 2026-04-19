"""
Preferencias persistentes de usuarios — cross-session memory para el agente.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index

from app.database import Base


class PreferenciaUsuario(Base):
    __tablename__ = "preferencias_usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    clave = Column(String(100), nullable=False)   # ej "proveedor_favorito"
    valor = Column(Text)                           # ej "Concretos JAL"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_pref_usuario_clave", "usuario_id", "clave", unique=True),
    )
