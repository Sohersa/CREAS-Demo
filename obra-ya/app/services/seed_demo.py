"""
Seed de datos demo — crea cuentas de prueba para simular procesos completos.
Se ejecuta una vez al startup. Si ya existen, no duplica.
"""
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.usuario import Usuario
from app.models.proveedor import Proveedor
from app.models.empresa import Empresa
from app.models.miembro_empresa import MiembroEmpresa

logger = logging.getLogger(__name__)

# ── Demo accounts ────────────────────────────────────────────
DEMO_EMPRESA = {
    "nombre": "Constructora Demo SA de CV",
    "rfc": "CDM000101XXX",
    "direccion": "Av. Patria 1234, Zapopan, Jalisco",
    "telefono": "3300000001",
    "email": "demo@constructorademo.com",
    "requiere_aprobacion": True,
    "limite_sin_aprobacion": 100000.0,
}

DEMO_USUARIOS = [
    {
        "telefono": "5200000001",
        "nombre": "Admin Demo",
        "email": "admin@obraya.demo",
        "tipo": "comprador",
        "empresa": "Constructora Demo SA de CV",
        "rol_empresa": "director",
        "municipio_principal": "Zapopan",
    },
    {
        "telefono": "5200000002",
        "nombre": "Residente Demo",
        "email": "residente@obraya.demo",
        "tipo": "residente",
        "empresa": "Constructora Demo SA de CV",
        "rol_empresa": "residente",
        "municipio_principal": "Zapopan",
    },
    {
        "telefono": "5200000003",
        "nombre": "Superintendente Demo",
        "email": "super@obraya.demo",
        "tipo": "maestro_obra",
        "empresa": "Constructora Demo SA de CV",
        "rol_empresa": "superintendente",
        "municipio_principal": "Guadalajara",
    },
    {
        "telefono": "5200000004",
        "nombre": "Compras Demo",
        "email": "compras@obraya.demo",
        "tipo": "comprador",
        "empresa": "Constructora Demo SA de CV",
        "rol_empresa": "compras",
        "municipio_principal": "Zapopan",
    },
]

DEMO_PROVEEDORES = [
    {
        "nombre": "Materiales Zapopan Demo",
        "tipo": "mediano",
        "telefono_whatsapp": "5200000010",
        "email": "zapopan@proveedordemo.com",
        "direccion": "Av. Vallarta 567, Zapopan",
        "municipio": "Zapopan",
        "categorias": '["acero", "cemento", "arena", "grava", "block"]',
        "calificacion": 4.2,
    },
    {
        "nombre": "Ferreteria GDL Demo",
        "tipo": "pequeno",
        "telefono_whatsapp": "5200000011",
        "email": "gdl@proveedordemo.com",
        "direccion": "Calle Lopez Cotilla 890, Guadalajara",
        "municipio": "Guadalajara",
        "categorias": '["ferreteria", "plomeria", "electricidad", "pintura"]',
        "calificacion": 4.5,
    },
    {
        "nombre": "Concretos del Bajio Demo",
        "tipo": "grande",
        "telefono_whatsapp": "5200000012",
        "email": "bajio@proveedordemo.com",
        "direccion": "Carretera a Saltillo km 5, Tlaquepaque",
        "municipio": "Tlaquepaque",
        "categorias": '["concreto", "cemento", "mortero", "prefabricados"]',
        "calificacion": 3.8,
    },
]

DEMO_MIEMBROS = [
    # (usuario_telefono, rol, puede_pedir, puede_aprobar, puede_pagar, limite_aprobacion)
    ("5200000001", "director", True, True, True, None),      # Director — puede todo
    ("5200000002", "residente", True, False, False, 50000),   # Residente — pide hasta $50k
    ("5200000003", "superintendente", True, True, False, 150000),  # Super — aprueba hasta $150k
    ("5200000004", "compras", True, True, True, 500000),      # Compras — aprueba hasta $500k
]


def sembrar_datos_demo():
    """Crea las cuentas demo si no existen."""
    db = SessionLocal()
    try:
        creados = 0

        # 1. Empresa demo
        empresa = db.query(Empresa).filter(Empresa.rfc == DEMO_EMPRESA["rfc"]).first()
        if not empresa:
            empresa = Empresa(**DEMO_EMPRESA)
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
            creados += 1
            logger.info(f"[Seed] Empresa demo creada: {empresa.nombre}")

        # 2. Usuarios demo
        for u_data in DEMO_USUARIOS:
            existing = db.query(Usuario).filter(Usuario.telefono == u_data["telefono"]).first()
            if not existing:
                user = Usuario(
                    telefono=u_data["telefono"],
                    nombre=u_data["nombre"],
                    email=u_data["email"],
                    tipo=u_data["tipo"],
                    empresa=u_data["empresa"],
                    rol_empresa=u_data["rol_empresa"],
                    municipio_principal=u_data["municipio_principal"],
                    empresa_id=empresa.id,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                creados += 1
                logger.info(f"[Seed] Usuario demo creado: {user.nombre} ({user.telefono})")

        # 3. Proveedores demo
        for p_data in DEMO_PROVEEDORES:
            existing = db.query(Proveedor).filter(Proveedor.telefono_whatsapp == p_data["telefono_whatsapp"]).first()
            if not existing:
                prov = Proveedor(**p_data)
                db.add(prov)
                db.commit()
                db.refresh(prov)
                creados += 1
                logger.info(f"[Seed] Proveedor demo creado: {prov.nombre} ({prov.telefono_whatsapp})")

                # Create associated user for provider portal
                prov_user = db.query(Usuario).filter(Usuario.telefono == p_data["telefono_whatsapp"]).first()
                if not prov_user:
                    prov_user = Usuario(
                        telefono=p_data["telefono_whatsapp"],
                        nombre=p_data["nombre"],
                        email=p_data["email"],
                        tipo="proveedor",
                        es_proveedor=True,
                        proveedor_id=prov.id,
                        municipio_principal=p_data["municipio"],
                    )
                    db.add(prov_user)
                    db.commit()

        # 4. Miembros de empresa
        for tel, rol, puede_pedir, puede_aprobar, puede_pagar, limite in DEMO_MIEMBROS:
            user = db.query(Usuario).filter(Usuario.telefono == tel).first()
            if not user:
                continue
            existing = db.query(MiembroEmpresa).filter(
                MiembroEmpresa.empresa_id == empresa.id,
                MiembroEmpresa.usuario_id == user.id,
            ).first()
            if not existing:
                miembro = MiembroEmpresa(
                    empresa_id=empresa.id,
                    usuario_id=user.id,
                    rol=rol,
                    puede_pedir=puede_pedir,
                    puede_aprobar=puede_aprobar,
                    puede_pagar=puede_pagar,
                    limite_aprobacion=limite,
                )
                db.add(miembro)
                creados += 1

        db.commit()

        if creados:
            logger.info(f"[Seed] {creados} registros demo creados")
        else:
            logger.info("[Seed] Datos demo ya existian — nada que crear")

    except Exception as e:
        logger.error(f"[Seed] Error sembrando datos demo: {e}")
        db.rollback()
    finally:
        db.close()
