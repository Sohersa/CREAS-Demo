"""
Dashboard Interno — Command Center para fundadores de ObraYa.
Metricas de negocio, pricing intelligence, proveedores, usuarios, ordenes y operaciones.
"""
import json
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, distinct, desc, extract

from app.database import get_db
from app.models.usuario import Usuario
from app.models.cotizacion import Cotizacion, Comparativa
from app.models.orden import Orden
from app.models.proveedor import Proveedor
from app.models.pedido import Pedido
from app.models.precio_historico import PrecioHistorico
from app.models.catalogo import CatalogoMaestro
from app.models.incidencia import IncidenciaEntrega
from app.models.calificacion import CalificacionProveedor
from app.models.solicitud_proveedor import SolicitudProveedor
from app.models.aprobacion import Aprobacion
from app.models.empresa import Empresa

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ============================================================
# HELPER: truncar fecha por periodo
# ============================================================

def _trunc_date(col, periodo):
    """Return grouping expressions for SQLite date truncation."""
    if periodo == "dia":
        return func.date(col)
    elif periodo == "semana":
        return func.strftime('%Y-W%W', col)
    else:  # mes
        return func.strftime('%Y-%m', col)


# ============================================================
# API ENDPOINTS
# ============================================================

# ---------- OVERVIEW ----------

@router.get("/api/overview")
def api_overview(db: Session = Depends(get_db)):
    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    total_cotizaciones = db.query(func.count(Cotizacion.id)).scalar() or 0
    total_ordenes = db.query(func.count(Orden.id)).scalar() or 0
    ordenes_activas = db.query(func.count(Orden.id)).filter(
        Orden.status.in_(["confirmada", "preparando", "en_transito", "en_obra"])
    ).scalar() or 0
    ordenes_completadas = db.query(func.count(Orden.id)).filter(
        Orden.status == "entregada"
    ).scalar() or 0
    total_proveedores = db.query(func.count(Proveedor.id)).filter(Proveedor.activo == True).scalar() or 0
    volumen_total = db.query(func.sum(Orden.total)).scalar() or 0
    volumen_completado = db.query(func.sum(Orden.total)).filter(Orden.status == "entregada").scalar() or 0

    tasa_conversion = 0
    if total_cotizaciones > 0:
        tasa_conversion = round((total_ordenes / total_cotizaciones) * 100, 1)

    revenue = round(volumen_completado * 0.02, 2)

    return {
        "total_usuarios": total_usuarios,
        "total_cotizaciones": total_cotizaciones,
        "total_ordenes": total_ordenes,
        "ordenes_activas": ordenes_activas,
        "ordenes_completadas": ordenes_completadas,
        "total_proveedores": total_proveedores,
        "volumen_total": round(volumen_total, 2),
        "tasa_conversion": tasa_conversion,
        "revenue": revenue,
    }


@router.get("/api/cotizaciones-por-periodo")
def api_cotizaciones_periodo(periodo: str = Query("semana", pattern="^(dia|semana|mes)$"), db: Session = Depends(get_db)):
    group_expr = _trunc_date(Cotizacion.enviada_at, periodo)
    rows = db.query(
        group_expr.label("periodo"),
        func.count(Cotizacion.id).label("total"),
    ).group_by("periodo").order_by("periodo").all()
    return [{"periodo": r.periodo, "total": r.total} for r in rows]


@router.get("/api/usuarios-por-periodo")
def api_usuarios_periodo(periodo: str = Query("semana", pattern="^(semana|mes)$"), db: Session = Depends(get_db)):
    group_expr = _trunc_date(Usuario.created_at, periodo)
    rows = db.query(
        group_expr.label("periodo"),
        func.count(Usuario.id).label("total"),
    ).group_by("periodo").order_by("periodo").all()
    return [{"periodo": r.periodo, "total": r.total} for r in rows]


@router.get("/api/ordenes-por-status")
def api_ordenes_status(db: Session = Depends(get_db)):
    rows = db.query(
        Orden.status,
        func.count(Orden.id).label("total"),
    ).group_by(Orden.status).all()
    return [{"status": r.status, "total": r.total} for r in rows]


@router.get("/api/categorias")
def api_categorias(db: Session = Depends(get_db)):
    rows = db.query(
        PrecioHistorico.categoria,
        func.count(PrecioHistorico.id).label("total"),
    ).filter(PrecioHistorico.categoria != None).group_by(PrecioHistorico.categoria).order_by(desc("total")).all()
    return [{"categoria": r.categoria or "Sin categoria", "total": r.total} for r in rows]


# ---------- PRICING INTELLIGENCE ----------

@router.get("/api/pricing/tendencia")
def api_pricing_tendencia(catalogo_id: int = Query(...), db: Session = Depends(get_db)):
    rows = db.query(
        func.strftime('%Y-%m', PrecioHistorico.fecha).label("periodo"),
        func.avg(PrecioHistorico.precio_unitario).label("promedio"),
        func.min(PrecioHistorico.precio_unitario).label("minimo"),
        func.max(PrecioHistorico.precio_unitario).label("maximo"),
        func.count(PrecioHistorico.id).label("cotizaciones"),
    ).filter(
        PrecioHistorico.catalogo_id == catalogo_id,
        PrecioHistorico.es_outlier == False,
    ).group_by("periodo").order_by("periodo").all()
    return [{
        "periodo": r.periodo,
        "promedio": round(r.promedio, 2) if r.promedio else 0,
        "minimo": round(r.minimo, 2) if r.minimo else 0,
        "maximo": round(r.maximo, 2) if r.maximo else 0,
        "cotizaciones": r.cotizaciones,
    } for r in rows]


@router.get("/api/pricing/ultimos")
def api_pricing_ultimos(db: Session = Depends(get_db)):
    rows = db.query(PrecioHistorico).order_by(PrecioHistorico.fecha.desc()).limit(50).all()
    return [{
        "id": r.id,
        "producto": r.producto_normalizado or r.producto_nombre,
        "categoria": r.categoria,
        "proveedor": r.proveedor_nombre,
        "precio_unitario": r.precio_unitario,
        "unidad": r.unidad,
        "precio_efectivo": r.precio_efectivo,
        "zona": r.zona,
        "fecha": r.fecha.isoformat() if r.fecha else None,
        "es_outlier": r.es_outlier,
    } for r in rows]


@router.get("/api/pricing/top-productos")
def api_pricing_top_productos(db: Session = Depends(get_db)):
    rows = db.query(
        PrecioHistorico.producto_normalizado,
        func.count(PrecioHistorico.id).label("total"),
        func.avg(PrecioHistorico.precio_unitario).label("precio_promedio"),
    ).filter(
        PrecioHistorico.producto_normalizado != None,
        PrecioHistorico.es_outlier == False,
    ).group_by(PrecioHistorico.producto_normalizado).order_by(desc("total")).limit(10).all()
    return [{
        "producto": r.producto_normalizado,
        "total_cotizaciones": r.total,
        "precio_promedio": round(r.precio_promedio, 2) if r.precio_promedio else 0,
    } for r in rows]


@router.get("/api/pricing/variaciones")
def api_pricing_variaciones(db: Session = Depends(get_db)):
    """Variacion de precio por producto: compara ultimo mes vs anterior."""
    ahora = datetime.now(timezone.utc)
    mes_actual_inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    mes_anterior_inicio = (mes_actual_inicio - timedelta(days=1)).replace(day=1)

    productos = db.query(
        PrecioHistorico.catalogo_id,
        PrecioHistorico.producto_normalizado,
    ).filter(
        PrecioHistorico.catalogo_id != None,
        PrecioHistorico.producto_normalizado != None,
    ).group_by(PrecioHistorico.catalogo_id, PrecioHistorico.producto_normalizado).all()

    result = []
    for p in productos:
        avg_actual = db.query(func.avg(PrecioHistorico.precio_unitario)).filter(
            PrecioHistorico.catalogo_id == p.catalogo_id,
            PrecioHistorico.fecha >= mes_actual_inicio,
            PrecioHistorico.es_outlier == False,
        ).scalar()
        avg_anterior = db.query(func.avg(PrecioHistorico.precio_unitario)).filter(
            PrecioHistorico.catalogo_id == p.catalogo_id,
            PrecioHistorico.fecha >= mes_anterior_inicio,
            PrecioHistorico.fecha < mes_actual_inicio,
            PrecioHistorico.es_outlier == False,
        ).scalar()

        variacion = 0
        if avg_anterior and avg_actual:
            variacion = round(((avg_actual - avg_anterior) / avg_anterior) * 100, 2)

        result.append({
            "catalogo_id": p.catalogo_id,
            "producto": p.producto_normalizado,
            "precio_actual": round(avg_actual, 2) if avg_actual else None,
            "precio_anterior": round(avg_anterior, 2) if avg_anterior else None,
            "variacion_pct": variacion,
        })

    result.sort(key=lambda x: abs(x["variacion_pct"]), reverse=True)
    return result


@router.get("/api/pricing/catalogo")
def api_pricing_catalogo(db: Session = Depends(get_db)):
    """Lista de productos del catalogo para dropdown."""
    rows = db.query(CatalogoMaestro.id, CatalogoMaestro.nombre, CatalogoMaestro.categoria).filter(
        CatalogoMaestro.activo == True
    ).order_by(CatalogoMaestro.nombre).all()
    return [{"id": r.id, "nombre": r.nombre, "categoria": r.categoria} for r in rows]


@router.get("/api/pricing/kpis")
def api_pricing_kpis(db: Session = Depends(get_db)):
    total_datos = db.query(func.count(PrecioHistorico.id)).scalar() or 0
    productos_trackeados = db.query(func.count(distinct(PrecioHistorico.catalogo_id))).filter(
        PrecioHistorico.catalogo_id != None
    ).scalar() or 0
    proveedores_trackeados = db.query(func.count(distinct(PrecioHistorico.proveedor_id))).filter(
        PrecioHistorico.proveedor_id != None
    ).scalar() or 0
    return {
        "total_datos": total_datos,
        "productos_trackeados": productos_trackeados,
        "proveedores_trackeados": proveedores_trackeados,
    }


# ---------- SUPPLIERS ----------

@router.get("/api/proveedores")
def api_proveedores(db: Session = Depends(get_db)):
    rows = db.query(Proveedor).filter(Proveedor.activo == True).order_by(Proveedor.calificacion.desc()).all()
    return [{
        "id": p.id,
        "nombre": p.nombre,
        "tipo": p.tipo,
        "categorias": p.categorias,
        "calificacion": p.calificacion,
        "total_pedidos": p.total_pedidos,
        "tasa_puntualidad": round(p.tasa_puntualidad * 100, 1) if p.tasa_puntualidad else 0,
        "tasa_cantidad": round(p.tasa_cantidad_correcta * 100, 1) if p.tasa_cantidad_correcta else 0,
        "tiempo_respuesta_promedio": p.tiempo_respuesta_promedio,
        "total_incidencias": p.total_incidencias,
        "total_ordenes_completadas": p.total_ordenes_completadas,
        "municipio": p.municipio,
    } for p in rows]


@router.get("/api/proveedores/top-calificacion")
def api_proveedores_top_cal(db: Session = Depends(get_db)):
    rows = db.query(Proveedor).filter(
        Proveedor.activo == True, Proveedor.total_pedidos > 0
    ).order_by(Proveedor.calificacion.desc()).limit(10).all()
    return [{"nombre": p.nombre, "calificacion": p.calificacion, "total_pedidos": p.total_pedidos} for p in rows]


@router.get("/api/proveedores/top-volumen")
def api_proveedores_top_vol(db: Session = Depends(get_db)):
    rows = db.query(
        Proveedor.nombre,
        func.count(Orden.id).label("ordenes"),
        func.sum(Orden.total).label("volumen"),
    ).join(Orden, Orden.proveedor_id == Proveedor.id).group_by(
        Proveedor.nombre
    ).order_by(desc("ordenes")).limit(10).all()
    return [{"nombre": r.nombre, "ordenes": r.ordenes, "volumen": round(r.volumen or 0, 2)} for r in rows]


@router.get("/api/proveedores/por-tipo")
def api_proveedores_tipo(db: Session = Depends(get_db)):
    rows = db.query(
        Proveedor.tipo,
        func.count(Proveedor.id).label("total"),
    ).filter(Proveedor.activo == True).group_by(Proveedor.tipo).all()
    return [{"tipo": r.tipo, "total": r.total} for r in rows]


@router.get("/api/proveedores/kpis")
def api_proveedores_kpis(db: Session = Depends(get_db)):
    activos = db.query(func.count(Proveedor.id)).filter(Proveedor.activo == True).scalar() or 0
    avg_resp = db.query(func.avg(Proveedor.tiempo_respuesta_promedio)).filter(
        Proveedor.activo == True
    ).scalar() or 0

    total_sol = db.query(func.count(SolicitudProveedor.id)).scalar() or 0
    respondidas = db.query(func.count(SolicitudProveedor.id)).filter(
        SolicitudProveedor.status == "respondida"
    ).scalar() or 0
    tasa_resp = round((respondidas / total_sol * 100), 1) if total_sol > 0 else 0

    return {
        "activos": activos,
        "tasa_respuesta": tasa_resp,
        "tiempo_respuesta_promedio": round(avg_resp, 0) if avg_resp else 0,
    }


# ---------- USERS ----------

@router.get("/api/usuarios")
def api_usuarios(db: Session = Depends(get_db)):
    users = db.query(Usuario).order_by(Usuario.created_at.desc()).all()
    result = []
    for u in users:
        total_pedidos = db.query(func.count(Pedido.id)).filter(Pedido.usuario_id == u.id).scalar() or 0
        total_gastado = db.query(func.sum(Orden.total)).filter(Orden.usuario_id == u.id, Orden.status == "entregada").scalar() or 0
        result.append({
            "id": u.id,
            "nombre": u.nombre or "Sin nombre",
            "telefono": u.telefono,
            "tipo": u.tipo,
            "total_pedidos": total_pedidos,
            "total_gastado": round(total_gastado or 0, 2),
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "ultimo_pedido": u.ultimo_pedido.isoformat() if u.ultimo_pedido else None,
        })
    return result


@router.get("/api/usuarios/top-compradores")
def api_usuarios_top(db: Session = Depends(get_db)):
    rows = db.query(
        Usuario.nombre,
        func.count(Orden.id).label("ordenes"),
        func.sum(Orden.total).label("volumen"),
    ).join(Orden, Orden.usuario_id == Usuario.id).filter(
        Orden.status == "entregada"
    ).group_by(Usuario.nombre).order_by(desc("volumen")).limit(10).all()
    return [{"nombre": r.nombre or "Sin nombre", "ordenes": r.ordenes, "volumen": round(r.volumen or 0, 2)} for r in rows]


@router.get("/api/usuarios/kpis")
def api_usuarios_kpis(db: Session = Depends(get_db)):
    total = db.query(func.count(Usuario.id)).scalar() or 0
    mes_pasado = datetime.now(timezone.utc) - timedelta(days=30)
    activos = db.query(func.count(distinct(Orden.usuario_id))).filter(
        Orden.created_at >= mes_pasado
    ).scalar() or 0

    avg_ticket = db.query(func.avg(Orden.total)).filter(Orden.status == "entregada").scalar() or 0

    return {
        "total": total,
        "activos_ultimo_mes": activos,
        "ticket_promedio": round(avg_ticket, 2),
    }


# ---------- ORDERS & REVENUE ----------

@router.get("/api/ordenes")
def api_ordenes(db: Session = Depends(get_db)):
    rows = db.query(Orden).order_by(Orden.created_at.desc()).limit(100).all()
    result = []
    for o in rows:
        prov = db.query(Proveedor.nombre).filter(Proveedor.id == o.proveedor_id).scalar()
        usr = db.query(Usuario.nombre).filter(Usuario.id == o.usuario_id).scalar()
        result.append({
            "id": o.id,
            "status": o.status,
            "proveedor": prov or "-",
            "usuario": usr or "-",
            "total": o.total,
            "municipio": o.municipio_entrega,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })
    return result


@router.get("/api/revenue-por-mes")
def api_revenue_mes(db: Session = Depends(get_db)):
    rows = db.query(
        func.strftime('%Y-%m', Orden.confirmada_at).label("mes"),
        func.sum(Orden.total).label("volumen"),
        func.count(Orden.id).label("ordenes"),
    ).filter(Orden.status == "entregada").group_by("mes").order_by("mes").all()
    return [{
        "mes": r.mes,
        "volumen": round(r.volumen or 0, 2),
        "revenue": round((r.volumen or 0) * 0.02, 2),
        "ordenes": r.ordenes,
    } for r in rows]


@router.get("/api/ordenes-por-mes")
def api_ordenes_mes(db: Session = Depends(get_db)):
    rows = db.query(
        func.strftime('%Y-%m', Orden.created_at).label("mes"),
        Orden.status,
        func.count(Orden.id).label("total"),
    ).group_by("mes", Orden.status).order_by("mes").all()

    # Reorganize for stacked bar
    meses = {}
    for r in rows:
        if r.mes not in meses:
            meses[r.mes] = {}
        meses[r.mes][r.status] = r.total

    return [{"mes": m, **statuses} for m, statuses in sorted(meses.items())]


@router.get("/api/ordenes/kpis")
def api_ordenes_kpis(db: Session = Depends(get_db)):
    revenue_total = db.query(func.sum(Orden.total)).filter(Orden.status == "entregada").scalar() or 0
    mes_inicio = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_mes = db.query(func.sum(Orden.total)).filter(
        Orden.status == "entregada",
        Orden.confirmada_at >= mes_inicio,
    ).scalar() or 0
    completadas = db.query(func.count(Orden.id)).filter(Orden.status == "entregada").scalar() or 0
    con_incidencia = db.query(func.count(Orden.id)).filter(Orden.status == "con_incidencia").scalar() or 0
    avg_ticket = db.query(func.avg(Orden.total)).filter(Orden.status == "entregada").scalar() or 0

    return {
        "revenue_total": round(revenue_total * 0.02, 2),
        "revenue_mes": round(revenue_mes * 0.02, 2),
        "completadas": completadas,
        "con_incidencia": con_incidencia,
        "ticket_promedio": round(avg_ticket, 2),
    }


# ---------- OPERATIONS ----------

@router.get("/api/operaciones")
def api_operaciones(db: Session = Depends(get_db)):
    # Incidencias abiertas
    incidencias = db.query(IncidenciaEntrega).filter(
        IncidenciaEntrega.status.in_(["abierta", "en_revision"])
    ).order_by(IncidenciaEntrega.created_at.desc()).all()
    incidencias_list = [{
        "id": i.id,
        "orden_id": i.orden_id,
        "tipo": i.tipo,
        "severidad": i.severidad,
        "status": i.status,
        "descripcion": i.descripcion_interpretada or i.descripcion_usuario,
        "created_at": i.created_at.isoformat() if i.created_at else None,
    } for i in incidencias]

    # Ordenes activas
    ordenes_activas = db.query(Orden).filter(
        Orden.status.in_(["confirmada", "preparando", "en_transito"])
    ).order_by(Orden.created_at.desc()).all()
    ordenes_list = [{
        "id": o.id,
        "status": o.status,
        "total": o.total,
        "municipio": o.municipio_entrega,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    } for o in ordenes_activas]

    # Peores proveedores
    peores = db.query(Proveedor).filter(
        Proveedor.activo == True, Proveedor.total_pedidos > 0
    ).order_by(Proveedor.calificacion.asc()).limit(5).all()
    peores_list = [{"nombre": p.nombre, "calificacion": p.calificacion, "total_incidencias": p.total_incidencias} for p in peores]

    # Solicitudes sin respuesta
    sin_respuesta = db.query(
        func.count(SolicitudProveedor.id)
    ).filter(SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"])).scalar() or 0

    # KPIs de operaciones
    total_incidencias = db.query(func.count(IncidenciaEntrega.id)).scalar() or 0
    total_ordenes = db.query(func.count(Orden.id)).scalar() or 0
    tasa_incidencias = round((total_incidencias / total_ordenes * 100), 1) if total_ordenes > 0 else 0

    total_sol = db.query(func.count(SolicitudProveedor.id)).scalar() or 0
    respondidas = db.query(func.count(SolicitudProveedor.id)).filter(SolicitudProveedor.status == "respondida").scalar() or 0
    tasa_resp = round((respondidas / total_sol * 100), 1) if total_sol > 0 else 0

    return {
        "incidencias": incidencias_list,
        "ordenes_activas": ordenes_list,
        "peores_proveedores": peores_list,
        "solicitudes_sin_respuesta": sin_respuesta,
        "kpis": {
            "tasa_incidencias": tasa_incidencias,
            "tasa_respuesta_proveedores": tasa_resp,
        },
    }


# ---------- APROBACIONES ----------

@router.get("/api/aprobaciones")
def api_aprobaciones(db: Session = Depends(get_db)):
    """Datos de aprobaciones para el dashboard."""
    pendientes = db.query(func.count(Aprobacion.id)).filter(Aprobacion.status == "pendiente").scalar() or 0
    aprobadas = db.query(func.count(Aprobacion.id)).filter(Aprobacion.status == "aprobada").scalar() or 0
    rechazadas = db.query(func.count(Aprobacion.id)).filter(Aprobacion.status == "rechazada").scalar() or 0
    expiradas = db.query(func.count(Aprobacion.id)).filter(Aprobacion.status == "expirada").scalar() or 0
    total = db.query(func.count(Aprobacion.id)).scalar() or 0

    # Lista pendientes con detalles
    pendientes_q = db.query(Aprobacion).filter(Aprobacion.status == "pendiente").order_by(Aprobacion.created_at.desc()).all()
    lista_pendientes = []
    for a in pendientes_q:
        solicitante = db.query(Usuario).filter(Usuario.id == a.solicitante_id).first()
        empresa = db.query(Empresa).filter(Empresa.id == a.empresa_id).first() if a.empresa_id else None
        lista_pendientes.append({
            "id": a.id,
            "orden_id": a.orden_id,
            "solicitante": solicitante.nombre if solicitante else f"Tel: {solicitante.telefono}" if solicitante else "?",
            "monto": a.monto,
            "empresa": empresa.nombre if empresa else "-",
            "nota": a.nota_solicitud or "",
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "expira_at": a.expira_at.isoformat() if a.expira_at else None,
        })

    # Historial (ultimas 50 resueltas)
    historial_q = db.query(Aprobacion).filter(
        Aprobacion.status.in_(["aprobada", "rechazada", "expirada"])
    ).order_by(Aprobacion.updated_at.desc()).limit(50).all()
    historial = []
    for a in historial_q:
        solicitante = db.query(Usuario).filter(Usuario.id == a.solicitante_id).first()
        aprobador = db.query(Usuario).filter(Usuario.id == a.aprobador_id).first() if a.aprobador_id else None
        historial.append({
            "id": a.id,
            "orden_id": a.orden_id,
            "solicitante": solicitante.nombre if solicitante else "?",
            "monto": a.monto,
            "status": a.status,
            "aprobador": aprobador.nombre if aprobador else "-",
            "nota_respuesta": a.nota_respuesta or "",
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })

    return {
        "pendientes": pendientes,
        "aprobadas": aprobadas,
        "rechazadas": rechazadas,
        "expiradas": expiradas,
        "total": total,
        "lista_pendientes": lista_pendientes,
        "historial": historial,
    }


# ============================================================
# DASHBOARD HTML — Single Page App
# ============================================================

@router.get("/", response_class=HTMLResponse)
def dashboard_page():
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ObraYa | Command Center</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --navy: #0F1B2D;
  --navy-light: #162236;
  --navy-lighter: #1C2C42;
  --orange: #E67E22;
  --orange-hover: #D35400;
  --blue: #2E86C1;
  --green: #27AE60;
  --red: #E74C3C;
  --bg: #F0F2F5;
  --card: #FFFFFF;
  --text: #1A1A2E;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
  --sidebar-w: 240px;
}
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); display: flex; min-height: 100vh; font-size: 14px; }

/* --- Sidebar --- */
.sidebar {
  width: var(--sidebar-w); background: var(--navy); color: #fff; display: flex; flex-direction: column;
  position: fixed; top: 0; left: 0; bottom: 0; z-index: 100; transition: transform .2s;
}
.sidebar-brand { padding: 24px 20px; border-bottom: 1px solid var(--navy-lighter); }
.sidebar-brand h1 { font-size: 18px; font-weight: 700; letter-spacing: -.3px; }
.sidebar-brand span { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
.sidebar-nav { flex: 1; padding: 12px 0; }
.sidebar-nav a {
  display: flex; align-items: center; gap: 12px; padding: 10px 20px; color: #94A3B8;
  text-decoration: none; font-size: 13px; font-weight: 500; transition: all .15s; border-left: 3px solid transparent;
}
.sidebar-nav a:hover { color: #fff; background: var(--navy-light); }
.sidebar-nav a.active { color: #fff; background: var(--navy-light); border-left-color: var(--orange); }
.sidebar-nav a svg { width: 18px; height: 18px; flex-shrink: 0; }
.sidebar-footer { padding: 16px 20px; border-top: 1px solid var(--navy-lighter); font-size: 11px; color: #64748B; }

/* --- Main --- */
.main { margin-left: var(--sidebar-w); flex: 1; min-height: 100vh; }
.topbar {
  height: 56px; background: var(--card); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; padding: 0 28px; position: sticky; top: 0; z-index: 50;
}
.topbar h2 { font-size: 16px; font-weight: 600; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.topbar-badge { background: var(--orange); color: #fff; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }
.content { padding: 24px 28px; }

/* --- KPI cards --- */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card {
  background: var(--card); border-radius: 10px; padding: 20px; border: 1px solid var(--border);
  transition: box-shadow .2s;
}
.kpi-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.06); }
.kpi-label { font-size: 12px; font-weight: 500; color: var(--text-secondary); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 700; line-height: 1; }
.kpi-value.orange { color: var(--orange); }
.kpi-value.blue { color: var(--blue); }
.kpi-value.green { color: var(--green); }

/* --- Chart cards --- */
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.chart-card {
  background: var(--card); border-radius: 10px; padding: 20px; border: 1px solid var(--border);
}
.chart-card.full { grid-column: 1 / -1; }
.chart-card h3 { font-size: 14px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.chart-card canvas { width: 100% !important; max-height: 300px; }

/* --- Controls --- */
.controls { display: flex; gap: 8px; margin-bottom: 16px; }
.controls select, .controls button {
  padding: 6px 14px; border-radius: 6px; font-size: 12px; font-family: inherit; cursor: pointer; font-weight: 500;
}
.controls select { border: 1px solid var(--border); background: var(--card); color: var(--text); }
.controls button { border: 1px solid var(--border); background: var(--card); color: var(--text); transition: all .15s; }
.controls button.active, .controls button:hover { background: var(--navy); color: #fff; border-color: var(--navy); }

/* --- Tables --- */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
table th { background: var(--bg); font-weight: 600; text-align: left; padding: 10px 12px; font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--text-secondary); }
table td { padding: 10px 12px; border-bottom: 1px solid var(--border); }
table tr:hover td { background: #F8FAFC; }
.badge {
  display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;
}
.badge-green { background: #D1FAE5; color: #065F46; }
.badge-blue { background: #DBEAFE; color: #1E40AF; }
.badge-orange { background: #FEF3C7; color: #92400E; }
.badge-red { background: #FEE2E2; color: #991B1B; }
.badge-gray { background: #F3F4F6; color: #4B5563; }

/* --- Heatmap cards --- */
.heatmap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin-bottom: 24px; }
.heatmap-card {
  background: var(--card); border-radius: 8px; padding: 14px; border: 1px solid var(--border);
}
.heatmap-card .product-name { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.heatmap-card .price-row { font-size: 12px; color: var(--text-secondary); }
.heatmap-card .variation { font-size: 20px; font-weight: 700; margin-top: 4px; }
.heatmap-card .variation.up { color: var(--red); }
.heatmap-card .variation.down { color: var(--green); }
.heatmap-card .variation.flat { color: var(--text-secondary); }

/* --- Tab sections --- */
.tab-section { display: none; }
.tab-section.active { display: block; }

/* --- Responsive --- */
@media (max-width: 1024px) {
  .chart-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }
  .sidebar.open { transform: translateX(0); }
  .main { margin-left: 0; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .topbar { padding: 0 16px; }
  .content { padding: 16px; }
}

/* Loading spinner */
.spinner { display: inline-block; width: 18px; height: 18px; border: 2px solid var(--border); border-top-color: var(--orange); border-radius: 50%; animation: spin .6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-overlay { display: flex; align-items: center; justify-content: center; padding: 40px; color: var(--text-secondary); gap: 8px; }
</style>
</head>
<body>

<!-- SIDEBAR -->
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand">
    <h1>ObraYa</h1>
    <span>Command Center</span>
  </div>
  <nav class="sidebar-nav">
    <a href="#" class="active" data-tab="overview">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
      Overview
    </a>
    <a href="#" data-tab="pricing">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      Pricing Intelligence
    </a>
    <a href="#" data-tab="suppliers">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4z"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>
      Proveedores
    </a>
    <a href="#" data-tab="users">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
      Usuarios
    </a>
    <a href="#" data-tab="orders">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
      Ordenes & Revenue
    </a>
    <a href="#" data-tab="operations">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      Operaciones
    </a>
    <a href="#" data-tab="aprobaciones">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      Aprobaciones
    </a>
    <a href="#" data-tab="credito">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
      Credito
    </a>
  </nav>
  <div class="sidebar-footer">ObraYa v0.1</div>
</aside>

<!-- MAIN -->
<div class="main">
  <div class="topbar">
    <h2 id="topbar-title">Overview</h2>
    <div class="topbar-right">
      <span id="topbar-badge" class="topbar-badge" style="display:none"></span>
      <span style="font-size:12px;color:var(--text-secondary)" id="last-updated"></span>
    </div>
  </div>

  <div class="content">

    <!-- ===================== OVERVIEW ===================== -->
    <div class="tab-section active" id="tab-overview">
      <div class="kpi-grid" id="overview-kpis"></div>
      <div class="controls">
        <button class="active" data-cotperiodo="semana" onclick="setCotPeriodo(this)">Semana</button>
        <button data-cotperiodo="dia" onclick="setCotPeriodo(this)">Dia</button>
        <button data-cotperiodo="mes" onclick="setCotPeriodo(this)">Mes</button>
      </div>
      <div class="chart-grid">
        <div class="chart-card"><h3>Cotizaciones por periodo</h3><canvas id="chart-cot-periodo"></canvas></div>
        <div class="chart-card"><h3>Usuarios nuevos por semana</h3><canvas id="chart-users-week"></canvas></div>
        <div class="chart-card"><h3>Ordenes por status</h3><canvas id="chart-ordenes-status"></canvas></div>
        <div class="chart-card"><h3>Distribucion por categoria</h3><canvas id="chart-categorias"></canvas></div>
      </div>
    </div>

    <!-- ===================== PRICING ===================== -->
    <div class="tab-section" id="tab-pricing">
      <div class="kpi-grid" id="pricing-kpis"></div>
      <div class="controls">
        <select id="pricing-product-select" onchange="loadPricingTrend()">
          <option value="">-- Selecciona producto --</option>
        </select>
      </div>
      <div class="chart-grid">
        <div class="chart-card full"><h3>Tendencia de precio</h3><canvas id="chart-price-trend"></canvas></div>
        <div class="chart-card"><h3>Top 10 productos mas cotizados</h3><canvas id="chart-top-productos"></canvas></div>
      </div>
      <h3 style="margin-bottom:12px;font-size:14px;font-weight:600">Variacion de precios</h3>
      <div class="heatmap-grid" id="pricing-heatmap"></div>
      <div class="chart-card" style="margin-top:16px">
        <h3>Ultimos 50 precios registrados</h3>
        <div class="table-wrap" id="pricing-table"></div>
      </div>
    </div>

    <!-- ===================== SUPPLIERS ===================== -->
    <div class="tab-section" id="tab-suppliers">
      <div class="kpi-grid" id="suppliers-kpis"></div>
      <div class="chart-grid">
        <div class="chart-card"><h3>Top 10 por calificacion</h3><canvas id="chart-prov-cal"></canvas></div>
        <div class="chart-card"><h3>Top 10 por volumen (ordenes)</h3><canvas id="chart-prov-vol"></canvas></div>
        <div class="chart-card"><h3>Proveedores por tipo</h3><canvas id="chart-prov-tipo"></canvas></div>
      </div>
      <div class="chart-card" style="margin-top:16px">
        <h3>Todos los proveedores</h3>
        <div class="table-wrap" id="suppliers-table"></div>
      </div>
    </div>

    <!-- ===================== USERS ===================== -->
    <div class="tab-section" id="tab-users">
      <div class="kpi-grid" id="users-kpis"></div>
      <div class="chart-grid">
        <div class="chart-card"><h3>Registros por semana</h3><canvas id="chart-user-reg"></canvas></div>
        <div class="chart-card"><h3>Top 10 compradores</h3><canvas id="chart-top-buyers"></canvas></div>
      </div>
      <div class="chart-card" style="margin-top:16px">
        <h3>Todos los usuarios</h3>
        <div class="table-wrap" id="users-table"></div>
      </div>
    </div>

    <!-- ===================== ORDERS & REVENUE ===================== -->
    <div class="tab-section" id="tab-orders">
      <div class="kpi-grid" id="orders-kpis"></div>
      <div class="chart-grid">
        <div class="chart-card"><h3>Revenue ObraYa por mes (2% comision)</h3><canvas id="chart-revenue"></canvas></div>
        <div class="chart-card"><h3>Ordenes por mes</h3><canvas id="chart-ordenes-mes"></canvas></div>
      </div>
      <div class="chart-card" style="margin-top:16px">
        <h3>Todas las ordenes</h3>
        <div class="table-wrap" id="orders-table"></div>
      </div>
    </div>

    <!-- ===================== OPERATIONS ===================== -->
    <div class="tab-section" id="tab-operations">
      <div class="kpi-grid" id="ops-kpis"></div>
      <div class="chart-grid">
        <div class="chart-card full">
          <h3>Incidencias abiertas</h3>
          <div class="table-wrap" id="ops-incidencias"></div>
        </div>
        <div class="chart-card">
          <h3>Ordenes activas</h3>
          <div class="table-wrap" id="ops-ordenes"></div>
        </div>
        <div class="chart-card">
          <h3>Proveedores con peor calificacion</h3>
          <div class="table-wrap" id="ops-peores"></div>
        </div>
      </div>
    </div>

    <!-- ===================== APROBACIONES ===================== -->
    <div class="tab-section" id="tab-aprobaciones">
      <div class="kpi-grid" id="aprobaciones-kpis"></div>
      <div class="chart-card" style="margin-top:20px;">
        <h3>Solicitudes de Aprobacion</h3>
        <div id="aprobaciones-list"></div>
      </div>
      <div class="chart-card" style="margin-top:20px;">
        <h3>Historial de Aprobaciones</h3>
        <div id="aprobaciones-historial"></div>
      </div>
    </div>

    <!-- ===================== CREDITO ===================== -->
    <div class="tab-section" id="tab-credito">
      <div class="kpi-grid" id="credito-kpis"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px;">
        <div class="chart-card"><h3>Distribucion de Scores</h3><canvas id="chart-score-dist"></canvas></div>
        <div class="chart-card"><h3>Top Usuarios por Score</h3><div id="credito-ranking"></div></div>
      </div>
    </div>

  </div>
</div>

<script>
const API = '/dashboard/api';
const charts = {};

// ============================================================
// NAVIGATION
// ============================================================
document.querySelectorAll('.sidebar-nav a').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const tab = link.dataset.tab;
    document.querySelectorAll('.sidebar-nav a').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
    document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    document.getElementById('topbar-title').textContent = link.textContent.trim();
    loadTab(tab);
  });
});

// ============================================================
// UTILITY
// ============================================================
async function fetchJSON(url) {
  const r = await fetch(url);
  return r.json();
}
function fmtMoney(n) { return '$' + (n || 0).toLocaleString('es-MX', {minimumFractionDigits: 0, maximumFractionDigits: 0}); }
function fmtPct(n) { return (n || 0) + '%'; }
function destroyChart(id) { if (charts[id]) { charts[id].destroy(); delete charts[id]; } }
function statusBadge(s) {
  const map = {entregada:'green',confirmada:'blue',preparando:'orange',en_transito:'blue',en_obra:'orange',con_incidencia:'red',cancelada:'gray'};
  return '<span class="badge badge-'+(map[s]||'gray')+'">'+s+'</span>';
}
function severityBadge(s) {
  const map = {leve:'blue',media:'orange',grave:'red'};
  return '<span class="badge badge-'+(map[s]||'gray')+'">'+s+'</span>';
}
function fmtDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', {day:'2-digit',month:'short',year:'numeric'});
}

function renderKPIs(containerId, kpis) {
  document.getElementById(containerId).innerHTML = kpis.map(k =>
    '<div class="kpi-card"><div class="kpi-label">'+k.label+'</div><div class="kpi-value '+(k.color||'')+'">'+k.value+'</div></div>'
  ).join('');
}

const chartColors = {
  orange: '#E67E22', blue: '#2E86C1', green: '#27AE60', red: '#E74C3C', navy: '#0F1B2D',
  purple: '#8E44AD', teal: '#1ABC9C', yellow: '#F1C40F', gray: '#95A5A6',
  palette: ['#2E86C1','#E67E22','#27AE60','#E74C3C','#8E44AD','#1ABC9C','#F1C40F','#95A5A6','#0F1B2D','#D35400']
};

// ============================================================
// TAB LOADERS
// ============================================================
const tabLoaded = {};
function loadTab(tab) {
  if (tabLoaded[tab]) return;
  tabLoaded[tab] = true;
  const loaders = {overview: loadOverview, pricing: loadPricing, suppliers: loadSuppliers, users: loadUsers, orders: loadOrders, operations: loadOperations, aprobaciones: loadAprobaciones, credito: loadCredito};
  if (loaders[tab]) loaders[tab]();
}

// ============================================================
// OVERVIEW
// ============================================================
let cotPeriodo = 'semana';
function setCotPeriodo(btn) {
  document.querySelectorAll('[data-cotperiodo]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  cotPeriodo = btn.dataset.cotperiodo;
  tabLoaded['overview'] = false;
  loadOverviewCotChart();
}

async function loadOverview() {
  const data = await fetchJSON(API+'/overview');
  renderKPIs('overview-kpis', [
    {label:'Usuarios', value:data.total_usuarios, color:'blue'},
    {label:'Cotizaciones', value:data.total_cotizaciones, color:''},
    {label:'Ordenes totales', value:data.total_ordenes, color:''},
    {label:'Ordenes activas', value:data.ordenes_activas, color:'orange'},
    {label:'Proveedores', value:data.total_proveedores, color:''},
    {label:'Volumen transaccionado', value:fmtMoney(data.volumen_total), color:''},
    {label:'Tasa conversion', value:fmtPct(data.tasa_conversion), color:'blue'},
    {label:'Revenue ObraYa (2%)', value:fmtMoney(data.revenue), color:'green'},
  ]);
  if (data.ordenes_activas > 0) {
    document.getElementById('topbar-badge').style.display = '';
    document.getElementById('topbar-badge').textContent = data.ordenes_activas + ' activas';
  }
  loadOverviewCotChart();
  loadOverviewCharts();
}

async function loadOverviewCotChart() {
  const data = await fetchJSON(API+'/cotizaciones-por-periodo?periodo='+cotPeriodo);
  destroyChart('chart-cot-periodo');
  charts['chart-cot-periodo'] = new Chart(document.getElementById('chart-cot-periodo'), {
    type: 'line',
    data: {
      labels: data.map(d => d.periodo),
      datasets: [{label:'Cotizaciones', data: data.map(d => d.total), borderColor: chartColors.blue, backgroundColor: chartColors.blue+'20', fill: true, tension: .3}]
    },
    options: {responsive:true, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}
  });
}

async function loadOverviewCharts() {
  // Users per week
  const usersData = await fetchJSON(API+'/usuarios-por-periodo?periodo=semana');
  destroyChart('chart-users-week');
  charts['chart-users-week'] = new Chart(document.getElementById('chart-users-week'), {
    type: 'line',
    data: {
      labels: usersData.map(d => d.periodo),
      datasets: [{label:'Usuarios nuevos', data: usersData.map(d => d.total), borderColor: chartColors.green, backgroundColor: chartColors.green+'20', fill: true, tension: .3}]
    },
    options: {responsive:true, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}
  });

  // Orders by status
  const statusData = await fetchJSON(API+'/ordenes-por-status');
  const statusColors = {confirmada:chartColors.blue, preparando:chartColors.orange, en_transito:chartColors.teal, en_obra:chartColors.yellow, entregada:chartColors.green, con_incidencia:chartColors.red, cancelada:chartColors.gray};
  destroyChart('chart-ordenes-status');
  charts['chart-ordenes-status'] = new Chart(document.getElementById('chart-ordenes-status'), {
    type: 'bar',
    data: {
      labels: statusData.map(d => d.status),
      datasets: [{label:'Ordenes', data: statusData.map(d => d.total), backgroundColor: statusData.map(d => statusColors[d.status] || chartColors.gray)}]
    },
    options: {responsive:true, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}
  });

  // Categories donut
  const catData = await fetchJSON(API+'/categorias');
  destroyChart('chart-categorias');
  charts['chart-categorias'] = new Chart(document.getElementById('chart-categorias'), {
    type: 'doughnut',
    data: {
      labels: catData.map(d => d.categoria),
      datasets: [{data: catData.map(d => d.total), backgroundColor: chartColors.palette}]
    },
    options: {responsive:true, plugins:{legend:{position:'right',labels:{boxWidth:12,font:{size:11}}}}}
  });
}

// ============================================================
// PRICING INTELLIGENCE
// ============================================================
async function loadPricing() {
  // KPIs
  const kpis = await fetchJSON(API+'/pricing/kpis');
  renderKPIs('pricing-kpis', [
    {label:'Total datos de precio', value: kpis.total_datos, color:'blue'},
    {label:'Productos trackeados', value: kpis.productos_trackeados, color:''},
    {label:'Proveedores trackeados', value: kpis.proveedores_trackeados, color:''},
  ]);

  // Load catalog dropdown
  const catalogo = await fetchJSON(API+'/pricing/catalogo');
  const sel = document.getElementById('pricing-product-select');
  catalogo.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.nombre + ' (' + p.categoria + ')';
    sel.appendChild(opt);
  });

  // Top products
  const topProd = await fetchJSON(API+'/pricing/top-productos');
  destroyChart('chart-top-productos');
  charts['chart-top-productos'] = new Chart(document.getElementById('chart-top-productos'), {
    type: 'bar',
    data: {
      labels: topProd.map(d => d.producto),
      datasets: [{label:'Cotizaciones', data: topProd.map(d => d.total_cotizaciones), backgroundColor: chartColors.orange}]
    },
    options: {responsive:true, indexAxis:'y', plugins:{legend:{display:false}}, scales:{x:{beginAtZero:true}}}
  });

  // Variaciones heatmap
  const variaciones = await fetchJSON(API+'/pricing/variaciones');
  document.getElementById('pricing-heatmap').innerHTML = variaciones.slice(0, 20).map(v => {
    const cls = v.variacion_pct > 0 ? 'up' : v.variacion_pct < 0 ? 'down' : 'flat';
    const arrow = v.variacion_pct > 0 ? '&#9650; ' : v.variacion_pct < 0 ? '&#9660; ' : '';
    return '<div class="heatmap-card"><div class="product-name">'+v.producto+'</div>' +
      '<div class="price-row">'+(v.precio_actual ? fmtMoney(v.precio_actual) : 'Sin datos')+'</div>' +
      '<div class="variation '+cls+'">'+arrow+v.variacion_pct+'%</div></div>';
  }).join('') || '<p style="color:var(--text-secondary)">Sin datos de variacion</p>';

  // Last 50 prices table
  const ultimos = await fetchJSON(API+'/pricing/ultimos');
  document.getElementById('pricing-table').innerHTML = '<table><thead><tr><th>Producto</th><th>Categoria</th><th>Proveedor</th><th>Precio</th><th>Unidad</th><th>Zona</th><th>Fecha</th></tr></thead><tbody>' +
    ultimos.map(r => '<tr><td>'+r.producto+'</td><td>'+( r.categoria||'-')+'</td><td>'+(r.proveedor||'-')+'</td><td>'+fmtMoney(r.precio_unitario)+'</td><td>'+(r.unidad||'-')+'</td><td>'+(r.zona||'-')+'</td><td>'+fmtDate(r.fecha)+'</td></tr>').join('') +
    '</tbody></table>';
}

async function loadPricingTrend() {
  const catId = document.getElementById('pricing-product-select').value;
  if (!catId) return;
  const data = await fetchJSON(API+'/pricing/tendencia?catalogo_id='+catId);
  destroyChart('chart-price-trend');
  charts['chart-price-trend'] = new Chart(document.getElementById('chart-price-trend'), {
    type: 'line',
    data: {
      labels: data.map(d => d.periodo),
      datasets: [
        {label:'Promedio', data: data.map(d => d.promedio), borderColor: chartColors.blue, backgroundColor: chartColors.blue+'20', fill: true, tension: .3},
        {label:'Min', data: data.map(d => d.minimo), borderColor: chartColors.green, borderDash:[5,5], fill:false, tension:.3},
        {label:'Max', data: data.map(d => d.maximo), borderColor: chartColors.red, borderDash:[5,5], fill:false, tension:.3},
      ]
    },
    options: {responsive:true, scales:{y:{beginAtZero:false}}}
  });
}

// ============================================================
// SUPPLIERS
// ============================================================
async function loadSuppliers() {
  // KPIs
  const kpis = await fetchJSON(API+'/proveedores/kpis');
  renderKPIs('suppliers-kpis', [
    {label:'Proveedores activos', value: kpis.activos, color:'blue'},
    {label:'Tasa de respuesta', value: fmtPct(kpis.tasa_respuesta), color:'green'},
    {label:'Tiempo respuesta promedio', value: kpis.tiempo_respuesta_promedio + ' min', color:'orange'},
  ]);

  // Top calificacion
  const topCal = await fetchJSON(API+'/proveedores/top-calificacion');
  destroyChart('chart-prov-cal');
  charts['chart-prov-cal'] = new Chart(document.getElementById('chart-prov-cal'), {
    type: 'bar',
    data: {
      labels: topCal.map(d => d.nombre),
      datasets: [{label:'Calificacion', data: topCal.map(d => d.calificacion), backgroundColor: chartColors.green}]
    },
    options: {responsive:true, indexAxis:'y', plugins:{legend:{display:false}}, scales:{x:{beginAtZero:true, max:5}}}
  });

  // Top volumen
  const topVol = await fetchJSON(API+'/proveedores/top-volumen');
  destroyChart('chart-prov-vol');
  charts['chart-prov-vol'] = new Chart(document.getElementById('chart-prov-vol'), {
    type: 'bar',
    data: {
      labels: topVol.map(d => d.nombre),
      datasets: [{label:'Ordenes', data: topVol.map(d => d.ordenes), backgroundColor: chartColors.blue}]
    },
    options: {responsive:true, indexAxis:'y', plugins:{legend:{display:false}}, scales:{x:{beginAtZero:true}}}
  });

  // Por tipo (pie)
  const tipoData = await fetchJSON(API+'/proveedores/por-tipo');
  destroyChart('chart-prov-tipo');
  charts['chart-prov-tipo'] = new Chart(document.getElementById('chart-prov-tipo'), {
    type: 'pie',
    data: {
      labels: tipoData.map(d => d.tipo),
      datasets: [{data: tipoData.map(d => d.total), backgroundColor: [chartColors.blue, chartColors.orange, chartColors.green]}]
    },
    options: {responsive:true, plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}}}
  });

  // Table
  const provs = await fetchJSON(API+'/proveedores');
  document.getElementById('suppliers-table').innerHTML = '<table><thead><tr><th>Nombre</th><th>Tipo</th><th>Categorias</th><th>Calificacion</th><th>Pedidos</th><th>Puntualidad</th><th>Cantidad OK</th><th>Tiempo Rta</th><th>Incidencias</th></tr></thead><tbody>' +
    provs.map(p => '<tr><td>'+p.nombre+'</td><td>'+p.tipo+'</td><td>'+(p.categorias||'-')+'</td><td>'+p.calificacion+'</td><td>'+p.total_pedidos+'</td><td>'+p.tasa_puntualidad+'%</td><td>'+p.tasa_cantidad+'%</td><td>'+p.tiempo_respuesta_promedio+' min</td><td>'+p.total_incidencias+'</td></tr>').join('') +
    '</tbody></table>';
}

// ============================================================
// USERS
// ============================================================
async function loadUsers() {
  const kpis = await fetchJSON(API+'/usuarios/kpis');
  renderKPIs('users-kpis', [
    {label:'Total usuarios', value: kpis.total, color:'blue'},
    {label:'Activos ultimo mes', value: kpis.activos_ultimo_mes, color:'green'},
    {label:'Ticket promedio', value: fmtMoney(kpis.ticket_promedio), color:'orange'},
  ]);

  // Registros por semana
  const regData = await fetchJSON(API+'/usuarios-por-periodo?periodo=semana');
  destroyChart('chart-user-reg');
  charts['chart-user-reg'] = new Chart(document.getElementById('chart-user-reg'), {
    type: 'line',
    data: {
      labels: regData.map(d => d.periodo),
      datasets: [{label:'Nuevos usuarios', data: regData.map(d => d.total), borderColor: chartColors.blue, backgroundColor: chartColors.blue+'20', fill: true, tension: .3}]
    },
    options: {responsive:true, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}
  });

  // Top buyers
  const topBuyers = await fetchJSON(API+'/usuarios/top-compradores');
  destroyChart('chart-top-buyers');
  charts['chart-top-buyers'] = new Chart(document.getElementById('chart-top-buyers'), {
    type: 'bar',
    data: {
      labels: topBuyers.map(d => d.nombre),
      datasets: [{label:'Volumen ($)', data: topBuyers.map(d => d.volumen), backgroundColor: chartColors.orange}]
    },
    options: {responsive:true, indexAxis:'y', plugins:{legend:{display:false}}, scales:{x:{beginAtZero:true}}}
  });

  // Table
  const users = await fetchJSON(API+'/usuarios');
  document.getElementById('users-table').innerHTML = '<table><thead><tr><th>Nombre</th><th>Telefono</th><th>Tipo</th><th>Pedidos</th><th>Total gastado</th><th>Registro</th><th>Ultimo pedido</th></tr></thead><tbody>' +
    users.map(u => '<tr><td>'+u.nombre+'</td><td>'+u.telefono+'</td><td>'+u.tipo+'</td><td>'+u.total_pedidos+'</td><td>'+fmtMoney(u.total_gastado)+'</td><td>'+fmtDate(u.created_at)+'</td><td>'+fmtDate(u.ultimo_pedido)+'</td></tr>').join('') +
    '</tbody></table>';
}

// ============================================================
// ORDERS & REVENUE
// ============================================================
async function loadOrders() {
  const kpis = await fetchJSON(API+'/ordenes/kpis');
  renderKPIs('orders-kpis', [
    {label:'Revenue total (2%)', value: fmtMoney(kpis.revenue_total), color:'green'},
    {label:'Revenue este mes', value: fmtMoney(kpis.revenue_mes), color:'green'},
    {label:'Ordenes completadas', value: kpis.completadas, color:'blue'},
    {label:'Con incidencia', value: kpis.con_incidencia, color:'orange'},
    {label:'Ticket promedio', value: fmtMoney(kpis.ticket_promedio), color:''},
  ]);

  // Revenue por mes
  const revData = await fetchJSON(API+'/revenue-por-mes');
  destroyChart('chart-revenue');
  charts['chart-revenue'] = new Chart(document.getElementById('chart-revenue'), {
    type: 'bar',
    data: {
      labels: revData.map(d => d.mes),
      datasets: [{label:'Revenue (2%)', data: revData.map(d => d.revenue), backgroundColor: chartColors.green}]
    },
    options: {responsive:true, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}
  });

  // Ordenes por mes (stacked)
  const mesData = await fetchJSON(API+'/ordenes-por-mes');
  const allStatuses = [...new Set(mesData.flatMap(d => Object.keys(d).filter(k => k !== 'mes')))];
  const sColors = {confirmada:chartColors.blue, preparando:chartColors.orange, en_transito:chartColors.teal, en_obra:chartColors.yellow, entregada:chartColors.green, con_incidencia:chartColors.red, cancelada:chartColors.gray};
  destroyChart('chart-ordenes-mes');
  charts['chart-ordenes-mes'] = new Chart(document.getElementById('chart-ordenes-mes'), {
    type: 'bar',
    data: {
      labels: mesData.map(d => d.mes),
      datasets: allStatuses.map(s => ({
        label: s,
        data: mesData.map(d => d[s] || 0),
        backgroundColor: sColors[s] || chartColors.gray,
      }))
    },
    options: {responsive:true, scales:{x:{stacked:true},y:{stacked:true, beginAtZero:true}}, plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}}}
  });

  // Orders table
  const ordenes = await fetchJSON(API+'/ordenes');
  document.getElementById('orders-table').innerHTML = '<table><thead><tr><th>#</th><th>Status</th><th>Proveedor</th><th>Usuario</th><th>Total</th><th>Municipio</th><th>Fecha</th></tr></thead><tbody>' +
    ordenes.map(o => '<tr><td>'+o.id+'</td><td>'+statusBadge(o.status)+'</td><td>'+o.proveedor+'</td><td>'+o.usuario+'</td><td>'+fmtMoney(o.total)+'</td><td>'+(o.municipio||'-')+'</td><td>'+fmtDate(o.created_at)+'</td></tr>').join('') +
    '</tbody></table>';
}

// ============================================================
// OPERATIONS
// ============================================================
async function loadOperations() {
  const data = await fetchJSON(API+'/operaciones');

  renderKPIs('ops-kpis', [
    {label:'Tasa de incidencias', value: fmtPct(data.kpis.tasa_incidencias), color:'orange'},
    {label:'Tasa respuesta proveedores', value: fmtPct(data.kpis.tasa_respuesta_proveedores), color:'blue'},
    {label:'Solicitudes sin respuesta', value: data.solicitudes_sin_respuesta, color:'orange'},
    {label:'Incidencias abiertas', value: data.incidencias.length, color:'red'},
    {label:'Ordenes activas', value: data.ordenes_activas.length, color:'blue'},
  ]);

  // Incidencias table
  document.getElementById('ops-incidencias').innerHTML = data.incidencias.length ?
    '<table><thead><tr><th>#</th><th>Orden</th><th>Tipo</th><th>Severidad</th><th>Status</th><th>Descripcion</th><th>Fecha</th></tr></thead><tbody>' +
    data.incidencias.map(i => '<tr><td>'+i.id+'</td><td>'+i.orden_id+'</td><td>'+i.tipo+'</td><td>'+severityBadge(i.severidad)+'</td><td>'+statusBadge(i.status)+'</td><td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+(i.descripcion||'-')+'</td><td>'+fmtDate(i.created_at)+'</td></tr>').join('') +
    '</tbody></table>' : '<p style="padding:20px;color:var(--text-secondary)">Sin incidencias abiertas</p>';

  // Ordenes activas table
  document.getElementById('ops-ordenes').innerHTML = data.ordenes_activas.length ?
    '<table><thead><tr><th>#</th><th>Status</th><th>Total</th><th>Municipio</th><th>Fecha</th></tr></thead><tbody>' +
    data.ordenes_activas.map(o => '<tr><td>'+o.id+'</td><td>'+statusBadge(o.status)+'</td><td>'+fmtMoney(o.total)+'</td><td>'+(o.municipio||'-')+'</td><td>'+fmtDate(o.created_at)+'</td></tr>').join('') +
    '</tbody></table>' : '<p style="padding:20px;color:var(--text-secondary)">Sin ordenes activas</p>';

  // Peores proveedores
  document.getElementById('ops-peores').innerHTML = data.peores_proveedores.length ?
    '<table><thead><tr><th>Proveedor</th><th>Calificacion</th><th>Incidencias</th></tr></thead><tbody>' +
    data.peores_proveedores.map(p => '<tr><td>'+p.nombre+'</td><td>'+p.calificacion+'</td><td>'+p.total_incidencias+'</td></tr>').join('') +
    '</tbody></table>' : '<p style="padding:20px;color:var(--text-secondary)">Sin datos</p>';
}

// ============================================================
// CREDITO
// ============================================================
async function loadAprobaciones() {
  tabLoaded['aprobaciones'] = false; // always reload
  const data = await fetchJSON(API+'/aprobaciones');

  renderKPIs('aprobaciones-kpis', [
    {label:'Pendientes', value: data.pendientes || 0, color:'orange'},
    {label:'Aprobadas', value: data.aprobadas || 0, color:'green'},
    {label:'Rechazadas', value: data.rechazadas || 0, color:'red'},
    {label:'Expiradas', value: data.expiradas || 0, color:'gray'},
    {label:'Total', value: data.total || 0, color:'blue'},
  ]);

  // Pendientes list
  let html = '';
  if ((data.lista_pendientes || []).length === 0) {
    html = '<p style="color:#888;padding:20px;text-align:center;">No hay solicitudes pendientes</p>';
  } else {
    html = '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
    html += '<tr style="border-bottom:2px solid #eee;"><th style="text-align:left;padding:8px;">Orden</th><th>Solicitante</th><th>Monto</th><th>Empresa</th><th>Nota</th><th>Creada</th><th>Expira</th><th>Acciones</th></tr>';
    data.lista_pendientes.forEach(a => {
      html += '<tr style="border-bottom:1px solid #f0f0f0;">' +
        '<td style="padding:8px;font-weight:700;">#' + a.orden_id + '</td>' +
        '<td>' + (a.solicitante || '-') + '</td>' +
        '<td style="text-align:right;font-weight:600;">' + fmtMoney(a.monto) + '</td>' +
        '<td>' + (a.empresa || '-') + '</td>' +
        '<td>' + (a.nota || '-') + '</td>' +
        '<td>' + fmtDate(a.created_at) + '</td>' +
        '<td>' + fmtDate(a.expira_at) + '</td>' +
        '<td style="text-align:center;">' +
          '<button onclick="aprobarDesdeUI('+a.id+','+a.orden_id+')" style="background:#27AE60;color:#fff;border:none;border-radius:4px;padding:4px 12px;cursor:pointer;margin-right:4px;">Aprobar</button>' +
          '<button onclick="rechazarDesdeUI('+a.id+','+a.orden_id+')" style="background:#E74C3C;color:#fff;border:none;border-radius:4px;padding:4px 12px;cursor:pointer;">Rechazar</button>' +
        '</td></tr>';
    });
    html += '</table>';
  }
  document.getElementById('aprobaciones-list').innerHTML = html;

  // Historial
  let hhtml = '';
  if ((data.historial || []).length === 0) {
    hhtml = '<p style="color:#888;padding:20px;text-align:center;">Sin historial aun</p>';
  } else {
    hhtml = '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
    hhtml += '<tr style="border-bottom:2px solid #eee;"><th style="text-align:left;padding:8px;">Orden</th><th>Solicitante</th><th>Monto</th><th>Status</th><th>Aprobador</th><th>Nota</th><th>Fecha</th></tr>';
    data.historial.forEach(a => {
      const sColor = a.status === 'aprobada' ? 'green' : a.status === 'rechazada' ? 'red' : 'gray';
      hhtml += '<tr style="border-bottom:1px solid #f0f0f0;">' +
        '<td style="padding:8px;">#' + a.orden_id + '</td>' +
        '<td>' + (a.solicitante || '-') + '</td>' +
        '<td style="text-align:right;">' + fmtMoney(a.monto) + '</td>' +
        '<td><span class="badge badge-'+sColor+'">' + a.status + '</span></td>' +
        '<td>' + (a.aprobador || '-') + '</td>' +
        '<td>' + (a.nota_respuesta || '-') + '</td>' +
        '<td>' + fmtDate(a.updated_at) + '</td></tr>';
    });
    hhtml += '</table>';
  }
  document.getElementById('aprobaciones-historial').innerHTML = hhtml;
}

async function aprobarDesdeUI(aprobacionId, ordenId) {
  if (!confirm('Aprobar orden #' + ordenId + '?')) return;
  const r = await fetch('/aprobaciones/' + aprobacionId + '/aprobar', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({aprobador_id: 1, nota: 'Aprobado desde dashboard'})});
  if (r.ok) { alert('Orden aprobada'); tabLoaded['aprobaciones'] = false; loadAprobaciones(); }
  else alert('Error al aprobar');
}

async function rechazarDesdeUI(aprobacionId, ordenId) {
  const motivo = prompt('Motivo del rechazo:');
  if (!motivo) return;
  const r = await fetch('/aprobaciones/' + aprobacionId + '/rechazar', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({aprobador_id: 1, nota: motivo})});
  if (r.ok) { alert('Orden rechazada'); tabLoaded['aprobaciones'] = false; loadAprobaciones(); }
  else alert('Error al rechazar');
}

async function loadCredito() {
  const stats = await fetchJSON('/credito/stats');
  const ranking = await fetchJSON('/credito/ranking?limit=15');

  renderKPIs('credito-kpis', [
    {label:'Score promedio', value: stats.avg_score?.toFixed(1) || '0', color:'blue'},
    {label:'Usuarios con score', value: stats.con_score || 0, color:''},
    {label:'Elegibles para credito', value: stats.elegibles_credito || 0, color:'green'},
    {label:'Volumen potencial', value: fmtMoney(stats.volumen_potencial), color:'orange'},
    {label:'Dias pago promedio', value: (stats.promedio_dias_pago_global || 0).toFixed(1), color:''},
  ]);

  // Score distribution donut chart
  destroyChart('chart-score-dist');
  const dist = stats.distribution || {};
  charts['chart-score-dist'] = new Chart(document.getElementById('chart-score-dist'), {
    type:'doughnut',
    data:{
      labels:['Excelente (80+)','Bueno (65-79)','Regular (40-64)','Malo (<40)','Sin historial'],
      datasets:[{data:[dist.excelente||0, dist.bueno||0, dist.regular||0, dist.malo||0, dist.sin_historial||0],
        backgroundColor:['#27AE60','#2E86C1','#E67E22','#e74c3c','#ccc']}]
    },
    options:{responsive:true, plugins:{legend:{position:'bottom'}}}
  });

  // Ranking table
  let html = '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
  html += '<tr style="border-bottom:2px solid #eee;"><th style="text-align:left;padding:8px;">Usuario</th><th>Score</th><th>Nivel</th><th>Gastado</th><th>Pedidos</th></tr>';
  (ranking.ranking || []).forEach((u,i) => {
    const color = u.score >= 80 ? '#27AE60' : u.score >= 65 ? '#2E86C1' : u.score >= 40 ? '#E67E22' : '#e74c3c';
    html += '<tr style="border-bottom:1px solid #f0f0f0;">' +
      '<td style="padding:8px;">' + (u.nombre || u.telefono) + '</td>' +
      '<td style="text-align:center;"><span style="color:' + color + ';font-weight:700;">' + (u.score?.toFixed(0)) + '</span></td>' +
      '<td style="text-align:center;">' + u.nivel + '</td>' +
      '<td style="text-align:right;">' + fmtMoney(u.total_gastado) + '</td>' +
      '<td style="text-align:center;">' + u.pedidos_completados + '</td>' +
    '</tr>';
  });
  html += '</table>';
  document.getElementById('credito-ranking').innerHTML = html;
}

// ============================================================
// INIT
// ============================================================
document.getElementById('last-updated').textContent = 'Actualizado: ' + new Date().toLocaleString('es-MX');
loadTab('overview');
</script>
</body>
</html>"""
