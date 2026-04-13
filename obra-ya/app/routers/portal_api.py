"""
Portal API — endpoints para el portal web completo.
Fase 1: Crear pedidos desde web (comprador)
Fase 2: Pagos con Stripe
Fase 3: Presupuestos de obra
Fase 4: Aprobaciones corporativas
Fase 5: Portal vendedor completo
Fase 6: Vinculacion WhatsApp-Web
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.services.auth_service import verificar_token
from app.models.catalogo import CatalogoMaestro
from app.models.pedido import Pedido
from app.models.cotizacion import Cotizacion
from app.models.solicitud_proveedor import SolicitudProveedor
from app.models.orden import Orden
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.models.presupuesto import PresupuestoObra, PartidaPresupuesto
from app.models.aprobacion import Aprobacion
from app.models.empresa import Empresa
from app.models.miembro_empresa import MiembroEmpresa
from app.services.cotizador import generar_cotizaciones, guardar_cotizaciones
from app.services.cotizacion_activa import enviar_solicitudes_a_proveedores
from app.services.orden_service import crear_orden
from app.services.pagos import crear_sesion_pago, calcular_desglose

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portal", tags=["portal-api"])


# ─── Auth helper ──────────────────────────────────────────────────────

def _get_user_id(authorization: str, db: Session) -> int | None:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    payload = verificar_token(token)
    if not payload:
        return None
    return int(payload.get("sub", 0))


# ─── Pydantic schemas ─────────────────────────────────────────────────

class PedidoWebBody(BaseModel):
    usuario_id: int
    items: list[dict]  # [{catalogo_id, nombre, categoria, cantidad, unidad}]
    direccion_entrega: str
    municipio_entrega: str = ""
    fecha_entrega: str = ""


class ElegirProveedorBody(BaseModel):
    cotizacion_id: int
    usuario_id: int


class ProductoBody(BaseModel):
    catalogo_id: int | None = None
    nombre: str
    categoria: str
    unidad: str
    precio_unitario: float
    disponibilidad: str = "inmediata"
    precio_incluye_flete: bool = False


class ProductoUpdateBody(BaseModel):
    precio_unitario: float | None = None
    disponibilidad: str | None = None
    activo: bool | None = None
    precio_incluye_flete: bool | None = None


class ResponderSolicitudBody(BaseModel):
    precio_total: float
    tiempo_entrega: str = "24h"
    incluye_flete: bool = False
    costo_flete: float = 0
    notas: str = ""
    items: list[dict] = []  # [{producto, precio_unitario, cantidad}]


class PerfilProveedorBody(BaseModel):
    nombre: str | None = None
    telefono_whatsapp: str | None = None
    email: str | None = None
    direccion: str | None = None
    municipio: str | None = None
    categorias: list[str] | None = None
    horario_atencion: str | None = None


class PresupuestoBody(BaseModel):
    usuario_id: int
    nombre_obra: str
    direccion: str = ""
    fecha_inicio: str = ""
    fecha_fin_estimada: str = ""
    presupuesto_total: float = 0
    partidas: list[dict] = []  # [{nombre_material, categoria, unidad, cantidad, precio_unitario}]


class PartidaBody(BaseModel):
    nombre_material: str
    categoria: str = ""
    unidad: str = ""
    cantidad_presupuestada: float = 0
    precio_unitario_estimado: float = 0


class ConsumoBody(BaseModel):
    cantidad: float
    monto: float = 0


class VincularTelefonoBody(BaseModel):
    usuario_id: int
    telefono: str
    codigo_pais: str = "+52"


# ═══════════════════════════════════════════════════════════════════════
# FASE 1: CREAR PEDIDOS DESDE WEB (COMPRADOR)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/api/catalogo")
def get_catalogo(q: str = "", categoria: str = "", db: Session = Depends(get_db)):
    """Buscar productos en el catalogo maestro."""
    query = db.query(CatalogoMaestro).filter(CatalogoMaestro.activo == True)
    if categoria:
        query = query.filter(CatalogoMaestro.categoria == categoria)
    if q:
        query = query.filter(CatalogoMaestro.nombre.ilike(f"%{q}%"))
    items = query.order_by(CatalogoMaestro.categoria, CatalogoMaestro.nombre).all()
    return [
        {
            "id": i.id,
            "nombre": i.nombre,
            "categoria": i.categoria,
            "unidad": i.unidad,
            "descripcion": i.descripcion,
            "precio_referencia": i.precio_referencia,
        }
        for i in items
    ]


@router.get("/api/catalogo/categorias")
def get_categorias(db: Session = Depends(get_db)):
    """Lista de categorias disponibles."""
    cats = db.query(CatalogoMaestro.categoria).filter(
        CatalogoMaestro.activo == True
    ).distinct().all()
    return [c[0] for c in cats]


@router.post("/api/pedido")
async def crear_pedido_web(body: PedidoWebBody, db: Session = Depends(get_db)):
    """Crear pedido desde el portal web — contacta proveedores por WhatsApp + genera cotizaciones de la BD."""
    # Construir pedido_data en el formato que espera cotizador.py
    pedido_data = {
        "pedido": {
            "items": [
                {
                    "producto": item.get("nombre", ""),
                    "categoria": item.get("categoria", ""),
                    "cantidad": item.get("cantidad", 1),
                    "unidad": item.get("unidad", "pieza"),
                }
                for item in body.items
            ],
            "entrega": {
                "direccion": body.direccion_entrega,
                "fecha": body.fecha_entrega,
            },
        }
    }

    # Crear registro Pedido
    pedido = Pedido(
        usuario_id=body.usuario_id,
        status="cotizando",
        mensaje_original=f"[Portal Web] {len(body.items)} materiales",
        pedido_interpretado=json.dumps(pedido_data, ensure_ascii=False),
        direccion_entrega=body.direccion_entrega,
        municipio_entrega=body.municipio_entrega,
    )
    if body.fecha_entrega:
        try:
            pedido.fecha_entrega = datetime.strptime(body.fecha_entrega, "%Y-%m-%d").date()
        except ValueError:
            pass
    db.add(pedido)
    db.flush()

    # 1) Contactar proveedores reales por WhatsApp
    solicitudes_enviadas = 0
    try:
        solicitudes = await enviar_solicitudes_a_proveedores(db, pedido.id, pedido_data)
        solicitudes_enviadas = len(solicitudes) if solicitudes else 0
        logger.info(f"Pedido #{pedido.id}: {solicitudes_enviadas} proveedores contactados por WhatsApp")
    except Exception as e:
        logger.error(f"Pedido #{pedido.id}: Error contactando proveedores: {e}")

    # 2) Generar cotizaciones de referencia desde la BD (instantaneo)
    cotizaciones = generar_cotizaciones(db, pedido_data)
    cot_ids = []
    if cotizaciones:
        cot_ids = guardar_cotizaciones(db, pedido.id, cotizaciones)

    # Status depends on what happened
    if solicitudes_enviadas > 0:
        pedido.status = "cotizando"  # Waiting for real WhatsApp responses
    elif cot_ids:
        pedido.status = "enviado"  # Only static quotes available
    db.commit()

    return {
        "ok": True,
        "pedido_id": pedido.id,
        "cotizaciones_count": len(cot_ids),
        "proveedores_contactados": solicitudes_enviadas,
        "status": pedido.status,
    }


@router.get("/api/pedido/{pedido_id}/status")
def get_pedido_status(pedido_id: int, db: Session = Depends(get_db)):
    """Estado del pedido: proveedores contactados y respuestas."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return {"ok": False, "error": "Pedido no encontrado"}

    solicitudes = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.pedido_id == pedido_id
    ).all()
    respondidas = [s for s in solicitudes if s.status == "respondida"]
    cotizaciones = db.query(Cotizacion).filter(Cotizacion.pedido_id == pedido_id).count()

    return {
        "ok": True,
        "pedido_id": pedido_id,
        "status": pedido.status,
        "proveedores_contactados": len(solicitudes),
        "proveedores_respondidos": len(respondidas),
        "cotizaciones_disponibles": cotizaciones,
    }


@router.get("/api/pedido/{pedido_id}/cotizaciones")
def get_cotizaciones(pedido_id: int, db: Session = Depends(get_db)):
    """Comparativa de cotizaciones para un pedido."""
    cotizaciones = db.query(Cotizacion).filter(
        Cotizacion.pedido_id == pedido_id,
        Cotizacion.total > 0,
    ).order_by(Cotizacion.total.asc()).all()

    result = []
    for c in cotizaciones:
        prov = db.query(Proveedor).filter(Proveedor.id == c.proveedor_id).first()
        items = []
        try:
            items = json.loads(c.items) if c.items else []
        except (json.JSONDecodeError, TypeError):
            pass
        result.append({
            "cotizacion_id": c.id,
            "proveedor_id": c.proveedor_id,
            "proveedor_nombre": prov.nombre if prov else "Desconocido",
            "proveedor_calificacion": prov.calificacion if prov else 0,
            "proveedor_municipio": prov.municipio if prov else "",
            "items": items,
            "subtotal": c.subtotal,
            "costo_flete": c.costo_flete,
            "total": c.total,
            "tiempo_entrega": c.tiempo_entrega,
        })
    return result


@router.post("/api/pedido/{pedido_id}/elegir")
def elegir_proveedor(pedido_id: int, body: ElegirProveedorBody, db: Session = Depends(get_db)):
    """Seleccionar proveedor y crear orden."""
    try:
        orden = crear_orden(db, body.cotizacion_id, body.usuario_id)
        return {
            "ok": True,
            "orden_id": orden.id,
            "status": orden.status,
            "total": orden.total,
        }
    except ValueError as e:
        return {"ok": False, "error": str(e)}


@router.get("/api/mis-pedidos/{usuario_id}")
def get_mis_pedidos(usuario_id: int, db: Session = Depends(get_db)):
    """Pedidos en proceso del usuario (no ordenes aun)."""
    pedidos = db.query(Pedido).filter(
        Pedido.usuario_id == usuario_id,
        Pedido.status.in_(["interpretando", "cotizando", "enviado"]),
    ).order_by(Pedido.created_at.desc()).limit(20).all()

    result = []
    for p in pedidos:
        cot_count = db.query(Cotizacion).filter(Cotizacion.pedido_id == p.id).count()
        items_data = []
        try:
            data = json.loads(p.pedido_interpretado) if p.pedido_interpretado else {}
            items_data = data.get("pedido", {}).get("items", [])
        except (json.JSONDecodeError, TypeError):
            pass
        result.append({
            "id": p.id,
            "status": p.status,
            "items_count": len(items_data),
            "items_resumen": ", ".join(i.get("producto", "")[:30] for i in items_data[:3]),
            "direccion": p.direccion_entrega or "",
            "cotizaciones": cot_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return result


# ═══════════════════════════════════════════════════════════════════════
# FASE 2: PAGOS CON STRIPE
# ═══════════════════════════════════════════════════════════════════════

@router.post("/api/pagar/{orden_id}")
def pagar_orden(orden_id: int, db: Session = Depends(get_db)):
    """Crea sesion de pago Stripe para una orden."""
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        return {"ok": False, "error": "Orden no encontrada"}
    if orden.pagado:
        return {"ok": False, "error": "Esta orden ya fue pagada"}
    try:
        base_url = "https://web-production-60dcc.up.railway.app"
        result = crear_sesion_pago(orden_id, orden.total, base_url)
        desglose = calcular_desglose(orden.total)
        return {"ok": True, "url": result["url"], "desglose": desglose}
    except Exception as e:
        logger.error(f"Error creando sesion Stripe: {e}")
        return {"ok": False, "error": "Error al crear sesion de pago"}


# ═══════════════════════════════════════════════════════════════════════
# FASE 3: PRESUPUESTOS DE OBRA
# ═══════════════════════════════════════════════════════════════════════

@router.get("/api/presupuestos/{usuario_id}")
def get_presupuestos(usuario_id: int, db: Session = Depends(get_db)):
    """Listar presupuestos de obra del usuario."""
    presupuestos = db.query(PresupuestoObra).filter(
        PresupuestoObra.usuario_id == usuario_id,
        PresupuestoObra.activo == True,
    ).order_by(PresupuestoObra.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "nombre_obra": p.nombre_obra,
            "direccion": p.direccion,
            "presupuesto_total": p.presupuesto_total,
            "gastado_total": p.gastado_total,
            "porcentaje_consumido": p.porcentaje_consumido,
            "fecha_inicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
            "fecha_fin_estimada": p.fecha_fin_estimada.isoformat() if p.fecha_fin_estimada else None,
        }
        for p in presupuestos
    ]


@router.get("/api/presupuesto/{presupuesto_id}")
def get_presupuesto_detalle(presupuesto_id: int, db: Session = Depends(get_db)):
    """Detalle de presupuesto con partidas."""
    p = db.query(PresupuestoObra).filter(PresupuestoObra.id == presupuesto_id).first()
    if not p:
        return {"ok": False, "error": "Presupuesto no encontrado"}
    partidas = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.presupuesto_id == presupuesto_id
    ).order_by(PartidaPresupuesto.categoria, PartidaPresupuesto.nombre_material).all()
    return {
        "ok": True,
        "presupuesto": {
            "id": p.id,
            "nombre_obra": p.nombre_obra,
            "direccion": p.direccion,
            "presupuesto_total": p.presupuesto_total,
            "gastado_total": p.gastado_total,
            "porcentaje_consumido": p.porcentaje_consumido,
        },
        "partidas": [
            {
                "id": pt.id,
                "nombre_material": pt.nombre_material,
                "categoria": pt.categoria,
                "unidad": pt.unidad,
                "cantidad_presupuestada": pt.cantidad_presupuestada,
                "cantidad_consumida": pt.cantidad_consumida,
                "porcentaje_consumido": pt.porcentaje_consumido,
                "precio_unitario_estimado": pt.precio_unitario_estimado,
                "monto_presupuestado": pt.monto_presupuestado,
                "monto_gastado": pt.monto_gastado,
                "bloqueado": pt.bloqueado,
            }
            for pt in partidas
        ],
    }


@router.post("/api/presupuestos")
def crear_presupuesto(body: PresupuestoBody, db: Session = Depends(get_db)):
    """Crear presupuesto de obra nuevo."""
    total = 0
    p = PresupuestoObra(
        usuario_id=body.usuario_id,
        nombre_obra=body.nombre_obra,
        direccion=body.direccion,
        presupuesto_total=body.presupuesto_total,
    )
    if body.fecha_inicio:
        try:
            p.fecha_inicio = datetime.strptime(body.fecha_inicio, "%Y-%m-%d").date()
        except ValueError:
            pass
    if body.fecha_fin_estimada:
        try:
            p.fecha_fin_estimada = datetime.strptime(body.fecha_fin_estimada, "%Y-%m-%d").date()
        except ValueError:
            pass
    db.add(p)
    db.flush()

    for pt_data in body.partidas:
        monto = pt_data.get("cantidad", 0) * pt_data.get("precio_unitario", 0)
        total += monto
        partida = PartidaPresupuesto(
            presupuesto_id=p.id,
            nombre_material=pt_data.get("nombre_material", ""),
            categoria=pt_data.get("categoria", ""),
            unidad=pt_data.get("unidad", ""),
            cantidad_presupuestada=pt_data.get("cantidad", 0),
            precio_unitario_estimado=pt_data.get("precio_unitario", 0),
            monto_presupuestado=monto,
        )
        db.add(partida)

    if not body.presupuesto_total and total > 0:
        p.presupuesto_total = total
    db.commit()
    return {"ok": True, "presupuesto_id": p.id}


@router.post("/api/presupuesto/{presupuesto_id}/partidas")
def agregar_partida(presupuesto_id: int, body: PartidaBody, db: Session = Depends(get_db)):
    """Agregar partida a un presupuesto."""
    monto = body.cantidad_presupuestada * body.precio_unitario_estimado
    partida = PartidaPresupuesto(
        presupuesto_id=presupuesto_id,
        nombre_material=body.nombre_material,
        categoria=body.categoria,
        unidad=body.unidad,
        cantidad_presupuestada=body.cantidad_presupuestada,
        precio_unitario_estimado=body.precio_unitario_estimado,
        monto_presupuestado=monto,
    )
    db.add(partida)
    db.commit()
    return {"ok": True, "partida_id": partida.id}


@router.put("/api/presupuesto/{presupuesto_id}/partidas/{partida_id}/consumo")
def registrar_consumo(presupuesto_id: int, partida_id: int, body: ConsumoBody, db: Session = Depends(get_db)):
    """Registrar consumo en una partida."""
    partida = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.id == partida_id,
        PartidaPresupuesto.presupuesto_id == presupuesto_id,
    ).first()
    if not partida:
        return {"ok": False, "error": "Partida no encontrada"}
    if partida.bloqueado:
        return {"ok": False, "error": "Partida bloqueada - presupuesto agotado"}

    partida.cantidad_consumida = (partida.cantidad_consumida or 0) + body.cantidad
    monto = body.monto if body.monto else body.cantidad * (partida.precio_unitario_estimado or 0)
    partida.monto_gastado = (partida.monto_gastado or 0) + monto
    if partida.cantidad_presupuestada and partida.cantidad_presupuestada > 0:
        partida.porcentaje_consumido = round(
            (partida.cantidad_consumida / partida.cantidad_presupuestada) * 100, 1
        )
    if partida.porcentaje_consumido and partida.porcentaje_consumido >= 100:
        partida.bloqueado = True

    # Update parent budget
    presupuesto = db.query(PresupuestoObra).filter(PresupuestoObra.id == presupuesto_id).first()
    if presupuesto:
        presupuesto.gastado_total = (presupuesto.gastado_total or 0) + monto
        if presupuesto.presupuesto_total and presupuesto.presupuesto_total > 0:
            presupuesto.porcentaje_consumido = round(
                (presupuesto.gastado_total / presupuesto.presupuesto_total) * 100, 1
            )
    db.commit()
    return {"ok": True, "porcentaje": partida.porcentaje_consumido}


# ═══════════════════════════════════════════════════════════════════════
# FASE 4: APROBACIONES CORPORATIVAS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/api/aprobaciones/pendientes/{usuario_id}")
def get_aprobaciones_pendientes(usuario_id: int, db: Session = Depends(get_db)):
    """Aprobaciones pendientes donde este usuario es aprobador."""
    # Check if user is an approver
    miembro = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.usuario_id == usuario_id,
        MiembroEmpresa.puede_aprobar == True,
    ).first()
    if not miembro:
        return {"es_aprobador": False, "pendientes": []}

    aprobaciones = db.query(Aprobacion).filter(
        Aprobacion.empresa_id == miembro.empresa_id,
        Aprobacion.status == "pendiente",
    ).order_by(Aprobacion.solicitada_at.desc()).all()

    result = []
    for a in aprobaciones:
        orden = db.query(Orden).filter(Orden.id == a.orden_id).first()
        solicitante = db.query(Usuario).filter(Usuario.id == a.solicitante_id).first()
        items = []
        if orden and orden.items:
            try:
                items = json.loads(orden.items) if isinstance(orden.items, str) else orden.items
            except (json.JSONDecodeError, TypeError):
                pass
        result.append({
            "id": a.id,
            "orden_id": a.orden_id,
            "monto": a.monto,
            "solicitante": solicitante.nombre if solicitante else "Desconocido",
            "items": items,
            "direccion": orden.direccion_entrega if orden else "",
            "solicitada_at": a.solicitada_at.isoformat() if a.solicitada_at else None,
            "expira_at": a.expira_at.isoformat() if a.expira_at else None,
        })
    return {"es_aprobador": True, "pendientes": result}


@router.post("/api/aprobaciones/{aprobacion_id}/aprobar")
def aprobar(aprobacion_id: int, db: Session = Depends(get_db)):
    """Aprobar una solicitud de compra."""
    a = db.query(Aprobacion).filter(Aprobacion.id == aprobacion_id).first()
    if not a:
        return {"ok": False, "error": "Aprobacion no encontrada"}
    a.status = "aprobada"
    a.respondida_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.post("/api/aprobaciones/{aprobacion_id}/rechazar")
def rechazar(aprobacion_id: int, db: Session = Depends(get_db)):
    """Rechazar una solicitud de compra."""
    a = db.query(Aprobacion).filter(Aprobacion.id == aprobacion_id).first()
    if not a:
        return {"ok": False, "error": "Aprobacion no encontrada"}
    a.status = "rechazada"
    a.respondida_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════
# FASE 5: PORTAL VENDEDOR COMPLETO
# ═══════════════════════════════════════════════════════════════════════

# --- Productos del proveedor ---

@router.get("/api/proveedor/{proveedor_id}/productos")
def get_productos(proveedor_id: int, db: Session = Depends(get_db)):
    """Listar productos del proveedor."""
    productos = db.query(Producto).filter(
        Producto.proveedor_id == proveedor_id,
    ).order_by(Producto.categoria, Producto.nombre).all()
    return [
        {
            "id": p.id,
            "catalogo_id": p.catalogo_id,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "unidad": p.unidad,
            "precio_unitario": p.precio_unitario,
            "disponibilidad": p.disponibilidad,
            "precio_incluye_flete": p.precio_incluye_flete,
            "stock_actual": p.stock_actual,
            "activo": p.activo,
            "precio_actualizado": p.precio_actualizado.isoformat() if p.precio_actualizado else None,
        }
        for p in productos
    ]


@router.post("/api/proveedor/{proveedor_id}/productos")
def crear_producto(proveedor_id: int, body: ProductoBody, db: Session = Depends(get_db)):
    """Agregar producto al catalogo del proveedor."""
    producto = Producto(
        proveedor_id=proveedor_id,
        catalogo_id=body.catalogo_id,
        nombre=body.nombre,
        categoria=body.categoria,
        unidad=body.unidad,
        precio_unitario=body.precio_unitario,
        disponibilidad=body.disponibilidad,
        precio_incluye_flete=body.precio_incluye_flete,
        precio_actualizado=datetime.now(timezone.utc),
    )
    db.add(producto)
    db.commit()
    return {"ok": True, "producto_id": producto.id}


@router.put("/api/proveedor/{proveedor_id}/productos/{producto_id}")
def actualizar_producto(proveedor_id: int, producto_id: int, body: ProductoUpdateBody, db: Session = Depends(get_db)):
    """Actualizar precio/disponibilidad de un producto."""
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.proveedor_id == proveedor_id,
    ).first()
    if not producto:
        return {"ok": False, "error": "Producto no encontrado"}
    if body.precio_unitario is not None:
        producto.precio_unitario = body.precio_unitario
        producto.precio_actualizado = datetime.now(timezone.utc)
    if body.disponibilidad is not None:
        producto.disponibilidad = body.disponibilidad
    if body.activo is not None:
        producto.activo = body.activo
    if body.precio_incluye_flete is not None:
        producto.precio_incluye_flete = body.precio_incluye_flete
    db.commit()
    return {"ok": True}


@router.delete("/api/proveedor/{proveedor_id}/productos/{producto_id}")
def desactivar_producto(proveedor_id: int, producto_id: int, db: Session = Depends(get_db)):
    """Desactivar producto (soft delete)."""
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.proveedor_id == proveedor_id,
    ).first()
    if not producto:
        return {"ok": False, "error": "Producto no encontrado"}
    producto.activo = False
    db.commit()
    return {"ok": True}


# --- Solicitudes de cotizacion (pendientes de responder) ---

@router.get("/api/proveedor/{proveedor_id}/solicitudes")
def get_solicitudes(proveedor_id: int, db: Session = Depends(get_db)):
    """Solicitudes de cotizacion pendientes de responder."""
    solicitudes = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.proveedor_id == proveedor_id,
        SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"]),
    ).order_by(SolicitudProveedor.enviada_at.desc()).all()

    result = []
    for s in solicitudes:
        pedido = db.query(Pedido).filter(Pedido.id == s.pedido_id).first()
        items_data = []
        if pedido and pedido.pedido_interpretado:
            try:
                data = json.loads(pedido.pedido_interpretado)
                items_data = data.get("pedido", {}).get("items", [])
            except (json.JSONDecodeError, TypeError):
                pass
        result.append({
            "id": s.id,
            "pedido_id": s.pedido_id,
            "status": s.status,
            "mensaje_enviado": s.mensaje_enviado,
            "items": items_data,
            "direccion_entrega": pedido.direccion_entrega if pedido else "",
            "fecha_entrega": pedido.fecha_entrega.isoformat() if pedido and pedido.fecha_entrega else "",
            "enviada_at": s.enviada_at.isoformat() if s.enviada_at else None,
            "recordatorios": s.recordatorios_enviados or 0,
        })
    return result


@router.post("/api/proveedor/{proveedor_id}/solicitudes/{solicitud_id}/responder")
def responder_solicitud(
    proveedor_id: int,
    solicitud_id: int,
    body: ResponderSolicitudBody,
    db: Session = Depends(get_db),
):
    """Responder a una solicitud de cotizacion desde el portal web."""
    solicitud = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.id == solicitud_id,
        SolicitudProveedor.proveedor_id == proveedor_id,
    ).first()
    if not solicitud:
        return {"ok": False, "error": "Solicitud no encontrada"}

    ahora = datetime.now(timezone.utc)

    # Update solicitud
    solicitud.status = "respondida"
    solicitud.precio_total = body.precio_total
    solicitud.tiempo_entrega = body.tiempo_entrega
    solicitud.incluye_flete = body.incluye_flete
    solicitud.costo_flete = body.costo_flete
    solicitud.notas = body.notas
    solicitud.respondida_at = ahora
    if solicitud.enviada_at:
        diff = ahora - solicitud.enviada_at
        solicitud.tiempo_respuesta_minutos = int(diff.total_seconds() / 60)

    # Create Cotizacion record
    items_json = json.dumps(body.items, ensure_ascii=False) if body.items else "[]"
    subtotal = body.precio_total - body.costo_flete
    cotizacion = Cotizacion(
        pedido_id=solicitud.pedido_id,
        proveedor_id=proveedor_id,
        status="respondida",
        items=items_json,
        subtotal=subtotal,
        costo_flete=body.costo_flete,
        total=body.precio_total,
        tiempo_entrega=body.tiempo_entrega,
        notas_proveedor=body.notas,
        respondida_at=ahora,
    )
    db.add(cotizacion)
    db.commit()

    return {"ok": True}


# --- Perfil del proveedor ---

@router.get("/api/proveedor/{proveedor_id}/perfil")
def get_perfil(proveedor_id: int, db: Session = Depends(get_db)):
    """Obtener perfil del proveedor."""
    p = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not p:
        return {"ok": False, "error": "Proveedor no encontrado"}
    categorias = []
    try:
        categorias = json.loads(p.categorias) if p.categorias else []
    except (json.JSONDecodeError, TypeError):
        pass
    return {
        "ok": True,
        "perfil": {
            "id": p.id,
            "nombre": p.nombre,
            "tipo": p.tipo,
            "telefono_whatsapp": p.telefono_whatsapp,
            "email": p.email,
            "direccion": p.direccion,
            "municipio": p.municipio,
            "categorias": categorias,
            "horario_atencion": p.horario_atencion,
            "calificacion": p.calificacion,
            "total_pedidos": p.total_pedidos,
            "pedidos_cumplidos": p.pedidos_cumplidos,
        },
    }


@router.put("/api/proveedor/{proveedor_id}/perfil")
def actualizar_perfil(proveedor_id: int, body: PerfilProveedorBody, db: Session = Depends(get_db)):
    """Actualizar perfil del proveedor."""
    p = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not p:
        return {"ok": False, "error": "Proveedor no encontrado"}
    if body.nombre is not None:
        p.nombre = body.nombre
    if body.telefono_whatsapp is not None:
        p.telefono_whatsapp = body.telefono_whatsapp
    if body.email is not None:
        p.email = body.email
    if body.direccion is not None:
        p.direccion = body.direccion
    if body.municipio is not None:
        p.municipio = body.municipio
    if body.categorias is not None:
        p.categorias = json.dumps(body.categorias, ensure_ascii=False)
    if body.horario_atencion is not None:
        p.horario_atencion = body.horario_atencion
    p.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════
# FASE 6: VINCULAR WHATSAPP ↔ WEB
# ═══════════════════════════════════════════════════════════════════════

@router.post("/api/vincular-telefono")
def vincular_telefono(body: VincularTelefonoBody, db: Session = Depends(get_db)):
    """Vincular telefono WhatsApp a cuenta web."""
    usuario = db.query(Usuario).filter(Usuario.id == body.usuario_id).first()
    if not usuario:
        return {"ok": False, "error": "Usuario no encontrado"}

    telefono_full = body.telefono.replace("+", "").replace(" ", "")
    ordenes_vinculadas = 0

    # Check if there's an existing user with this phone
    usuario_tel = db.query(Usuario).filter(
        Usuario.telefono == telefono_full,
        Usuario.id != body.usuario_id,
    ).first()

    if usuario_tel:
        # Merge: move orders/pedidos from phone user to web user
        db.query(Pedido).filter(Pedido.usuario_id == usuario_tel.id).update(
            {"usuario_id": body.usuario_id}
        )
        ordenes_vinculadas += db.query(Orden).filter(Orden.usuario_id == usuario_tel.id).update(
            {"usuario_id": body.usuario_id}
        )
        db.query(PresupuestoObra).filter(PresupuestoObra.usuario_id == usuario_tel.id).update(
            {"usuario_id": body.usuario_id}
        )
        # Deactivate old user
        usuario_tel.activo = False if hasattr(usuario_tel, 'activo') else None

    # Set phone on web user
    usuario.telefono = telefono_full
    usuario.telefono_codigo_pais = body.codigo_pais
    db.commit()

    return {"ok": True, "ordenes_vinculadas": ordenes_vinculadas}
