"""
Modelo de calificaciones — rating auto-calculado por entrega.
No son estrellas manuales: se calculan de datos reales (puntualidad, incidencias, etc).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from app.database import Base


class CalificacionProveedor(Base):
    __tablename__ = "calificaciones_proveedor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False, unique=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Scores auto-calculados (0.0 a 5.0 cada uno)
    puntualidad = Column(Float)                     # Basado en fecha prometida vs real
    cantidad_correcta = Column(Float)               # Basado en incidencias de cantidad
    especificacion_correcta = Column(Float)         # Basado en incidencias de spec
    sin_incidencias = Column(Float)                 # 5.0 si cero problemas

    # Score compuesto (promedio ponderado)
    calificacion_total = Column(Float)              # Se guarda tambien en Proveedor.calificacion

    # Feedback manual opcional del usuario (via WhatsApp)
    comentario_usuario = Column(Text)
    estrellas_usuario = Column(Integer)             # 1-5, override manual

    auto_calculada = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
