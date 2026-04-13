"""
Modelos de presupuesto de obra — control de consumo de materiales.
PresupuestoObra: encabezado del presupuesto por obra.
PartidaPresupuesto: linea de material con cantidades y montos.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from app.database import Base


class PresupuestoObra(Base):
    __tablename__ = "presupuestos_obra"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    nombre_obra = Column(String(300), nullable=False)  # "Torre Norte", "Residencial Los Pinos"
    direccion = Column(String(500))

    presupuesto_total = Column(Float, default=0)  # Total $ budget
    gastado_total = Column(Float, default=0)  # Running total spent
    porcentaje_consumido = Column(Float, default=0)  # 0-100

    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    fecha_inicio = Column(DateTime)
    fecha_fin_estimada = Column(DateTime)


class PartidaPresupuesto(Base):
    __tablename__ = "partidas_presupuesto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos_obra.id"), nullable=False)
    catalogo_id = Column(Integer, ForeignKey("catalogo_maestro.id"), nullable=True)

    nombre_material = Column(String(300), nullable=False)  # "Concreto f'c 250"
    categoria = Column(String(50))  # concreto, acero, etc.
    unidad = Column(String(30))  # m3, piezas, bultos

    cantidad_presupuestada = Column(Float, nullable=False)
    cantidad_consumida = Column(Float, default=0)
    porcentaje_consumido = Column(Float, default=0)

    precio_unitario_estimado = Column(Float)  # Budget unit price
    monto_presupuestado = Column(Float)  # cantidad * precio_unitario_estimado
    monto_gastado = Column(Float, default=0)  # Actual spent

    alerta_50_enviada = Column(Boolean, default=False)
    alerta_80_enviada = Column(Boolean, default=False)
    alerta_100_enviada = Column(Boolean, default=False)
    bloqueado = Column(Boolean, default=False)  # True when 100% reached

    created_at = Column(DateTime, default=datetime.utcnow)
