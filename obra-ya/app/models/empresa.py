"""
Modelo de empresas constructoras.
Permite agrupar usuarios por empresa y configurar flujos de aprobacion.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(300), nullable=False)
    rfc = Column(String(20))
    direccion = Column(String(500))
    telefono = Column(String(20))
    email = Column(String(200))

    # Approval settings
    requiere_aprobacion = Column(Boolean, default=False)  # Optional feature
    limite_sin_aprobacion = Column(Float, default=0)  # Below this amount, no approval needed

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)
