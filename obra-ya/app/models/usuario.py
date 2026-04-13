"""
Modelo de usuarios (obras / compradores / proveedores).
Soporta autenticacion por email/password, Google, Microsoft.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telefono = Column(String(20), unique=True, nullable=True)
    nombre = Column(String(200))
    empresa = Column(String(200))
    tipo = Column(String(20), default="residente")  # residente, maestro_obra, comprador, particular, proveedor
    obras_activas = Column(Text)  # JSON array de direcciones
    municipio_principal = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    ultimo_pedido = Column(DateTime)

    # ─── Autenticacion ────────────────────────────────────────────────
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    auth_provider = Column(String(20), default="email")  # email, google, microsoft
    auth_provider_id = Column(String(255), nullable=True)  # ID externo (Google/Microsoft sub)
    avatar_url = Column(String(500), nullable=True)
    email_verificado = Column(Boolean, default=False)
    ultimo_login = Column(DateTime, nullable=True)

    # ─── Telefono con codigo de pais ──────────────────────────────────
    telefono_codigo_pais = Column(String(5), default="+52")  # +52, +1, +57, etc.

    # ─── Rol en plataforma ────────────────────────────────────────────
    es_proveedor = Column(Boolean, default=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)

    # ��── Empresa / Rol corporativo ────────────────────────────────────
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    rol_empresa = Column(String(30))  # residente, superintendente, compras, director

    # ─── Credit scoring (para futuro lending) ──────��──────────────────
    score_credito = Column(Float, default=50.0)  # 0-100
    total_gastado = Column(Float, default=0)
    total_pedidos_completados = Column(Integer, default=0)
    promedio_dias_pago = Column(Float)
    pedidos_pagados_a_tiempo = Column(Integer, default=0)
    pedidos_pagados_tarde = Column(Integer, default=0)
