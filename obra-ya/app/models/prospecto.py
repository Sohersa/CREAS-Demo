"""
ProspectoProveedor — despacho de materiales al que queremos contactar para
ofrecerle unirse a ObraYa. CRM de outreach B2B.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean

from app.database import Base


class ProspectoProveedor(Base):
    """
    Un despacho / materialista / ferreteria que AUN NO es proveedor de ObraYa,
    pero que queremos contactar automaticamente para sumarlo.
    """
    __tablename__ = "prospectos_proveedor"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identidad
    nombre = Column(String(200), nullable=False)
    telefono = Column(String(20), nullable=False, index=True)
    email = Column(String(150))
    direccion = Column(String(300))
    municipio = Column(String(100))
    estado = Column(String(50), default="Jalisco")

    # Clasificacion
    categoria = Column(String(50))              # concreto, acero, agregados, etc.
    tipo = Column(String(20))                   # pequeno, mediano, grande
    tamano_estimado = Column(String(50))        # "2-5 empleados", "medio", etc.

    # Origen del lead
    origen = Column(String(50))                 # google_maps, directorio, manual, referido, webscrape
    origen_url = Column(String(500))            # URL de donde salio (Maps, etc)
    calificacion_google = Column(Float)         # Rating publico

    # Status de outreach
    status = Column(String(30), default="pendiente", index=True)
    # Status posibles:
    #   pendiente           — en la cola, aun no contactamos
    #   contactado          — enviamos primer mensaje
    #   sin_respuesta       — contactado pero no respondio
    #   dialogo_activo      — respondio, conversando
    #   interesado          — dijo que le interesa
    #   rechazado           — dijo que no
    #   opt_out             — pidio no contactar
    #   invalido            — numero no existe / error
    #   convertido          — ya esta en la tabla Proveedor (lead cerrado)
    #   descartado          — nosotros decidimos no continuar

    # Intentos
    intentos_contacto = Column(Integer, default=0)
    ultimo_contacto_at = Column(DateTime)
    proximo_contacto_at = Column(DateTime)       # programado para follow-up
    mensajes_enviados = Column(Integer, default=0)
    mensajes_recibidos = Column(Integer, default=0)

    # Senales de interes (se llenan segun responda)
    score_interes = Column(Integer, default=0)   # 0-100
    ultima_respuesta = Column(Text)              # texto de la ultima respuesta que mando
    ultima_respuesta_at = Column(DateTime)
    razon_rechazo = Column(String(200))          # si rechazo, por que

    # Conversion (cuando se vuelve Proveedor)
    proveedor_id = Column(Integer)               # Si se convirtio, su id en Proveedor
    convertido_at = Column(DateTime)

    # Metadatos
    notas = Column(Text)                         # notas internas del equipo de ventas
    campana = Column(String(100))                # nombre de la campana/batch
    activo = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
