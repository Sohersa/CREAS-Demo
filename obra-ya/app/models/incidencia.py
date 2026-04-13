"""
Modelo de incidencias — problemas reportados en entregas.
El usuario reporta por WhatsApp, la IA clasifica y registra.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from app.database import Base


class IncidenciaEntrega(Base):
    __tablename__ = "incidencias_entrega"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Tipo: cantidad_incorrecta, especificacion, entrega_tarde, material_danado,
    #        no_llego, cobro_diferente, otro
    tipo = Column(String(30), nullable=False)

    # Severidad: leve, media, grave
    severidad = Column(String(10), default="media")

    descripcion_usuario = Column(Text)              # Mensaje original del usuario
    descripcion_interpretada = Column(Text)         # Interpretacion de la IA

    # Para problemas de cantidad
    cantidad_esperada = Column(Float)
    cantidad_recibida = Column(Float)
    unidad = Column(String(20))

    # Resolucion
    # Status: abierta, en_revision, resuelta, cerrada
    status = Column(String(20), default="abierta")
    resolucion = Column(Text)                       # Como se resolvio
    resuelta_at = Column(DateTime)

    # Evidencia (IDs de fotos de WhatsApp, JSON array)
    fotos_ids = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
