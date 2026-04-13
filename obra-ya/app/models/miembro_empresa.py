"""
Modelo de miembros de empresa — roles y permisos dentro de una constructora.
Roles: residente, superintendente, compras, director, admin
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from app.database import Base


class MiembroEmpresa(Base):
    __tablename__ = "miembros_empresa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    rol = Column(String(30), nullable=False)
    # Roles: residente, superintendente, compras, director, admin
    puede_pedir = Column(Boolean, default=True)
    puede_aprobar = Column(Boolean, default=False)
    puede_pagar = Column(Boolean, default=False)
    limite_aprobacion = Column(Float)  # Max amount this person can approve
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
