"""
Modelo de proveedores de materiales de construccion.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.database import Base


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(20), nullable=False)  # grande, mediano, pequeno
    telefono_whatsapp = Column(String(20))
    email = Column(String(100))
    direccion = Column(String(300))
    municipio = Column(String(100))  # Zapopan, Tlaquepaque, etc.
    latitud = Column(Float)
    longitud = Column(Float)
    categorias = Column(Text)  # JSON array: ["concreto", "acero"]
    horario_atencion = Column(String(100), default="Lun-Sab 7:00-17:00")
    tiene_api = Column(Boolean, default=False)
    api_url = Column(String(300))
    metodo_contacto = Column(String(20), default="whatsapp")  # whatsapp, api, telefono, email
    calificacion = Column(Float, default=4.0)
    total_pedidos = Column(Integer, default=0)
    pedidos_cumplidos = Column(Integer, default=0)
    tiempo_respuesta_promedio = Column(Integer, default=30)  # minutos

    # Metricas de cumplimiento (auto-calculadas por calificacion_service)
    tasa_puntualidad = Column(Float, default=1.0)               # 0.0-1.0 tasa de entregas a tiempo
    tasa_cantidad_correcta = Column(Float, default=1.0)         # 0.0-1.0 sin problemas de cantidad
    tasa_especificacion_correcta = Column(Float, default=1.0)   # 0.0-1.0 sin problemas de spec
    total_incidencias = Column(Integer, default=0)
    total_ordenes_completadas = Column(Integer, default=0)

    codigo_registro = Column(String(20), unique=True, nullable=True)  # Para onboarding via WhatsApp

    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
