"""
Modelo de solicitudes a proveedores — cuando Nico les pide cotizacion por WhatsApp.
Cada pedido genera N solicitudes (una por proveedor contactado).

Flujo:
  enviada → respondida (proveedor contesto con precio)
  enviada → recordatorio_enviado → respondida
  enviada → sin_respuesta (timeout, no contesto)
  enviada → rechazada (proveedor dijo que no tiene stock)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from app.database import Base


class SolicitudProveedor(Base):
    __tablename__ = "solicitudes_proveedor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)

    # Status: enviada, recordatorio_enviado, respondida, sin_respuesta, rechazada
    status = Column(String(25), default="enviada")

    # Mensaje que Nico le mando al proveedor
    mensaje_enviado = Column(Text)
    whatsapp_msg_id = Column(String(100))
    error_envio = Column(Text)

    # Respuesta del proveedor (texto crudo)
    respuesta_cruda = Column(Text)

    # Respuesta parseada por la IA
    precio_total = Column(Float)                    # Precio total cotizado
    precio_desglose = Column(Text)                  # JSON: [{producto, precio_unitario, cantidad}]
    tiempo_entrega = Column(String(100))            # "mañana a las 7", "2 días"
    incluye_flete = Column(Boolean)
    costo_flete = Column(Float)
    notas = Column(Text)                            # Condiciones, observaciones del proveedor
    disponibilidad = Column(String(50))             # "inmediata", "24hrs", "sin stock"

    # Tracking de tiempos
    enviada_at = Column(DateTime, default=datetime.utcnow)
    recordatorio_at = Column(DateTime)              # Cuando se le insistio
    respondida_at = Column(DateTime)                # Cuando contesto
    tiempo_respuesta_minutos = Column(Integer)      # Calculado

    # Cuantas veces se le insistio
    recordatorios_enviados = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
