"""
Panel de administracion — endpoints API + panel HTML interactivo.
"""
import json
import os
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.catalogo import CatalogoMaestro, AliasProducto
from app.models.pedido import Pedido
from app.models.cotizacion import Cotizacion
from app.models.usuario import Usuario
from app.models.orden import Orden
from app.models.seguimiento import SeguimientoEntrega
from app.models.incidencia import IncidenciaEntrega
from app.models.calificacion import CalificacionProveedor
from app.models.solicitud_proveedor import SolicitudProveedor
from app.services.orden_service import avanzar_status, obtener_timeline
from app.services.incidencia_service import resolver_incidencia
from app.services.notificaciones import enviar_notificacion_por_status
from app.utils.telefono import normalizar_telefono_mx

router = APIRouter(prefix="/admin", tags=["admin"])


# --- MODELOS PYDANTIC ---

class PrecioUpdate(BaseModel):
    nuevo_precio: float


class AvanzarOrdenBody(BaseModel):
    status: str
    nota: str = ""
    nombre_chofer: str = ""
    telefono_chofer: str = ""
    placas_vehiculo: str = ""
    tipo_vehiculo: str = ""


class ResolverIncidenciaBody(BaseModel):
    resolucion: str


class ProveedorCreate(BaseModel):
    nombre: str
    tipo: str = "pequeno"
    municipio: str = ""
    telefono_whatsapp: str = ""
    categorias: list[str] = []
    metodo_contacto: str = "whatsapp"


# --- API ENDPOINTS ---


@router.post("/api/seed")
def seed_database(db: Session = Depends(get_db)):
    """Seed the database remotely with catalogo maestro and proveedores data."""
    # Resolve data directory relative to this file (works locally and on Railway)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    catalogo_path = os.path.join(base_dir, "data", "catalogo_maestro.json")
    proveedores_path = os.path.join(base_dir, "data", "proveedores_seed.json")

    summary = {
        "catalogo_maestro": 0,
        "aliases": 0,
        "proveedores": 0,
        "productos": 0,
        "productos_vinculados": 0,
        "skipped_existing": False,
    }

    # --- Step 1: Load Catalogo Maestro + Aliases ---
    existing_catalogo = db.query(CatalogoMaestro).count()
    if existing_catalogo > 0:
        summary["skipped_existing"] = True
        summary["catalogo_maestro"] = existing_catalogo
        summary["aliases"] = db.query(AliasProducto).count()
    else:
        with open(catalogo_path, "r", encoding="utf-8") as f:
            catalogo_data = json.load(f)

        for item in catalogo_data["catalogo"]:
            maestro = CatalogoMaestro(
                nombre=item["nombre"],
                categoria=item["categoria"],
                subcategoria=item.get("subcategoria"),
                unidad=item["unidad"],
                descripcion=item.get("descripcion", ""),
                precio_referencia=item.get("precio_referencia"),
                activo=True,
            )
            db.add(maestro)
            db.flush()
            summary["catalogo_maestro"] += 1

            # Official name as first alias
            alias_oficial = AliasProducto(
                catalogo_id=maestro.id,
                alias=item["nombre"].lower(),
                fuente="manual",
                confianza=1.0,
                activo=True,
            )
            db.add(alias_oficial)
            summary["aliases"] += 1

            # All additional aliases
            for alias_text in item.get("aliases", []):
                alias = AliasProducto(
                    catalogo_id=maestro.id,
                    alias=alias_text.lower().strip(),
                    fuente="manual",
                    confianza=1.0,
                    activo=True,
                )
                db.add(alias)
                summary["aliases"] += 1

        db.commit()

    # --- Step 2: Load Proveedores + Productos ---
    existing_proveedores = db.query(Proveedor).count()
    if existing_proveedores > 0:
        summary["proveedores"] = existing_proveedores
        summary["productos"] = db.query(Producto).count()
        summary["productos_vinculados"] = db.query(Producto).filter(
            Producto.catalogo_id.isnot(None)
        ).count()
    else:
        with open(proveedores_path, "r", encoding="utf-8") as f:
            prov_data = json.load(f)

        for prov_item in prov_data["proveedores"]:
            proveedor = Proveedor(
                nombre=prov_item["nombre"],
                tipo=prov_item["tipo"],
                municipio=prov_item["municipio"],
                telefono_whatsapp=normalizar_telefono_mx(prov_item.get("telefono_whatsapp", "")),
                categorias=json.dumps(prov_item["categorias"]),
                metodo_contacto=prov_item.get("metodo_contacto", "whatsapp"),
                calificacion=prov_item.get("calificacion", 4.0),
                total_pedidos=prov_item.get("total_pedidos", 0),
                pedidos_cumplidos=prov_item.get("pedidos_cumplidos", 0),
                activo=True,
            )
            db.add(proveedor)
            db.flush()
            summary["proveedores"] += 1

            for prod_item in prov_item.get("productos", []):
                # Find catalogo_id via alias matching
                nombre_lower = prod_item["nombre"].lower().strip()
                alias_match = db.query(AliasProducto).filter(
                    AliasProducto.alias == nombre_lower,
                    AliasProducto.activo == True,
                ).first()
                catalogo_id = alias_match.catalogo_id if alias_match else None

                # Fallback: partial match
                if not catalogo_id:
                    all_aliases = db.query(AliasProducto).filter(AliasProducto.activo == True).all()
                    best_match = None
                    best_len = 0
                    for a in all_aliases:
                        if a.alias in nombre_lower or nombre_lower in a.alias:
                            if len(a.alias) > best_len:
                                best_match = a
                                best_len = len(a.alias)
                    if best_match:
                        catalogo_id = best_match.catalogo_id

                producto = Producto(
                    proveedor_id=proveedor.id,
                    catalogo_id=catalogo_id,
                    categoria=prod_item["categoria"],
                    nombre=prod_item["nombre"],
                    nombre_proveedor=prod_item["nombre"],
                    unidad=prod_item["unidad"],
                    precio_unitario=prod_item["precio_unitario"],
                    disponibilidad=prod_item.get("disponibilidad", "inmediata"),
                    activo=True,
                )
                db.add(producto)
                summary["productos"] += 1

                if catalogo_id:
                    summary["productos_vinculados"] += 1
                    # Add proveedor product name as a new alias if it doesn't exist
                    exists = db.query(AliasProducto).filter(
                        AliasProducto.alias == nombre_lower,
                        AliasProducto.catalogo_id == catalogo_id,
                    ).first()
                    if not exists:
                        nuevo_alias = AliasProducto(
                            catalogo_id=catalogo_id,
                            alias=nombre_lower,
                            fuente="proveedor",
                            proveedor_id=proveedor.id,
                            confianza=1.0,
                            activo=True,
                        )
                        db.add(nuevo_alias)

        db.commit()

    return {
        "status": "ok",
        "message": "Database seeded successfully" if not summary["skipped_existing"] else "Data already exists, skipped seeding",
        "summary": summary,
    }


@router.get("/api/proveedores")
def listar_proveedores(db: Session = Depends(get_db)):
    proveedores = db.query(Proveedor).filter(Proveedor.activo == True).all()
    resultado = []
    for p in proveedores:
        productos = db.query(Producto).filter(Producto.proveedor_id == p.id, Producto.activo == True).all()
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "tipo": p.tipo,
            "municipio": p.municipio,
            "categorias": json.loads(p.categorias) if p.categorias else [],
            "metodo_contacto": p.metodo_contacto,
            "calificacion": p.calificacion,
            "total_pedidos": p.total_pedidos,
            "telefono_whatsapp": p.telefono_whatsapp,
            "productos": [
                {
                    "id": prod.id,
                    "nombre": prod.nombre,
                    "categoria": prod.categoria,
                    "precio_unitario": prod.precio_unitario,
                    "unidad": prod.unidad,
                    "disponibilidad": prod.disponibilidad,
                }
                for prod in productos
            ],
        })
    return resultado


@router.get("/api/pedidos")
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = db.query(Pedido).order_by(Pedido.created_at.desc()).limit(50).all()
    resultado = []
    for p in pedidos:
        usuario = db.query(Usuario).filter(Usuario.id == p.usuario_id).first()
        cotizaciones = db.query(Cotizacion).filter(Cotizacion.pedido_id == p.id).all()
        resultado.append({
            "id": p.id,
            "usuario": usuario.nombre if usuario else "Desconocido",
            "telefono": usuario.telefono if usuario else "",
            "status": p.status,
            "mensaje_original": p.mensaje_original,
            "direccion_entrega": p.direccion_entrega,
            "fecha_entrega": str(p.fecha_entrega) if p.fecha_entrega else "",
            "cotizaciones": len(cotizaciones),
            "created_at": p.created_at.isoformat() if p.created_at else "",
        })
    return resultado


@router.post("/api/test-whatsapp")
async def test_whatsapp(
    telefono: str = "5213333859426",
    mensaje: str = "Hola, esta es una prueba de ObraYa 🏗️",
    provider: str = "",
):
    """Envia un mensaje de prueba por WhatsApp. provider=meta|twilio|'' (default from config)."""
    results = {}

    if provider == "meta" or provider == "":
        # Try Meta
        try:
            from app.services.whatsapp import _enviar_texto as meta_enviar, WHATSAPP_API_URL
            from app.config import settings as s
            url = f"{WHATSAPP_API_URL}/{s.WHATSAPP_PHONE_ID}/messages"
            headers = {"Authorization": f"Bearer {s.WHATSAPP_TOKEN}", "Content-Type": "application/json"}
            r = await meta_enviar(url, headers, telefono, mensaje)
            results["meta"] = r
        except Exception as e:
            results["meta"] = {"error": str(e)}

    if provider == "twilio" or provider == "":
        # Try Twilio
        try:
            from app.services.whatsapp_twilio import enviar_mensaje_texto as twilio_enviar
            r = await twilio_enviar(telefono, mensaje)
            results["twilio"] = r
        except Exception as e:
            results["twilio"] = {"error": str(e)}

    return {"telefono": telefono, "results": results}


@router.get("/api/diagnostico")
def diagnostico_whatsapp():
    """Diagnostic: check which integrations are configured (no secrets exposed)."""
    from app.config import settings
    return {
        "whatsapp_provider": settings.WHATSAPP_PROVIDER,
        "whatsapp_token_set": bool(settings.WHATSAPP_TOKEN),
        "whatsapp_phone_id_set": bool(settings.WHATSAPP_PHONE_ID),
        "twilio_sid_set": bool(settings.TWILIO_ACCOUNT_SID),
        "twilio_token_set": bool(settings.TWILIO_AUTH_TOKEN),
        "twilio_number_set": bool(settings.TWILIO_WHATSAPP_NUMBER),
        "anthropic_key_set": bool(settings.ANTHROPIC_API_KEY),
        "stripe_key_set": bool(settings.STRIPE_SECRET_KEY),
        "google_client_id_set": bool(settings.GOOGLE_CLIENT_ID),
        "environment": settings.ENVIRONMENT,
    }


@router.get("/api/stats")
def obtener_stats(db: Session = Depends(get_db)):
    total_proveedores = db.query(func.count(Proveedor.id)).filter(Proveedor.activo == True).scalar()
    total_productos = db.query(func.count(Producto.id)).filter(Producto.activo == True).scalar()
    total_pedidos = db.query(func.count(Pedido.id)).scalar()
    total_usuarios = db.query(func.count(Usuario.id)).scalar()
    total_cotizaciones = db.query(func.count(Cotizacion.id)).scalar()
    total_ordenes = db.query(func.count(Orden.id)).scalar()
    ordenes_activas = db.query(func.count(Orden.id)).filter(
        Orden.status.notin_(["entregada", "cancelada"])
    ).scalar()
    ordenes_completadas = db.query(func.count(Orden.id)).filter(Orden.status == "entregada").scalar()
    total_incidencias = db.query(func.count(IncidenciaEntrega.id)).filter(
        IncidenciaEntrega.status == "abierta"
    ).scalar()

    pedidos_por_status = {}
    for status, count in db.query(Pedido.status, func.count(Pedido.id)).group_by(Pedido.status).all():
        pedidos_por_status[status] = count

    ordenes_por_status = {}
    for status, count in db.query(Orden.status, func.count(Orden.id)).group_by(Orden.status).all():
        ordenes_por_status[status] = count

    return {
        "total_proveedores": total_proveedores or 0,
        "total_productos": total_productos or 0,
        "total_pedidos": total_pedidos or 0,
        "total_usuarios": total_usuarios or 0,
        "total_cotizaciones": total_cotizaciones or 0,
        "total_ordenes": total_ordenes or 0,
        "ordenes_activas": ordenes_activas or 0,
        "ordenes_completadas": ordenes_completadas or 0,
        "incidencias_abiertas": total_incidencias or 0,
        "pedidos_por_status": pedidos_por_status,
        "ordenes_por_status": ordenes_por_status,
    }


@router.post("/api/proveedores/{proveedor_id}/productos/{producto_id}/precio")
def actualizar_precio(proveedor_id: int, producto_id: int, body: PrecioUpdate, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.proveedor_id == proveedor_id,
    ).first()
    if not producto:
        return {"error": "Producto no encontrado"}
    producto.precio_unitario = body.nuevo_precio
    producto.precio_actualizado = datetime.utcnow()
    db.commit()
    return {"ok": True, "producto": producto.nombre, "nuevo_precio": body.nuevo_precio}


@router.post("/api/proveedores")
def crear_proveedor(body: ProveedorCreate, db: Session = Depends(get_db)):
    telefono_normalizado = normalizar_telefono_mx(body.telefono_whatsapp) if body.telefono_whatsapp else ""
    proveedor = Proveedor(
        nombre=body.nombre,
        tipo=body.tipo,
        municipio=body.municipio,
        telefono_whatsapp=telefono_normalizado,
        categorias=json.dumps(body.categorias),
        metodo_contacto=body.metodo_contacto,
        activo=True,
    )
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return {"ok": True, "id": proveedor.id, "nombre": proveedor.nombre}


@router.put("/api/proveedores/{proveedor_id}")
def actualizar_proveedor(proveedor_id: int, body: ProveedorCreate, db: Session = Depends(get_db)):
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return {"error": "Proveedor no encontrado"}
    if body.nombre:
        proveedor.nombre = body.nombre
    if body.tipo:
        proveedor.tipo = body.tipo
    if body.municipio:
        proveedor.municipio = body.municipio
    if body.telefono_whatsapp:
        proveedor.telefono_whatsapp = normalizar_telefono_mx(body.telefono_whatsapp)
    if body.categorias:
        proveedor.categorias = json.dumps(body.categorias)
    if body.metodo_contacto:
        proveedor.metodo_contacto = body.metodo_contacto
    db.commit()
    return {"ok": True, "id": proveedor.id, "nombre": proveedor.nombre}


@router.delete("/api/proveedores/{proveedor_id}")
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return {"error": "Proveedor no encontrado"}
    proveedor.activo = False
    db.commit()
    return {"ok": True, "nombre": proveedor.nombre}


@router.get("/api/solicitudes")
def listar_solicitudes(db: Session = Depends(get_db)):
    """Diagnostico: ver todas las solicitudes a proveedores y su estado."""
    solicitudes = db.query(SolicitudProveedor).order_by(SolicitudProveedor.created_at.desc()).limit(50).all()
    resultado = []
    for sol in solicitudes:
        prov = db.query(Proveedor).filter(Proveedor.id == sol.proveedor_id).first()
        resultado.append({
            "id": sol.id,
            "pedido_id": sol.pedido_id,
            "proveedor_id": sol.proveedor_id,
            "proveedor_nombre": prov.nombre if prov else "?",
            "proveedor_tel": prov.telefono_whatsapp if prov else "?",
            "status": sol.status,
            "precio_total": sol.precio_total,
            "tiempo_entrega": sol.tiempo_entrega,
            "respuesta_cruda": (sol.respuesta_cruda or "")[:200],
            "enviada_at": sol.enviada_at.isoformat() if sol.enviada_at else None,
            "respondida_at": sol.respondida_at.isoformat() if sol.respondida_at else None,
            "tiempo_respuesta_min": sol.tiempo_respuesta_minutos,
            "recordatorios": sol.recordatorios_enviados,
        })
    return resultado


@router.post("/api/proveedores/normalizar-telefonos")
def normalizar_telefonos_proveedores(db: Session = Depends(get_db)):
    """Normaliza todos los telefonos de proveedores al formato 521XXXXXXXXXX."""
    proveedores = db.query(Proveedor).filter(Proveedor.telefono_whatsapp.isnot(None)).all()
    cambios = []
    for prov in proveedores:
        tel_original = prov.telefono_whatsapp or ""
        tel_nuevo = normalizar_telefono_mx(tel_original)
        if tel_nuevo != tel_original:
            cambios.append({
                "id": prov.id,
                "nombre": prov.nombre,
                "antes": tel_original,
                "despues": tel_nuevo,
            })
            prov.telefono_whatsapp = tel_nuevo
    db.commit()
    return {"ok": True, "total_normalizados": len(cambios), "cambios": cambios}


# --- ORDENES API ---

@router.get("/api/ordenes")
def listar_ordenes(db: Session = Depends(get_db)):
    """Ordenes activas y recientes."""
    ordenes = db.query(Orden).order_by(Orden.created_at.desc()).limit(50).all()
    resultado = []
    for o in ordenes:
        proveedor = db.query(Proveedor).filter(Proveedor.id == o.proveedor_id).first()
        usuario = db.query(Usuario).filter(Usuario.id == o.usuario_id).first()
        resultado.append({
            "id": o.id,
            "pedido_id": o.pedido_id,
            "proveedor": proveedor.nombre if proveedor else "?",
            "proveedor_id": o.proveedor_id,
            "usuario": usuario.nombre if usuario else "?",
            "telefono": usuario.telefono if usuario else "",
            "status": o.status,
            "total": o.total,
            "direccion_entrega": o.direccion_entrega,
            "nombre_chofer": o.nombre_chofer,
            "placas_vehiculo": o.placas_vehiculo,
            "confirmada_at": o.confirmada_at.isoformat() if o.confirmada_at else None,
            "preparando_at": o.preparando_at.isoformat() if o.preparando_at else None,
            "en_transito_at": o.en_transito_at.isoformat() if o.en_transito_at else None,
            "en_obra_at": o.en_obra_at.isoformat() if o.en_obra_at else None,
            "entregada_at": o.entregada_at.isoformat() if o.entregada_at else None,
            "tiempo_entrega_minutos": o.tiempo_entrega_minutos,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })
    return resultado


@router.post("/api/ordenes/{orden_id}/avanzar")
def avanzar_orden(orden_id: int, body: AvanzarOrdenBody, db: Session = Depends(get_db)):
    """Avanza el status de una orden (admin mueve el status como si fuera el proveedor)."""
    datos_transporte = None
    if body.nombre_chofer or body.placas_vehiculo:
        datos_transporte = {
            "nombre_chofer": body.nombre_chofer,
            "telefono_chofer": body.telefono_chofer,
            "placas_vehiculo": body.placas_vehiculo,
            "tipo_vehiculo": body.tipo_vehiculo,
        }

    try:
        orden = avanzar_status(db, orden_id, body.status, origen="admin", nota=body.nota, datos_transporte=datos_transporte)
    except ValueError as e:
        return {"error": str(e)}

    # Enviar notificacion WhatsApp
    try:
        enviar_notificacion_por_status(db, orden)
    except Exception as e:
        pass  # No fallar si WhatsApp no esta configurado

    return {"ok": True, "orden_id": orden.id, "status": orden.status}


@router.get("/api/ordenes/{orden_id}/timeline")
def ver_timeline(orden_id: int, db: Session = Depends(get_db)):
    """Timeline completo de una orden."""
    return obtener_timeline(db, orden_id)


# --- INCIDENCIAS API ---

@router.get("/api/incidencias")
def listar_incidencias(db: Session = Depends(get_db)):
    """Todas las incidencias, mas recientes primero."""
    incidencias = db.query(IncidenciaEntrega).order_by(IncidenciaEntrega.created_at.desc()).limit(50).all()
    resultado = []
    for inc in incidencias:
        proveedor = db.query(Proveedor).filter(Proveedor.id == inc.proveedor_id).first()
        resultado.append({
            "id": inc.id,
            "orden_id": inc.orden_id,
            "proveedor": proveedor.nombre if proveedor else "?",
            "tipo": inc.tipo,
            "severidad": inc.severidad,
            "descripcion_usuario": inc.descripcion_usuario,
            "cantidad_esperada": inc.cantidad_esperada,
            "cantidad_recibida": inc.cantidad_recibida,
            "unidad": inc.unidad,
            "status": inc.status,
            "resolucion": inc.resolucion,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
        })
    return resultado


@router.post("/api/incidencias/{incidencia_id}/resolver")
def resolver_inc(incidencia_id: int, body: ResolverIncidenciaBody, db: Session = Depends(get_db)):
    """Resuelve una incidencia."""
    try:
        inc = resolver_incidencia(db, incidencia_id, body.resolucion)
        return {"ok": True, "id": inc.id, "status": inc.status}
    except ValueError as e:
        return {"error": str(e)}


# --- METRICAS PROVEEDORES API ---

@router.get("/api/metricas/ranking")
def ranking_proveedores(db: Session = Depends(get_db)):
    """Ranking de proveedores por calificacion."""
    proveedores = db.query(Proveedor).filter(Proveedor.activo == True).order_by(Proveedor.calificacion.desc()).all()
    return [{
        "id": p.id,
        "nombre": p.nombre,
        "calificacion": p.calificacion,
        "tasa_puntualidad": p.tasa_puntualidad,
        "tasa_cantidad_correcta": p.tasa_cantidad_correcta,
        "tasa_especificacion_correcta": p.tasa_especificacion_correcta,
        "total_ordenes_completadas": p.total_ordenes_completadas,
        "total_incidencias": p.total_incidencias,
        "total_pedidos": p.total_pedidos,
        "pedidos_cumplidos": p.pedidos_cumplidos,
    } for p in proveedores]


@router.get("/api/proveedores/{proveedor_id}/metricas")
def metricas_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    """Metricas detalladas de un proveedor."""
    prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not prov:
        return {"error": "Proveedor no encontrado"}

    # Ultimas calificaciones
    calificaciones = db.query(CalificacionProveedor).filter(
        CalificacionProveedor.proveedor_id == proveedor_id,
    ).order_by(CalificacionProveedor.created_at.desc()).limit(20).all()

    # Incidencias abiertas
    incidencias = db.query(IncidenciaEntrega).filter(
        IncidenciaEntrega.proveedor_id == proveedor_id,
        IncidenciaEntrega.status == "abierta",
    ).all()

    return {
        "proveedor": {
            "id": prov.id,
            "nombre": prov.nombre,
            "calificacion": prov.calificacion,
            "tasa_puntualidad": prov.tasa_puntualidad,
            "tasa_cantidad_correcta": prov.tasa_cantidad_correcta,
            "tasa_especificacion_correcta": prov.tasa_especificacion_correcta,
            "total_ordenes_completadas": prov.total_ordenes_completadas,
            "total_incidencias": prov.total_incidencias,
        },
        "calificaciones_recientes": [{
            "orden_id": c.orden_id,
            "puntualidad": c.puntualidad,
            "cantidad_correcta": c.cantidad_correcta,
            "especificacion_correcta": c.especificacion_correcta,
            "calificacion_total": c.calificacion_total,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        } for c in calificaciones],
        "incidencias_abiertas": [{
            "id": inc.id,
            "orden_id": inc.orden_id,
            "tipo": inc.tipo,
            "severidad": inc.severidad,
            "descripcion_usuario": inc.descripcion_usuario,
        } for inc in incidencias],
    }


# --- WHATSAPP TEMPLATES ---

@router.post("/api/whatsapp/crear-template")
async def crear_template_whatsapp():
    """Crea la plantilla 'solicitud_cotizacion' en Meta WhatsApp Business."""
    import httpx
    from app.config import settings

    # Necesitamos el WABA ID (WhatsApp Business Account ID)
    # Primero obtenerlo desde el phone number
    url_phone = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_ID}"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        # Get WABA ID from phone number
        r = await client.get(url_phone, headers=headers, params={"fields": "whatsapp_business_account"})
        phone_data = r.json()

        if "error" in phone_data:
            return {"error": "No se pudo obtener WABA ID", "detail": phone_data}

        waba_id = phone_data.get("whatsapp_business_account", {}).get("id") if isinstance(phone_data.get("whatsapp_business_account"), dict) else phone_data.get("id")
        if not waba_id:
            return {"error": "WABA ID no encontrado", "detail": phone_data}

        # Crear template
        url_template = f"https://graph.facebook.com/v21.0/{waba_id}/message_templates"
        template_data = {
            "name": "solicitud_cotizacion",
            "language": "es_MX",
            "category": "UTILITY",
            "components": [
                {
                    "type": "BODY",
                    "text": "Hola, buen dia. Soy Nico de ObraYa.\n\nTengo un cliente que necesita:\n{{1}}\n\nMe podrias pasar tu mejor precio con flete incluido? Si puedes indicar tiempo de entrega, mejor.\n\nGracias!",
                    "example": {
                        "body_text": [["10 toneladas de cemento gris, 200 blocks de 15cm"]]
                    },
                }
            ],
        }

        r2 = await client.post(
            url_template,
            json=template_data,
            headers={**headers, "Content-Type": "application/json"},
        )
        result = r2.json()
        return {"waba_id": waba_id, "template_result": result}


@router.get("/api/whatsapp/templates")
async def listar_templates():
    """Lista las plantillas de WhatsApp existentes."""
    import httpx
    from app.config import settings

    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        # Try to get WABA ID from phone number with different field names
        waba_id = None

        # Method 1: Try debug_info which sometimes has it
        for fields in ["", "verified_name,display_phone_number", "name"]:
            url = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_ID}"
            params = {"fields": fields} if fields else {}
            r = await client.get(url, headers=headers, params=params)
            phone_data = r.json()

            # Check if we can find WABA ID in response
            if "error" not in phone_data:
                break

        # Method 2: Try the app-scoped endpoint to list WABAs
        r_me = await client.get("https://graph.facebook.com/v21.0/me/whatsapp_business_accounts", headers=headers)
        me_data = r_me.json()

        if "data" in me_data and me_data["data"]:
            waba_id = me_data["data"][0]["id"]
        elif "error" not in phone_data:
            # Use phone_id as potential WABA ID or return debug info
            return {"debug_phone": phone_data, "debug_me": me_data, "phone_id": settings.WHATSAPP_PHONE_ID}
        else:
            return {"error": "No se pudo obtener WABA ID", "debug_phone": phone_data, "debug_me": me_data}

        url_templates = f"https://graph.facebook.com/v21.0/{waba_id}/message_templates"
        r2 = await client.get(url_templates, headers=headers)
        return {"waba_id": waba_id, "templates": r2.json()}


@router.post("/api/whatsapp/test-template")
async def test_template(
    telefono: str = "5213333859426",
    template_name: str = "solicitud_cotizacion",
    materiales: str = "10 toneladas de cemento gris, 200 blocks de 15cm",
):
    """Prueba enviar un mensaje con template a un numero."""
    from app.services.whatsapp import enviar_mensaje_template
    resultado = await enviar_mensaje_template(telefono, template_name, [materiales])
    return {"telefono": telefono, "template": template_name, "resultado": resultado}


# --- ANALYTICS DE PRECIOS ---

@router.get("/api/analytics/mercado")
def analytics_mercado(db: Session = Depends(get_db)):
    """Resumen general del mercado de precios."""
    from app.services.precio_historico_service import resumen_mercado
    return resumen_mercado(db)


@router.get("/api/analytics/tendencia/{catalogo_id}")
def analytics_tendencia(catalogo_id: int, meses: int = 6, db: Session = Depends(get_db)):
    """Tendencia de precio mensual de un producto."""
    from app.services.precio_historico_service import obtener_tendencia_precio
    return obtener_tendencia_precio(db, catalogo_id=catalogo_id, meses=meses)


@router.get("/api/analytics/precio/{catalogo_id}")
def analytics_precio_actual(catalogo_id: int, db: Session = Depends(get_db)):
    """Precio actual de mercado de un producto."""
    from app.services.precio_historico_service import obtener_precio_actual
    return obtener_precio_actual(db, catalogo_id=catalogo_id)


@router.get("/api/analytics/ranking/{catalogo_id}")
def analytics_ranking_proveedores(catalogo_id: int, db: Session = Depends(get_db)):
    """Ranking de proveedores por precio para un producto."""
    from app.services.precio_historico_service import ranking_proveedores_por_producto
    return ranking_proveedores_por_producto(db, catalogo_id=catalogo_id)


@router.get("/api/analytics/variacion/{catalogo_id}")
def analytics_variacion(catalogo_id: int, db: Session = Depends(get_db)):
    """Variacion porcentual mensual de un producto."""
    from app.services.precio_historico_service import variacion_precio_mensual
    return variacion_precio_mensual(db, catalogo_id=catalogo_id)


@router.get("/api/analytics/precios_historicos")
def listar_precios_historicos(limit: int = 50, db: Session = Depends(get_db)):
    """Ultimos precios registrados en la base de datos maestra."""
    from app.models.precio_historico import PrecioHistorico
    precios = db.query(PrecioHistorico).order_by(
        PrecioHistorico.fecha.desc()
    ).limit(limit).all()
    return [{
        "id": p.id,
        "producto": p.producto_normalizado or p.producto_nombre,
        "categoria": p.categoria,
        "proveedor": p.proveedor_nombre,
        "precio_unitario": p.precio_unitario,
        "unidad": p.unidad,
        "precio_efectivo": p.precio_efectivo,
        "incluye_flete": p.incluye_flete,
        "zona": p.zona,
        "es_outlier": p.es_outlier,
        "fecha": p.fecha.isoformat() if p.fecha else None,
    } for p in precios]


@router.get("/", response_class=HTMLResponse)
def panel_admin():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ObraYa - Panel Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; }
        .tab-active { border-bottom: 3px solid #ea580c; color: #ea580c; font-weight: 700; }
        .toast { animation: slideIn 0.3s ease-out, fadeOut 0.5s ease-in 2.5s forwards; }
        @keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @keyframes fadeOut { to { opacity: 0; } }
        input:focus { outline: 2px solid #ea580c; outline-offset: -2px; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">

    <!-- Header -->
    <nav class="bg-orange-600 text-white p-4 shadow-lg">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <div class="flex items-center gap-3">
                <a href="/" class="text-2xl font-bold hover:text-orange-200">ObraYa</a>
                <span class="bg-orange-700 px-2 py-0.5 rounded text-xs">Admin</span>
            </div>
            <div class="flex gap-4 text-sm">
                <a href="/" class="hover:text-orange-200">Inicio</a>
                <a href="/sim/" class="hover:text-orange-200">Chat Demo</a>
                <a href="/docs" class="hover:text-orange-200">API Docs</a>
            </div>
        </div>
    </nav>

    <!-- Toast container -->
    <div id="toasts" class="fixed top-4 right-4 z-50 space-y-2"></div>

    <div class="max-w-7xl mx-auto p-6">

        <!-- Stats Cards -->
        <div id="stats-cards" class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <!-- Se llenan con JS -->
        </div>

        <!-- Tabs -->
        <div class="flex border-b mb-6 gap-1">
            <button onclick="showTab('proveedores')" id="tab-proveedores" class="px-4 py-3 text-sm hover:text-orange-600 tab-active">Proveedores</button>
            <button onclick="showTab('precios')" id="tab-precios" class="px-4 py-3 text-sm hover:text-orange-600">Precios</button>
            <button onclick="showTab('pedidos')" id="tab-pedidos" class="px-4 py-3 text-sm hover:text-orange-600">Pedidos</button>
        </div>

        <!-- Tab: Proveedores -->
        <div id="panel-proveedores">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold text-gray-800">Proveedores</h2>
                <button onclick="mostrarFormProveedor()" class="bg-orange-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-orange-700">+ Agregar Proveedor</button>
            </div>

            <!-- Form nuevo proveedor (oculto) -->
            <div id="form-proveedor" class="hidden bg-orange-50 border border-orange-200 rounded-xl p-4 mb-4">
                <h3 class="font-bold text-orange-800 mb-3">Nuevo Proveedor</h3>
                <div class="grid md:grid-cols-3 gap-3">
                    <input id="np-nombre" placeholder="Nombre del proveedor" class="border rounded-lg px-3 py-2 text-sm">
                    <select id="np-tipo" class="border rounded-lg px-3 py-2 text-sm">
                        <option value="pequeno">Pequeno</option>
                        <option value="mediano">Mediano</option>
                        <option value="grande">Grande</option>
                    </select>
                    <input id="np-municipio" placeholder="Municipio (ej: Zapopan)" class="border rounded-lg px-3 py-2 text-sm">
                    <input id="np-telefono" placeholder="WhatsApp (+52...)" class="border rounded-lg px-3 py-2 text-sm">
                    <select id="np-contacto" class="border rounded-lg px-3 py-2 text-sm">
                        <option value="whatsapp">WhatsApp</option>
                        <option value="telefono">Telefono</option>
                        <option value="email">Email</option>
                        <option value="api">API</option>
                    </select>
                    <div class="flex gap-2">
                        <button onclick="guardarProveedor()" class="bg-orange-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-orange-700 flex-1">Guardar</button>
                        <button onclick="document.getElementById('form-proveedor').classList.add('hidden')" class="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm hover:bg-gray-400">Cancelar</button>
                    </div>
                </div>
            </div>

            <div id="tabla-proveedores" class="bg-white rounded-xl shadow overflow-x-auto">
                <!-- Se llena con JS -->
            </div>
        </div>

        <!-- Tab: Precios -->
        <div id="panel-precios" class="hidden">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold text-gray-800">Catalogo de Precios</h2>
                <div class="flex gap-2">
                    <select id="filtro-categoria" onchange="filtrarPrecios()" class="border rounded-lg px-3 py-2 text-sm">
                        <option value="">Todas las categorias</option>
                        <option value="concreto">Concreto</option>
                        <option value="acero">Acero</option>
                        <option value="agregados">Agregados</option>
                        <option value="cementantes">Cementantes</option>
                        <option value="block">Block</option>
                        <option value="tuberia">Tuberia</option>
                        <option value="impermeabilizante">Impermeabilizante</option>
                        <option value="electrico">Electrico</option>
                    </select>
                    <input id="filtro-buscar" oninput="filtrarPrecios()" placeholder="Buscar producto..." class="border rounded-lg px-3 py-2 text-sm w-48">
                </div>
            </div>
            <div id="tabla-precios" class="bg-white rounded-xl shadow overflow-x-auto">
                <!-- Se llena con JS -->
            </div>
            <p class="text-gray-400 text-xs mt-2">Haz clic en cualquier precio para editarlo</p>
        </div>

        <!-- Tab: Pedidos -->
        <div id="panel-pedidos" class="hidden">
            <h2 class="text-xl font-bold text-gray-800 mb-4">Pedidos Recientes</h2>
            <div id="tabla-pedidos" class="bg-white rounded-xl shadow overflow-x-auto">
                <!-- Se llena con JS -->
            </div>
        </div>
    </div>

    <footer class="text-center text-gray-400 text-sm py-8">
        ObraYa &copy; 2026 — Panel de administracion
    </footer>

    <script>
        let proveedoresData = [];
        let pedidosData = [];
        let statsData = {};

        // --- CARGA INICIAL ---
        async function cargarTodo() {
            const [stats, proveedores, pedidos] = await Promise.all([
                fetch('/admin/api/stats').then(r => r.json()),
                fetch('/admin/api/proveedores').then(r => r.json()),
                fetch('/admin/api/pedidos').then(r => r.json()),
            ]);
            statsData = stats;
            proveedoresData = proveedores;
            pedidosData = pedidos;
            renderStats();
            renderProveedores();
            renderPrecios();
            renderPedidos();
        }

        // --- STATS ---
        function renderStats() {
            const s = statsData;
            document.getElementById('stats-cards').innerHTML = `
                <div class="bg-white rounded-xl shadow p-4 text-center">
                    <div class="text-3xl font-bold text-orange-600">${s.total_proveedores}</div>
                    <div class="text-gray-500 text-sm">Proveedores</div>
                </div>
                <div class="bg-white rounded-xl shadow p-4 text-center">
                    <div class="text-3xl font-bold text-blue-600">${s.total_productos}</div>
                    <div class="text-gray-500 text-sm">Productos</div>
                </div>
                <div class="bg-white rounded-xl shadow p-4 text-center">
                    <div class="text-3xl font-bold text-green-600">${s.total_pedidos}</div>
                    <div class="text-gray-500 text-sm">Pedidos</div>
                </div>
                <div class="bg-white rounded-xl shadow p-4 text-center">
                    <div class="text-3xl font-bold text-purple-600">${s.total_usuarios}</div>
                    <div class="text-gray-500 text-sm">Usuarios</div>
                </div>
                <div class="bg-white rounded-xl shadow p-4 text-center">
                    <div class="text-3xl font-bold text-red-600">${s.total_cotizaciones}</div>
                    <div class="text-gray-500 text-sm">Cotizaciones</div>
                </div>
            `;
        }

        // --- PROVEEDORES ---
        function renderProveedores() {
            const rows = proveedoresData.map(p => {
                const tipoBadge = p.tipo === 'grande' ? 'bg-green-100 text-green-800'
                    : p.tipo === 'mediano' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800';
                return `<tr class="border-t hover:bg-gray-50">
                    <td class="p-3 font-medium">${p.nombre}</td>
                    <td class="p-3"><span class="px-2 py-1 rounded text-xs ${tipoBadge}">${p.tipo}</span></td>
                    <td class="p-3">${p.municipio}</td>
                    <td class="p-3 text-sm">${p.categorias.join(', ')}</td>
                    <td class="p-3 text-center">${p.productos.length}</td>
                    <td class="p-3 text-center">${p.calificacion}</td>
                    <td class="p-3 text-center">
                        <button onclick="eliminarProveedor(${p.id}, '${p.nombre}')" class="text-red-400 hover:text-red-600 text-xs">Eliminar</button>
                    </td>
                </tr>`;
            }).join('');

            document.getElementById('tabla-proveedores').innerHTML = `
                <table class="w-full text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="p-3 text-left">Nombre</th>
                            <th class="p-3 text-left">Tipo</th>
                            <th class="p-3 text-left">Municipio</th>
                            <th class="p-3 text-left">Categorias</th>
                            <th class="p-3 text-center">Productos</th>
                            <th class="p-3 text-center">Calificacion</th>
                            <th class="p-3 text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        }

        // --- PRECIOS (con edicion inline) ---
        function renderPrecios(filtroCategoria = '', filtroBuscar = '') {
            let filas = [];
            proveedoresData.forEach(p => {
                p.productos.forEach(prod => {
                    if (filtroCategoria && prod.categoria !== filtroCategoria) return;
                    if (filtroBuscar && !prod.nombre.toLowerCase().includes(filtroBuscar.toLowerCase())) return;
                    filas.push({...prod, proveedor_id: p.id, proveedor_nombre: p.nombre, proveedor_tipo: p.tipo});
                });
            });

            // Ordenar por categoria y nombre
            filas.sort((a, b) => a.categoria.localeCompare(b.categoria) || a.nombre.localeCompare(b.nombre));

            const catColors = {
                concreto: 'bg-orange-100 text-orange-700',
                acero: 'bg-blue-100 text-blue-700',
                agregados: 'bg-yellow-100 text-yellow-700',
                cementantes: 'bg-gray-100 text-gray-700',
                block: 'bg-red-100 text-red-700',
                tuberia: 'bg-green-100 text-green-700',
                impermeabilizante: 'bg-purple-100 text-purple-700',
                electrico: 'bg-indigo-100 text-indigo-700',
            };

            const rows = filas.map(f => `
                <tr class="border-t hover:bg-gray-50">
                    <td class="p-3 font-medium">${f.nombre}</td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded text-xs ${catColors[f.categoria] || 'bg-gray-100'}">${f.categoria}</span></td>
                    <td class="p-3">${f.proveedor_nombre}</td>
                    <td class="p-3 text-right">
                        <span id="precio-${f.proveedor_id}-${f.id}"
                              class="font-mono cursor-pointer hover:bg-orange-50 px-2 py-1 rounded"
                              onclick="editarPrecio(${f.proveedor_id}, ${f.id}, ${f.precio_unitario})"
                              title="Clic para editar">$${f.precio_unitario.toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
                    </td>
                    <td class="p-3">${f.unidad}</td>
                    <td class="p-3"><span class="text-xs ${f.disponibilidad === 'inmediata' ? 'text-green-600' : 'text-yellow-600'}">${f.disponibilidad}</span></td>
                </tr>
            `).join('');

            document.getElementById('tabla-precios').innerHTML = `
                <table class="w-full text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="p-3 text-left">Producto</th>
                            <th class="p-3 text-left">Categoria</th>
                            <th class="p-3 text-left">Proveedor</th>
                            <th class="p-3 text-right">Precio</th>
                            <th class="p-3 text-left">Unidad</th>
                            <th class="p-3 text-left">Disponibilidad</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
                <div class="p-3 text-gray-400 text-xs text-right">${filas.length} productos</div>
            `;
        }

        function filtrarPrecios() {
            const cat = document.getElementById('filtro-categoria').value;
            const buscar = document.getElementById('filtro-buscar').value;
            renderPrecios(cat, buscar);
        }

        function editarPrecio(proveedorId, productoId, precioActual) {
            const span = document.getElementById(`precio-${proveedorId}-${productoId}`);
            const input = document.createElement('input');
            input.type = 'number';
            input.step = '0.01';
            input.value = precioActual;
            input.className = 'border border-orange-400 rounded px-2 py-1 w-28 text-right text-sm font-mono';

            input.onblur = () => guardarPrecio(proveedorId, productoId, input.value);
            input.onkeydown = (e) => {
                if (e.key === 'Enter') guardarPrecio(proveedorId, productoId, input.value);
                if (e.key === 'Escape') cargarTodo();
            };

            span.replaceWith(input);
            input.focus();
            input.select();
        }

        async function guardarPrecio(proveedorId, productoId, nuevoPrecio) {
            const precio = parseFloat(nuevoPrecio);
            if (isNaN(precio) || precio <= 0) {
                toast('Precio invalido', 'error');
                cargarTodo();
                return;
            }
            const res = await fetch(`/admin/api/proveedores/${proveedorId}/productos/${productoId}/precio`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({nuevo_precio: precio}),
            });
            const data = await res.json();
            if (data.ok) {
                toast(`Precio de ${data.producto} actualizado a $${precio.toLocaleString()}`, 'success');
            } else {
                toast('Error al guardar', 'error');
            }
            cargarTodo();
        }

        // --- PEDIDOS ---
        function renderPedidos() {
            if (!pedidosData.length) {
                document.getElementById('tabla-pedidos').innerHTML = `
                    <div class="p-12 text-center text-gray-400">
                        <div class="text-4xl mb-3">--</div>
                        <p>No hay pedidos todavia</p>
                        <p class="text-sm mt-1">Los pedidos apareceran aqui cuando lleguen por WhatsApp o el simulador</p>
                        <a href="/sim/" class="text-orange-600 hover:underline text-sm mt-2 inline-block">Probar el simulador →</a>
                    </div>
                `;
                return;
            }

            const statusColors = {
                interpretando: 'bg-yellow-100 text-yellow-800',
                cotizando: 'bg-blue-100 text-blue-800',
                comparando: 'bg-purple-100 text-purple-800',
                enviado: 'bg-green-100 text-green-800',
                aceptado: 'bg-green-200 text-green-900',
                entregado: 'bg-gray-100 text-gray-800',
                cancelado: 'bg-red-100 text-red-800',
            };

            const rows = pedidosData.map(p => `
                <tr class="border-t hover:bg-gray-50">
                    <td class="p-3 font-mono text-gray-500">#${p.id}</td>
                    <td class="p-3 font-medium">${p.usuario}</td>
                    <td class="p-3 text-sm text-gray-500">${p.telefono}</td>
                    <td class="p-3 max-w-xs truncate text-sm">${(p.mensaje_original || '').substring(0, 80)}</td>
                    <td class="p-3"><span class="px-2 py-1 rounded text-xs ${statusColors[p.status] || 'bg-gray-100'}">${p.status}</span></td>
                    <td class="p-3 text-center">${p.cotizaciones}</td>
                    <td class="p-3 text-sm text-gray-400">${p.created_at ? p.created_at.substring(0, 16).replace('T', ' ') : ''}</td>
                </tr>
            `).join('');

            document.getElementById('tabla-pedidos').innerHTML = `
                <table class="w-full text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="p-3 text-left">ID</th>
                            <th class="p-3 text-left">Usuario</th>
                            <th class="p-3 text-left">Telefono</th>
                            <th class="p-3 text-left">Mensaje</th>
                            <th class="p-3 text-left">Status</th>
                            <th class="p-3 text-center">Cotizaciones</th>
                            <th class="p-3 text-left">Fecha</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        }

        // --- TABS ---
        function showTab(tab) {
            ['proveedores', 'precios', 'pedidos'].forEach(t => {
                document.getElementById(`panel-${t}`).classList.toggle('hidden', t !== tab);
                document.getElementById(`tab-${t}`).classList.toggle('tab-active', t === tab);
            });
        }

        // --- PROVEEDOR CRUD ---
        function mostrarFormProveedor() {
            document.getElementById('form-proveedor').classList.toggle('hidden');
        }

        async function guardarProveedor() {
            const data = {
                nombre: document.getElementById('np-nombre').value,
                tipo: document.getElementById('np-tipo').value,
                municipio: document.getElementById('np-municipio').value,
                telefono_whatsapp: document.getElementById('np-telefono').value,
                metodo_contacto: document.getElementById('np-contacto').value,
                categorias: [],
            };
            if (!data.nombre) { toast('Falta el nombre', 'error'); return; }
            const res = await fetch('/admin/api/proveedores', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data),
            });
            const result = await res.json();
            if (result.ok) {
                toast(`Proveedor ${result.nombre} creado`, 'success');
                document.getElementById('form-proveedor').classList.add('hidden');
                cargarTodo();
            }
        }

        async function eliminarProveedor(id, nombre) {
            if (!confirm(`Eliminar a ${nombre}?`)) return;
            const res = await fetch(`/admin/api/proveedores/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.ok) {
                toast(`${nombre} eliminado`, 'success');
                cargarTodo();
            }
        }

        // --- TOAST ---
        function toast(msg, type = 'info') {
            const colors = { success: 'bg-green-500', error: 'bg-red-500', info: 'bg-blue-500' };
            const div = document.createElement('div');
            div.className = `toast ${colors[type]} text-white px-4 py-2 rounded-lg shadow-lg text-sm`;
            div.textContent = msg;
            document.getElementById('toasts').appendChild(div);
            setTimeout(() => div.remove(), 3000);
        }

        // Cargar al iniciar
        cargarTodo();
    </script>

</body>
</html>
"""
