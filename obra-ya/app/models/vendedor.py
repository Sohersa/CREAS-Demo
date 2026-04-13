"""
Modelo de vendedores — personas que trabajan para un proveedor.
Cada proveedor puede tener múltiples vendedores con sus propios números WhatsApp.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from app.database import Base


class Vendedor(Base):
    __tablename__ = "vendedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)

    nombre = Column(String(200), nullable=False)
    telefono_whatsapp = Column(String(20), nullable=False)
    email = Column(String(200))
    rol = Column(String(50), default="vendedor")  # vendedor, gerente, mostrador, almacen

    # Performance
    solicitudes_atendidas = Column(Integer, default=0)
    tiempo_respuesta_promedio = Column(Integer)  # minutos
    calificacion = Column(Float, default=4.0)

    # Availability
    disponible = Column(Boolean, default=True)  # false = vacaciones, no disponible
    horario = Column(String(100))  # "L-V 8:00-18:00"
    categorias_especialidad = Column(Text)  # JSON: ["acero", "cemento"] — what they know about

    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
