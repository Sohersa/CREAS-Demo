"""
Precio Historico — cada dato de precio que pasa por ObraYa se guarda aqui.

Esta es la tabla mas valiosa del sistema. Cada vez que un proveedor responde
con un precio, se registra aqui. Con el tiempo esto genera:
  - Curvas de precio por producto por zona
  - Deteccion de proveedores caros/baratos
  - Prediccion de aumentos de precios
  - Benchmark de mercado
  - Estacionalidad de materiales
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from app.database import Base


class PrecioHistorico(Base):
    """
    Un registro = un precio de un producto de un proveedor en un momento.
    """
    __tablename__ = "precios_historicos"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Que producto
    catalogo_id = Column(Integer, ForeignKey("catalogo_maestro.id"), nullable=True)
    producto_nombre = Column(String(300), nullable=False)  # Nombre tal como lo dio el proveedor
    producto_normalizado = Column(String(300))  # Nombre mapeado al catalogo maestro
    categoria = Column(String(50))  # concreto, acero, agregados, etc.

    # Quien cotizo
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    proveedor_nombre = Column(String(200))

    # El precio
    precio_unitario = Column(Float, nullable=False)
    unidad = Column(String(30), nullable=False)  # m3, pieza, bulto, kg, ton, viaje, cubeta, rollo
    cantidad_cotizada = Column(Float)  # Cuanto pidio el usuario
    subtotal = Column(Float)  # precio_unitario * cantidad

    # Flete
    incluye_flete = Column(Boolean, default=False)
    costo_flete = Column(Float, default=0)
    flete_por_unidad = Column(Float)  # costo_flete / cantidad (para normalizar)

    # Precio efectivo (unitario + flete prorrateado)
    precio_efectivo = Column(Float)  # precio_unitario + (costo_flete / cantidad)

    # Contexto
    zona = Column(String(100))  # Municipio/ciudad de entrega
    tiempo_entrega = Column(String(100))  # "manana", "3 dias", etc.
    disponibilidad = Column(String(50))  # inmediata, 24hrs, etc.
    condiciones = Column(String(300))  # pago contra entrega, credito, etc.

    # Trazabilidad
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes_proveedor.id"), nullable=True)
    fuente = Column(String(30), default="cotizacion_activa")
    # Fuentes: cotizacion_activa, manual, referencia_db, importacion

    # Metadatos
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    dia_semana = Column(Integer)  # 0=lunes, 6=domingo
    mes = Column(Integer)
    anio = Column(Integer)
    trimestre = Column(Integer)

    # Validacion
    es_outlier = Column(Boolean, default=False)  # Marcado si el precio es muy raro
    confianza = Column(Float, default=1.0)  # 0-1, que tan confiable es este dato
    notas = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
