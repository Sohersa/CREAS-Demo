"""
Modelo de productos/materiales que ofrece cada proveedor.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from app.database import Base


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    catalogo_id = Column(Integer, ForeignKey("catalogo_maestro.id"))  # Apunta al producto estandar
    categoria = Column(String(50), nullable=False)  # concreto, acero, agregados, etc.
    nombre = Column(String(200), nullable=False)  # Nombre como le llama ESTE proveedor
    nombre_proveedor = Column(String(200))  # Nombre original del proveedor (si difiere)
    descripcion = Column(Text)
    especificaciones = Column(Text)  # JSON con specs tecnicas
    unidad = Column(String(20), nullable=False)  # m3, pieza, kg, ton, bulto, viaje, cubeta, rollo
    precio_unitario = Column(Float, nullable=False)  # MXN
    precio_incluye_flete = Column(Boolean, default=False)
    costo_flete_km = Column(Float, default=0)  # MXN por km
    disponibilidad = Column(String(20), default="inmediata")  # inmediata, 24h, 48h, sobre_pedido
    stock_actual = Column(Integer)
    precio_actualizado = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
