"""
Catalogo Maestro de productos y sus aliases.
Esta es la tabla canonica — todos los proveedores apuntan aqui.
Cada producto tiene multiples aliases (nombres alternativos).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from app.database import Base


class CatalogoMaestro(Base):
    """
    Los 30 productos estandar de ObraYa.
    Cada uno tiene un nombre canonico, categoria, y unidad oficial.
    """
    __tablename__ = "catalogo_maestro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False, unique=True)  # Nombre oficial estandar
    categoria = Column(String(50), nullable=False)
    # Categorias: concreto, acero, agregados, cementantes, block, tuberia, impermeabilizante, electrico
    subcategoria = Column(String(100))  # Ej: "premezclado", "corrugada", etc.
    unidad = Column(String(20), nullable=False)  # m3, pieza, kg, ton, bulto, cubeta, rollo
    descripcion = Column(Text)  # Descripcion tecnica estandar
    especificaciones = Column(Text)  # JSON con specs clave (resistencia, diametro, etc.)
    precio_referencia = Column(Float)  # Precio promedio de mercado GDL (para detectar errores)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AliasProducto(Base):
    """
    Todos los nombres alternativos con los que se conoce un producto.
    Incluye: nombres de proveedor, jerga de obra, transcripciones de voz, etc.
    """
    __tablename__ = "aliases_producto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    catalogo_id = Column(Integer, ForeignKey("catalogo_maestro.id"), nullable=False)
    alias = Column(String(300), nullable=False)  # El nombre alternativo
    fuente = Column(String(50), default="manual")
    # Fuentes: "manual", "proveedor", "usuario", "voz", "ia"
    # - manual: puesto a mano por el admin
    # - proveedor: asi le llama un proveedor especifico
    # - usuario: asi lo pidio un usuario y Claude lo interpreto
    # - voz: transcripcion de audio con errores tipicos
    # - ia: detectado automaticamente por Claude
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))  # Opcional: de que proveedor viene
    confianza = Column(Float, default=1.0)  # 0-1, que tan seguro es el mapeo
    veces_usado = Column(Integer, default=0)  # Cuantas veces se ha usado este alias
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
