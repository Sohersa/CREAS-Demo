"""
Portal de seguimiento — dashboard para clientes y proveedores.
Single-page app con login por telefono, dashboards diferenciados por rol.
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_

from app.database import get_db
from app.services.auth_service import verificar_token
from app.models.usuario import Usuario
from app.models.proveedor import Proveedor
from app.models.orden import Orden
from app.models.pedido import Pedido
from app.models.cotizacion import Cotizacion
from app.models.seguimiento import SeguimientoEntrega
from app.models.incidencia import IncidenciaEntrega
from app.models.calificacion import CalificacionProveedor

router = APIRouter(prefix="/portal", tags=["portal"])


# ─── Pydantic models ───────────────────────────────────────────────

class LoginRequest(BaseModel):
    telefono: str
    nombre: str = ""
    empresa: str = ""


class UpdateStatusRequest(BaseModel):
    status: str
    nota: str = ""
    nombre_chofer: str = ""
    telefono_chofer: str = ""
    placas_vehiculo: str = ""
    tipo_vehiculo: str = ""


# ─── API: Login / identify ─────────────────────────────────────────

@router.post("/api/login")
def portal_login(body: LoginRequest, db: Session = Depends(get_db)):
    telefono = body.telefono.strip().replace(" ", "")
    # Check if supplier
    proveedor = db.query(Proveedor).filter(
        Proveedor.telefono_whatsapp == telefono,
        Proveedor.activo == True
    ).first()
    if proveedor:
        return {
            "rol": "proveedor",
            "id": proveedor.id,
            "nombre": proveedor.nombre,
            "telefono": telefono,
        }
    # Check if client
    usuario = db.query(Usuario).filter(Usuario.telefono == telefono).first()
    nombre = body.nombre.strip() if body.nombre else ""
    empresa = body.empresa.strip() if body.empresa else ""
    if not usuario:
        # Auto-registrar como cliente nuevo
        usuario = Usuario(
            telefono=telefono,
            nombre=nombre or "Cliente",
            empresa=empresa or None,
            tipo="residente",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    else:
        # Actualizar nombre/empresa si los mandaron
        if nombre and nombre != usuario.nombre:
            usuario.nombre = nombre
        if empresa and empresa != usuario.empresa:
            usuario.empresa = empresa
        db.commit()
        db.refresh(usuario)
    return {
        "rol": "cliente",
        "id": usuario.id,
        "nombre": usuario.nombre or "Cliente",
        "telefono": telefono,
    }


@router.post("/api/login-token")
def portal_login_token(db: Session = Depends(get_db), authorization: str = Header("")):
    """Login al portal usando JWT token de OAuth/registro."""
    token = authorization.replace("Bearer ", "")
    payload = verificar_token(token)
    if not payload:
        return {"ok": False, "error": "Token invalido o expirado."}

    user_id = int(payload.get("sub", 0))
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        return {"ok": False, "error": "Usuario no encontrado."}

    # Check if they're also a provider
    if usuario.telefono:
        proveedor = db.query(Proveedor).filter(
            Proveedor.telefono_whatsapp == usuario.telefono,
            Proveedor.activo == True
        ).first()
        if proveedor:
            return {
                "ok": True,
                "rol": "proveedor",
                "id": proveedor.id,
                "nombre": proveedor.nombre,
                "telefono": usuario.telefono,
            }

    return {
        "ok": True,
        "rol": "cliente",
        "id": usuario.id,
        "nombre": usuario.nombre or "Cliente",
        "telefono": usuario.telefono or "",
    }


# ─── API: Client endpoints ─────────────────────────────────────────

@router.get("/api/cliente/{usuario_id}/ordenes")
def cliente_ordenes(usuario_id: int, status: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(Orden).filter(Orden.usuario_id == usuario_id)
    if status == "activas":
        q = q.filter(Orden.status.in_(["confirmada", "preparando", "en_transito", "en_obra"]))
    elif status == "historial":
        q = q.filter(Orden.status.in_(["entregada", "cancelada"]))
    elif status:
        q = q.filter(Orden.status == status)
    ordenes = q.order_by(Orden.created_at.desc()).all()
    resultado = []
    for o in ordenes:
        proveedor = db.query(Proveedor).filter(Proveedor.id == o.proveedor_id).first()
        resultado.append({
            "id": o.id,
            "pedido_id": o.pedido_id,
            "status": o.status,
            "items": json.loads(o.items) if o.items else [],
            "total": o.total,
            "direccion_entrega": o.direccion_entrega,
            "municipio_entrega": o.municipio_entrega,
            "proveedor_nombre": proveedor.nombre if proveedor else "N/A",
            "proveedor_telefono": proveedor.telefono_whatsapp if proveedor else "",
            "nombre_chofer": o.nombre_chofer,
            "telefono_chofer": o.telefono_chofer,
            "placas_vehiculo": o.placas_vehiculo,
            "tipo_vehiculo": o.tipo_vehiculo,
            "fecha_entrega_prometida": o.fecha_entrega_prometida.isoformat() if o.fecha_entrega_prometida else None,
            "fecha_entrega_real": o.fecha_entrega_real.isoformat() if o.fecha_entrega_real else None,
            "confirmada_at": o.confirmada_at.isoformat() if o.confirmada_at else None,
            "preparando_at": o.preparando_at.isoformat() if o.preparando_at else None,
            "en_transito_at": o.en_transito_at.isoformat() if o.en_transito_at else None,
            "en_obra_at": o.en_obra_at.isoformat() if o.en_obra_at else None,
            "entregada_at": o.entregada_at.isoformat() if o.entregada_at else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "pagado": o.pagado or False,
            "metodo_pago": o.metodo_pago,
            "fecha_pago": o.fecha_pago.isoformat() if o.fecha_pago else None,
        })
    return resultado


@router.get("/api/cliente/{usuario_id}/resumen")
def cliente_resumen(usuario_id: int, db: Session = Depends(get_db)):
    ordenes = db.query(Orden).filter(Orden.usuario_id == usuario_id).all()
    total_gastado = sum(o.total or 0 for o in ordenes)
    total_ordenes = len(ordenes)
    promedio = total_gastado / total_ordenes if total_ordenes else 0
    activas = sum(1 for o in ordenes if o.status in ["confirmada", "preparando", "en_transito", "en_obra"])
    completadas = sum(1 for o in ordenes if o.status == "entregada")
    # Breakdown by material type from items
    material_totals = {}
    for o in ordenes:
        if o.items:
            try:
                items = json.loads(o.items)
                for item in items:
                    cat = item.get("categoria", item.get("material", "Otros"))
                    material_totals[cat] = material_totals.get(cat, 0) + (item.get("subtotal", 0) or 0)
            except (json.JSONDecodeError, TypeError):
                pass
    return {
        "total_gastado": round(total_gastado, 2),
        "total_ordenes": total_ordenes,
        "promedio_por_orden": round(promedio, 2),
        "ordenes_activas": activas,
        "ordenes_completadas": completadas,
        "desglose_material": material_totals,
    }


@router.get("/api/cliente/{usuario_id}/calificaciones")
def cliente_calificaciones(usuario_id: int, db: Session = Depends(get_db)):
    cals = db.query(CalificacionProveedor).filter(
        CalificacionProveedor.usuario_id == usuario_id
    ).order_by(CalificacionProveedor.created_at.desc()).all()
    resultado = []
    for c in cals:
        proveedor = db.query(Proveedor).filter(Proveedor.id == c.proveedor_id).first()
        resultado.append({
            "id": c.id,
            "orden_id": c.orden_id,
            "proveedor_nombre": proveedor.nombre if proveedor else "N/A",
            "puntualidad": c.puntualidad,
            "cantidad_correcta": c.cantidad_correcta,
            "especificacion_correcta": c.especificacion_correcta,
            "sin_incidencias": c.sin_incidencias,
            "calificacion_total": c.calificacion_total,
            "comentario_usuario": c.comentario_usuario,
            "estrellas_usuario": c.estrellas_usuario,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return resultado


# ─── API: Supplier endpoints ───────────────────────────────────────

@router.get("/api/proveedor/{proveedor_id}/ordenes")
def proveedor_ordenes(proveedor_id: int, status: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(Orden).filter(Orden.proveedor_id == proveedor_id)
    if status == "activas":
        q = q.filter(Orden.status.in_(["confirmada", "preparando", "en_transito", "en_obra"]))
    elif status == "historial":
        q = q.filter(Orden.status.in_(["entregada", "cancelada"]))
    elif status:
        q = q.filter(Orden.status == status)
    ordenes = q.order_by(Orden.created_at.desc()).all()
    resultado = []
    for o in ordenes:
        usuario = db.query(Usuario).filter(Usuario.id == o.usuario_id).first()
        resultado.append({
            "id": o.id,
            "pedido_id": o.pedido_id,
            "status": o.status,
            "items": json.loads(o.items) if o.items else [],
            "total": o.total,
            "direccion_entrega": o.direccion_entrega,
            "municipio_entrega": o.municipio_entrega,
            "cliente_nombre": usuario.nombre if usuario else "Cliente",
            "cliente_telefono": usuario.telefono if usuario else "",
            "nombre_chofer": o.nombre_chofer,
            "telefono_chofer": o.telefono_chofer,
            "placas_vehiculo": o.placas_vehiculo,
            "tipo_vehiculo": o.tipo_vehiculo,
            "fecha_entrega_prometida": o.fecha_entrega_prometida.isoformat() if o.fecha_entrega_prometida else None,
            "confirmada_at": o.confirmada_at.isoformat() if o.confirmada_at else None,
            "preparando_at": o.preparando_at.isoformat() if o.preparando_at else None,
            "en_transito_at": o.en_transito_at.isoformat() if o.en_transito_at else None,
            "en_obra_at": o.en_obra_at.isoformat() if o.en_obra_at else None,
            "entregada_at": o.entregada_at.isoformat() if o.entregada_at else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "pagado": o.pagado or False,
            "metodo_pago": o.metodo_pago,
            "fecha_pago": o.fecha_pago.isoformat() if o.fecha_pago else None,
        })
    return resultado


@router.post("/api/proveedor/{proveedor_id}/ordenes/{orden_id}/status")
def proveedor_update_status(
    proveedor_id: int, orden_id: int,
    body: UpdateStatusRequest, db: Session = Depends(get_db)
):
    orden = db.query(Orden).filter(
        Orden.id == orden_id, Orden.proveedor_id == proveedor_id
    ).first()
    if not orden:
        return {"error": "Orden no encontrada"}

    valid_transitions = {
        "confirmada": ["preparando"],
        "preparando": ["en_transito"],
        "en_transito": ["en_obra"],
        "en_obra": ["entregada"],
    }
    if body.status not in valid_transitions.get(orden.status, []):
        return {"error": f"No se puede cambiar de {orden.status} a {body.status}"}

    old_status = orden.status
    orden.status = body.status
    now = datetime.utcnow()

    if body.status == "preparando":
        orden.preparando_at = now
    elif body.status == "en_transito":
        orden.en_transito_at = now
        if body.nombre_chofer:
            orden.nombre_chofer = body.nombre_chofer
        if body.telefono_chofer:
            orden.telefono_chofer = body.telefono_chofer
        if body.placas_vehiculo:
            orden.placas_vehiculo = body.placas_vehiculo
        if body.tipo_vehiculo:
            orden.tipo_vehiculo = body.tipo_vehiculo
    elif body.status == "en_obra":
        orden.en_obra_at = now
    elif body.status == "entregada":
        orden.entregada_at = now
        orden.fecha_entrega_real = now
        if orden.en_transito_at:
            delta = now - orden.en_transito_at
            orden.tiempo_entrega_minutos = int(delta.total_seconds() / 60)

    # Add tracking entry
    seg = SeguimientoEntrega(
        orden_id=orden.id,
        status_anterior=old_status,
        status_nuevo=body.status,
        origen="proveedor",
        nota=body.nota or None,
    )
    db.add(seg)
    db.commit()
    return {"ok": True, "status": orden.status}


@router.get("/api/proveedor/{proveedor_id}/metricas")
def proveedor_metricas(proveedor_id: int, db: Session = Depends(get_db)):
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return {"error": "Proveedor no encontrado"}

    ordenes = db.query(Orden).filter(Orden.proveedor_id == proveedor_id).all()
    total = len(ordenes)
    completadas = sum(1 for o in ordenes if o.status == "entregada")
    activas = sum(1 for o in ordenes if o.status in ["confirmada", "preparando", "en_transito", "en_obra"])
    ingresos_total = sum(o.total or 0 for o in ordenes if o.status == "entregada")
    ingresos_pendiente = sum(o.total or 0 for o in ordenes if o.status in ["confirmada", "preparando", "en_transito", "en_obra"])

    # On-time percentage
    a_tiempo = 0
    con_fecha = 0
    for o in ordenes:
        if o.status == "entregada" and o.fecha_entrega_prometida and o.fecha_entrega_real:
            con_fecha += 1
            if o.fecha_entrega_real <= o.fecha_entrega_prometida:
                a_tiempo += 1
    puntualidad_pct = round((a_tiempo / con_fecha * 100), 1) if con_fecha else 100.0

    incidencias = db.query(IncidenciaEntrega).filter(
        IncidenciaEntrega.proveedor_id == proveedor_id
    ).count()

    return {
        "nombre": proveedor.nombre,
        "calificacion": proveedor.calificacion,
        "total_ordenes": total,
        "ordenes_completadas": completadas,
        "ordenes_activas": activas,
        "ingresos_total": round(ingresos_total, 2),
        "ingresos_pendiente": round(ingresos_pendiente, 2),
        "puntualidad_porcentaje": puntualidad_pct,
        "total_incidencias": incidencias,
        "tasa_puntualidad": proveedor.tasa_puntualidad,
        "tasa_cantidad_correcta": proveedor.tasa_cantidad_correcta,
        "tasa_especificacion_correcta": proveedor.tasa_especificacion_correcta,
    }


@router.get("/api/proveedor/{proveedor_id}/calificaciones")
def proveedor_calificaciones(proveedor_id: int, db: Session = Depends(get_db)):
    cals = db.query(CalificacionProveedor).filter(
        CalificacionProveedor.proveedor_id == proveedor_id
    ).order_by(CalificacionProveedor.created_at.desc()).all()
    resultado = []
    for c in cals:
        resultado.append({
            "id": c.id,
            "orden_id": c.orden_id,
            "puntualidad": c.puntualidad,
            "cantidad_correcta": c.cantidad_correcta,
            "especificacion_correcta": c.especificacion_correcta,
            "sin_incidencias": c.sin_incidencias,
            "calificacion_total": c.calificacion_total,
            "comentario_usuario": c.comentario_usuario,
            "estrellas_usuario": c.estrellas_usuario,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return resultado


# ─── API: Shared - timeline ────────────────────────────────────────

@router.get("/api/orden/{orden_id}/timeline")
def orden_timeline(orden_id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        return {"error": "Orden no encontrada"}
    seguimientos = db.query(SeguimientoEntrega).filter(
        SeguimientoEntrega.orden_id == orden_id
    ).order_by(SeguimientoEntrega.created_at.asc()).all()

    steps = []
    # Always start with confirmada
    steps.append({
        "status": "confirmada",
        "label": "Confirmada",
        "timestamp": orden.confirmada_at.isoformat() if orden.confirmada_at else None,
        "completed": orden.confirmada_at is not None,
    })
    for s_name, s_label, s_field in [
        ("preparando", "Preparando", "preparando_at"),
        ("en_transito", "En transito", "en_transito_at"),
        ("en_obra", "En obra", "en_obra_at"),
        ("entregada", "Entregada", "entregada_at"),
    ]:
        ts = getattr(orden, s_field, None)
        steps.append({
            "status": s_name,
            "label": s_label,
            "timestamp": ts.isoformat() if ts else None,
            "completed": ts is not None,
        })

    events = []
    for seg in seguimientos:
        events.append({
            "de": seg.status_anterior,
            "a": seg.status_nuevo,
            "origen": seg.origen,
            "nota": seg.nota,
            "timestamp": seg.created_at.isoformat() if seg.created_at else None,
        })

    return {"steps": steps, "events": events, "current_status": orden.status}


# ─── HTML: Portal SPA ──────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def portal_page():
    return PORTAL_HTML


PORTAL_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ObraYa - Portal de Seguimiento</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ─── Reset & base ─── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', sans-serif;
  background: #F0F2F5;
  color: #1A1A2E;
  min-height: 100vh;
}
a { color: inherit; text-decoration: none; }
button { cursor: pointer; font-family: inherit; }
input, select { font-family: inherit; }

/* ─── Colors ─── */
:root {
  --navy: #0F1B2D;
  --navy-light: #1A2942;
  --orange: #E67E22;
  --orange-hover: #CF6D17;
  --blue: #2E86C1;
  --green: #27AE60;
  --red: #E74C3C;
  --gray-50: #F8F9FA;
  --gray-100: #F0F2F5;
  --gray-200: #E2E6EA;
  --gray-300: #CED4DA;
  --gray-400: #ADB5BD;
  --gray-500: #6C757D;
  --gray-700: #495057;
  --gray-900: #1A1A2E;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
  --radius: 8px;
  --radius-lg: 12px;
}

/* ─── Utility ─── */
.hidden { display: none !important; }

/* ─── Login screen ─── */
#login-screen {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--navy) 0%, #1a3a5c 100%);
}
.login-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 48px 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: var(--shadow-lg);
  text-align: center;
}
.login-card h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 4px;
}
.login-card .subtitle {
  color: var(--gray-500);
  font-size: 14px;
  margin-bottom: 32px;
}
.login-card .logo-text {
  font-size: 32px;
  font-weight: 700;
  color: var(--orange);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}
.form-group {
  text-align: left;
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: 6px;
}
.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1.5px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 15px;
  transition: border-color 0.2s;
  outline: none;
}
.form-group input:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px rgba(46,134,193,0.15);
}
.btn-primary {
  width: 100%;
  padding: 12px;
  background: var(--orange);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 600;
  transition: background 0.2s;
}
.btn-primary:hover { background: var(--orange-hover); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.phone-row { display: flex; gap: 8px; }
.phone-country {
  width: 120px; flex-shrink: 0; padding: 12px 8px; border: 1.5px solid var(--gray-300);
  border-radius: var(--radius); font-size: 13px; font-family: inherit; background: #fff;
  cursor: pointer;
}
.phone-country:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 3px rgba(46,134,193,0.15); }
.phone-input {
  flex: 1; min-width: 0; padding: 12px 14px; border: 1.5px solid var(--gray-300);
  border-radius: var(--radius); font-size: 15px; font-family: inherit;
}
.phone-input:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 3px rgba(46,134,193,0.15); }
.login-error {
  color: var(--red);
  font-size: 13px;
  margin-top: 12px;
  min-height: 20px;
}

/* ─── App shell ─── */
#app-shell { display: flex; min-height: 100vh; }

/* Sidebar */
.sidebar {
  width: 260px;
  background: var(--navy);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  transition: transform 0.3s;
}
.sidebar-header {
  padding: 24px 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.sidebar-header .brand {
  font-size: 22px;
  font-weight: 700;
  color: var(--orange);
  letter-spacing: -0.5px;
}
.sidebar-header .user-info {
  margin-top: 12px;
  font-size: 13px;
  color: rgba(255,255,255,0.7);
}
.sidebar-header .user-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}
.sidebar-header .user-role {
  display: inline-block;
  margin-top: 4px;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.role-cliente { background: rgba(46,134,193,0.25); color: #7EC8E3; }
.role-proveedor { background: rgba(39,174,96,0.25); color: #7DCEA0; }

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 20px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255,255,255,0.65);
  cursor: pointer;
  transition: all 0.15s;
  border-left: 3px solid transparent;
}
.nav-item:hover {
  color: #fff;
  background: rgba(255,255,255,0.06);
}
.nav-item.active {
  color: #fff;
  background: rgba(255,255,255,0.1);
  border-left-color: var(--orange);
}
.nav-item .nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.nav-item .nav-icon svg {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.btn-logout {
  width: 100%;
  padding: 9px;
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.7);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.btn-logout:hover {
  background: rgba(255,255,255,0.15);
  color: #fff;
}

/* Main content */
.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 32px;
  min-height: 100vh;
}
.page-header {
  margin-bottom: 28px;
}
.page-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--gray-900);
}
.page-header .page-desc {
  font-size: 14px;
  color: var(--gray-500);
  margin-top: 4px;
}

/* ─── Cards / Stats ─── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}
.stat-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--gray-200);
}
.stat-card .stat-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.stat-card .stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-900);
}
.stat-card .stat-sub {
  font-size: 12px;
  color: var(--gray-500);
  margin-top: 4px;
}
.stat-card.accent-orange { border-top: 3px solid var(--orange); }
.stat-card.accent-blue { border-top: 3px solid var(--blue); }
.stat-card.accent-green { border-top: 3px solid var(--green); }
.stat-card.accent-red { border-top: 3px solid var(--red); }

/* ─── Table card ─── */
.card {
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--gray-200);
  margin-bottom: 24px;
  overflow: hidden;
}
.card-header {
  padding: 18px 24px;
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-900);
}
.card-body { padding: 0; }
.card-body.padded { padding: 24px; }

table {
  width: 100%;
  border-collapse: collapse;
}
table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
}
table td {
  padding: 14px 16px;
  font-size: 14px;
  border-bottom: 1px solid var(--gray-100);
  vertical-align: middle;
}
table tr:last-child td { border-bottom: none; }
table tr:hover { background: var(--gray-50); }
table tr { cursor: pointer; }

/* ─── Status badges ─── */
.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.badge-confirmada { background: #EBF5FB; color: #2E86C1; }
.badge-preparando { background: #FEF5E7; color: #E67E22; }
.badge-en_transito { background: #F4ECF7; color: #8E44AD; }
.badge-en_obra { background: #E8F8F5; color: #1ABC9C; }
.badge-entregada { background: #EAFAF1; color: #27AE60; }
.badge-cancelada { background: #FDEDEC; color: #E74C3C; }
.badge-con_incidencia { background: #FDEDEC; color: #E74C3C; }
.badge-pagado { background: #EAFAF1; color: #27AE60; }
.badge-pendiente { background: #FEF5E7; color: #E67E22; }
.badge-en_proceso { background: #EBF5FB; color: #2E86C1; }

/* ─── Timeline ─── */
.timeline {
  position: relative;
  padding: 0 0 0 32px;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: var(--gray-200);
}
.timeline-step {
  position: relative;
  padding-bottom: 24px;
}
.timeline-step:last-child { padding-bottom: 0; }
.timeline-dot {
  position: absolute;
  left: -32px;
  top: 2px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--gray-200);
  border: 3px solid #fff;
  box-shadow: 0 0 0 2px var(--gray-200);
}
.timeline-dot.completed {
  background: var(--green);
  box-shadow: 0 0 0 2px var(--green);
}
.timeline-dot.current {
  background: var(--orange);
  box-shadow: 0 0 0 2px var(--orange);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 2px var(--orange); }
  50% { box-shadow: 0 0 0 6px rgba(230,126,34,0.25); }
}
.timeline-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-900);
}
.timeline-label.pending { color: var(--gray-400); }
.timeline-time {
  font-size: 12px;
  color: var(--gray-500);
  margin-top: 2px;
}

/* ─── Rating dots ─── */
.rating-dots {
  display: inline-flex;
  gap: 3px;
}
.rating-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--gray-200);
}
.rating-dot.filled { background: var(--orange); }

/* ─── Order detail panel ─── */
.detail-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 260px;
  background: rgba(0,0,0,0.3);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
}
.detail-panel {
  width: 560px;
  max-width: 100%;
  background: #fff;
  height: 100%;
  overflow-y: auto;
  box-shadow: -4px 0 24px rgba(0,0,0,0.15);
  animation: slideIn 0.25s ease;
}
@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
.detail-header {
  padding: 24px;
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
}
.detail-header h3 { font-size: 18px; font-weight: 700; }
.detail-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--gray-500);
  transition: background 0.15s;
}
.detail-close:hover { background: var(--gray-200); }
.detail-body { padding: 24px; }
.detail-section {
  margin-bottom: 28px;
}
.detail-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 14px;
}
.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
  border-bottom: 1px solid var(--gray-100);
}
.detail-row:last-child { border-bottom: none; }
.detail-row .label { color: var(--gray-500); }
.detail-row .value { font-weight: 500; color: var(--gray-900); }

/* ─── Payment card ─── */
.payment-breakdown {
  background: var(--gray-50);
  border-radius: var(--radius);
  padding: 16px;
  margin-top: 12px;
}
.payment-line {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
}
.payment-line.total {
  border-top: 2px solid var(--gray-200);
  margin-top: 8px;
  padding-top: 10px;
  font-weight: 700;
}
.payment-line .commission { color: var(--gray-500); font-size: 12px; }

.btn-pay {
  display: inline-block;
  margin-top: 12px;
  padding: 10px 24px;
  background: var(--green);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  transition: background 0.2s;
}
.btn-pay:hover { background: #219A52; }
.btn-pay:disabled { opacity: 0.5; cursor: not-allowed; }

/* ─── Supplier action buttons ─── */
.btn-action {
  padding: 8px 20px;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 600;
  transition: background 0.2s;
}
.btn-action:hover { background: #2471A3; }
.btn-action.btn-sm { padding: 6px 14px; font-size: 12px; }

/* ─── Transport form ─── */
.transport-form {
  background: var(--gray-50);
  border-radius: var(--radius);
  padding: 16px;
  margin-top: 12px;
}
.transport-form .form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
.transport-form input, .transport-form select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 13px;
  outline: none;
}
.transport-form input:focus, .transport-form select:focus {
  border-color: var(--blue);
}

/* ─── Metric bars ─── */
.metric-bar-container {
  margin-bottom: 16px;
}
.metric-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
}
.metric-bar-label .name { font-weight: 500; color: var(--gray-700); }
.metric-bar-label .val { font-weight: 600; color: var(--gray-900); }
.metric-bar {
  height: 8px;
  background: var(--gray-200);
  border-radius: 4px;
  overflow: hidden;
}
.metric-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}
.metric-bar-fill.green { background: var(--green); }
.metric-bar-fill.blue { background: var(--blue); }
.metric-bar-fill.orange { background: var(--orange); }

/* ─── Empty state ─── */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--gray-500);
}
.empty-state .empty-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  stroke: var(--gray-300);
  fill: none;
  stroke-width: 1.5;
}
.empty-state p { font-size: 14px; }

/* ─── Tabs ─── */
.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--gray-200);
  margin-bottom: 20px;
}
.tab-btn {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-500);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}
.tab-btn:hover { color: var(--gray-900); }
.tab-btn.active {
  color: var(--orange);
  border-bottom-color: var(--orange);
}

/* ─── Mobile hamburger ─── */
.hamburger {
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 300;
  width: 40px;
  height: 40px;
  background: var(--navy);
  border: none;
  border-radius: var(--radius);
  color: #fff;
  font-size: 20px;
  align-items: center;
  justify-content: center;
}

/* ─── Table scroll wrapper ─── */
.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* ─── Mobile overlay backdrop ─── */
.sidebar-backdrop {
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 99;
}
.sidebar-backdrop.show { display: block; }

/* ─── Responsive ─── */
@media (max-width: 768px) {
  .hamburger { display: flex; }
  .sidebar { transform: translateX(-100%); }
  .sidebar.open { transform: translateX(0); }
  .sidebar-backdrop.show { display: block; }
  .main-content { margin-left: 0; padding: 72px 16px 24px; }
  .detail-overlay { left: 0; }
  .detail-panel { width: 100%; }
  .stats-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
  .stat-card { padding: 16px; }
  .stat-card .stat-value { font-size: 22px; }
  .stat-card .stat-label { font-size: 11px; }
  .transport-form .form-row { grid-template-columns: 1fr; }
  .login-card { margin: 16px; padding: 32px 24px; }
  .login-card h1 { font-size: 22px; }
  .login-card .logo-text { font-size: 28px; }
  .page-header h2 { font-size: 20px; }
  .page-header .page-desc { font-size: 13px; }
  .card-header { padding: 14px 16px; }
  .card-header h3 { font-size: 14px; }
  table th { padding: 10px 12px; font-size: 11px; white-space: nowrap; }
  table td { padding: 12px; font-size: 13px; }
  .badge { font-size: 11px; padding: 3px 10px; white-space: nowrap; }
  .btn-action, .btn-action.btn-sm { min-height: 44px; min-width: 44px; padding: 10px 16px; font-size: 13px; }
  .btn-primary { min-height: 48px; font-size: 16px; }
  .btn-logout { min-height: 44px; }
  .btn-pay { min-height: 44px; }
  .nav-item { padding: 14px 20px; min-height: 48px; }
  .detail-close { width: 44px; height: 44px; font-size: 22px; }
  .detail-header { padding: 16px; }
  .detail-header h3 { font-size: 16px; }
  .detail-body { padding: 16px; }
  .detail-section h4 { font-size: 12px; }
  .detail-row { font-size: 13px; flex-wrap: wrap; gap: 4px; }
  .form-group input, .phone-country { min-height: 44px; font-size: 16px; }
  .transport-form input, .transport-form select { min-height: 44px; font-size: 14px; }
}
@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr; }
  .stat-card .stat-value { font-size: 24px; }
  .detail-row { flex-direction: column; gap: 2px; }
  .detail-row .label { font-size: 12px; }
  .detail-row .value { font-size: 14px; }
}

/* ─── Loading spinner ─── */
.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid var(--gray-200);
  border-top-color: var(--orange);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-center {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  gap: 12px;
  color: var(--gray-500);
  font-size: 14px;
}

/* ─── Catalogo / Nuevo Pedido ─── */
.cat-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--gray-200);
  background: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
}
.cat-btn:hover { border-color: var(--orange); color: var(--orange); }
.cat-btn.active { background: var(--orange); color: #fff; border-color: var(--orange); }
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-top: 16px;
}
.product-card {
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: box-shadow .15s;
}
.product-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.product-cat { font-size: 11px; text-transform: uppercase; color: var(--gray-500); letter-spacing: .5px; }
.product-name { font-weight: 600; font-size: 15px; color: var(--gray-800); }
.product-unit { font-size: 13px; color: var(--gray-500); }
.product-price { font-size: 13px; color: var(--green); font-weight: 500; }
.btn-add {
  margin-top: auto;
  padding: 8px;
  border-radius: var(--radius);
  border: 1px solid var(--orange);
  background: #fff;
  color: var(--orange);
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: all .15s;
}
.btn-add:hover { background: var(--orange); color: #fff; }
.btn-added {
  margin-top: auto;
  padding: 8px;
  border-radius: var(--radius);
  border: 1px solid var(--gray-200);
  background: var(--gray-50);
  color: var(--gray-500);
  font-size: 13px;
  cursor: default;
}

/* ─── Search bar ─── */
.search-bar {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color .15s;
}
.search-bar:focus { border-color: var(--orange); }

/* ─── Cotizaciones / Comparativa ─── */
.cot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
}
.cot-card {
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  overflow: hidden;
  transition: box-shadow .15s;
}
.cot-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.cot-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
}
.cot-rank {
  background: var(--orange);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 10px;
}
.cot-name { font-weight: 600; flex: 1; }
.cot-rating { font-size: 13px; color: var(--gray-500); }
.cot-items { padding: 12px 16px; font-size: 13px; }
.cot-items div { padding: 4px 0; border-bottom: 1px solid var(--gray-100); }
.cot-items div:last-child { border-bottom: none; }
.cot-totals {
  padding: 12px 16px;
  border-top: 1px solid var(--gray-200);
  font-size: 14px;
}
.cot-totals div { display: flex; justify-content: space-between; padding: 3px 0; }
.cot-totals .total-line { font-weight: 700; font-size: 16px; color: var(--orange); }

/* ─── Btn small variant ─── */
.btn-sm {
  padding: 6px 14px;
  font-size: 12px;
  border-radius: var(--radius);
  border: 1px solid var(--gray-200);
  background: #fff;
  cursor: pointer;
  transition: all .15s;
}
.btn-sm:hover { border-color: var(--orange); color: var(--orange); }

/* ─── Cart badge ─── */
.cart-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--red);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

/* ─── Subtitle ─── */
.subtitle { font-size: 14px; color: var(--gray-500); margin-top: 4px; }

/* ─── Responsive adjustments for new components ─── */
@media (max-width: 768px) {
  .product-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
  .product-card { padding: 12px; }
  .cot-grid { grid-template-columns: 1fr; }
  .cat-btn { padding: 8px 12px; font-size: 12px; }
  .btn-add, .btn-added { min-height: 44px; }
  .btn-sm { min-height: 44px; min-width: 44px; padding: 10px 14px; }
}

/* Tabs */
.tabs { display: flex; gap: 0; border-bottom: 2px solid #E5E7EB; margin-bottom: 16px; overflow-x: auto; }
.tab-btn {
  padding: 10px 18px; border: none; background: none; cursor: pointer;
  font-size: 14px; font-weight: 500; color: #6B7280; white-space: nowrap;
  border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all .2s;
}
.tab-btn:hover { color: #374151; }
.tab-btn.active { color: #F97316; border-bottom-color: #F97316; }
</style>
</head>
<body>

<!-- ── Login Screen ── -->
<div id="login-screen">
  <div class="login-card">
    <div class="logo-text">ObraYa</div>
    <h1>Portal de Seguimiento</h1>
    <p class="subtitle">Ingresa tus datos para acceder. Si es tu primera vez, te registraremos automaticamente.</p>
    <div class="form-group">
      <label>Tu nombre</label>
      <input type="text" id="login-name" placeholder="Ej. Juan Rodriguez" autocomplete="name">
    </div>
    <div class="form-group">
      <label>Empresa u obra (opcional)</label>
      <input type="text" id="login-empresa" placeholder="Ej. Constructora del Valle" autocomplete="organization">
    </div>
    <div class="form-group">
      <label>Numero de WhatsApp (10 digitos)</label>
      <div class="phone-row">
        <select class="phone-country" id="login-country-code">
          <option value="+52">&#127474;&#127485; +52</option>
          <option value="+1">&#127482;&#127480; +1</option>
          <option value="+57">&#127464;&#127476; +57</option>
          <option value="+56">&#127464;&#127473; +56</option>
          <option value="+54">&#127462;&#127479; +54</option>
          <option value="+55">&#127463;&#127479; +55</option>
          <option value="+51">&#127477;&#127466; +51</option>
          <option value="+593">&#127466;&#127464; +593</option>
          <option value="+58">&#127483;&#127466; +58</option>
          <option value="+506">&#127464;&#127479; +506</option>
          <option value="+502">&#127468;&#127481; +502</option>
          <option value="+503">&#127480;&#127483; +503</option>
          <option value="+504">&#127469;&#127475; +504</option>
          <option value="+505">&#127475;&#127470; +505</option>
          <option value="+507">&#127477;&#127462; +507</option>
          <option value="+591">&#127463;&#127476; +591</option>
          <option value="+595">&#127477;&#127486; +595</option>
          <option value="+598">&#127482;&#127486; +598</option>
          <option value="+34">&#127466;&#127480; +34</option>
        </select>
        <input type="tel" id="login-phone" placeholder="33 1234 5678" class="phone-input" autocomplete="tel">
      </div>
    </div>
    <button class="btn-primary" id="login-btn" onclick="doLogin()">Entrar al Portal</button>
    <div class="login-error" id="login-error"></div>
  </div>
</div>

<!-- ── App Shell ── -->
<div id="app-shell" class="hidden">
  <div class="sidebar-backdrop" id="sidebar-backdrop" onclick="closeSidebar()"></div>
  <button class="hamburger" onclick="toggleSidebar()">
    <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" fill="none" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  </button>

  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="brand">ObraYa</div>
      <div class="user-info">
        <div class="user-name" id="sidebar-name"></div>
        <span class="user-role" id="sidebar-role"></span>
      </div>
    </div>
    <nav class="sidebar-nav" id="sidebar-nav"></nav>
    <div class="sidebar-footer">
      <button class="btn-logout" onclick="doLogout()">Cerrar sesion</button>
    </div>
  </aside>

  <main class="main-content" id="main-content"></main>
</div>

<!-- ── Detail overlay ── -->
<div id="detail-overlay" class="detail-overlay hidden" onclick="closeDetailIfOutside(event)">
  <div class="detail-panel" id="detail-panel"></div>
</div>

<script>
/* ─── State ─── */
let currentUser = null;  // {rol, id, nombre, telefono}
let currentView = null;
let ordersCache = [];
let cart = JSON.parse(localStorage.getItem('obraya_cart') || '[]');
let activePedidoId = null;
let activePresupuestoId = null;

const STATUS_LABELS = {
  confirmada: 'Confirmada',
  preparando: 'Preparando',
  en_transito: 'En transito',
  en_obra: 'En obra',
  entregada: 'Entregada',
  cancelada: 'Cancelada',
  con_incidencia: 'Con incidencia'
};

const NEXT_STATUS = {
  confirmada: 'preparando',
  preparando: 'en_transito',
  en_transito: 'en_obra',
  en_obra: 'entregada',
};

const NEXT_STATUS_LABEL = {
  confirmada: 'Iniciar preparacion',
  preparando: 'Marcar en transito',
  en_transito: 'Registrar llegada a obra',
  en_obra: 'Confirmar entrega',
};

/* ─── SVG Icons ─── */
const ICONS = {
  orders: '<svg viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>',
  history: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  cost: '<svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
  ratings: '<svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
  metrics: '<svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
  revenue: '<svg viewBox="0 0 24 24"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
  incoming: '<svg viewBox="0 0 24 24"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/></svg>',
  cart: '<svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>',
};

/* ─── API helper ─── */
async function api(path, opts = {}) {
  const url = '/portal' + path;
  console.log('[API]', opts.method || 'GET', url);
  const o = { headers: { 'Content-Type': 'application/json' }, ...opts };
  if (o.body && typeof o.body === 'object') {
    console.log('[API] body:', JSON.stringify(o.body));
    o.body = JSON.stringify(o.body);
  }
  const res = await fetch(url, o);
  const data = await res.json();
  console.log('[API] response:', res.status, data);
  if (!res.ok) {
    throw new Error(data.detail || data.error || ('HTTP ' + res.status));
  }
  return data;
}

/* ─── Login ─── */
function cleanPhone(raw) {
  // Strip spaces, dashes, dots, parentheses, plus signs
  let p = raw.replace(/[^0-9]/g, '');
  // Strip common country codes if user typed them in the number field
  if (p.startsWith('52') && p.length >= 12) p = p.substring(2);
  if (p.startsWith('1') && p.length >= 11) p = p.substring(1);
  console.log('[Login] cleaned phone:', raw, '->', p);
  return p;
}

async function doLogin() {
  const rawPhone = document.getElementById('login-phone').value.trim();
  const countryCode = document.getElementById('login-country-code').value;
  const nombre = document.getElementById('login-name').value.trim();
  const empresa = document.getElementById('login-empresa').value.trim();
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  if (!rawPhone) { errEl.textContent = 'Ingresa tu numero de WhatsApp.'; return; }
  if (!nombre) { errEl.textContent = 'Ingresa tu nombre.'; return; }
  const phone = cleanPhone(rawPhone);
  if (phone.length < 10) { errEl.textContent = 'El numero debe tener al menos 10 digitos.'; return; }
  // Build full international number (e.g. 523312345678)
  const fullPhone = countryCode.replace('+', '') + phone;
  const btn = document.getElementById('login-btn');
  btn.disabled = true;
  btn.textContent = 'Entrando...';
  try {
    const data = await api('/api/login', { method: 'POST', body: { telefono: fullPhone, nombre: nombre, empresa: empresa } });
    if (!data.rol) {
      errEl.textContent = 'Error al ingresar. Intenta de nuevo.';
      btn.disabled = false;
      btn.textContent = 'Entrar al Portal';
      return;
    }
    currentUser = data;
    showApp();
  } catch (e) {
    errEl.textContent = e.message || 'Error de conexion. Intenta de nuevo.';
    btn.disabled = false;
    btn.textContent = 'Entrar al Portal';
  }
}

document.getElementById('login-phone').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

function doLogout() {
  currentUser = null;
  currentView = null;
  ordersCache = [];
  localStorage.removeItem('obraya_token');
  localStorage.removeItem('obraya_user');
  document.getElementById('app-shell').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('login-phone').value = '';
  document.getElementById('login-error').textContent = '';
  document.getElementById('login-btn').disabled = false;
  document.getElementById('login-btn').textContent = 'Ingresar';
}

/* ─── Auto-login from OAuth token ─── */
(async function checkOAuthSession() {
  const token = localStorage.getItem('obraya_token');
  const userJson = localStorage.getItem('obraya_user');
  if (!token) { console.log('[Portal] No OAuth token found'); return; }
  console.log('[Portal] Found OAuth token, attempting auto-login...');
  try {
    // Pre-fill form from stored user data as fallback
    if (userJson) {
      try {
        const u = JSON.parse(userJson);
        if (u.nombre) document.getElementById('login-name').value = u.nombre;
        if (u.empresa) document.getElementById('login-empresa').value = u.empresa;
      } catch(e) {}
    }
    const res = await fetch('/portal/api/login-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
      },
    });
    const data = await res.json();
    console.log('[Portal] login-token response:', data);
    if (data.ok) {
      currentUser = { rol: data.rol, id: data.id, nombre: data.nombre, telefono: data.telefono };
      showApp();
    }
  } catch (e) {
    console.log('[Portal] OAuth auto-login failed:', e);
  }
})();

/* ─── App init ─── */
function showApp() {
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('app-shell').classList.remove('hidden');
  document.getElementById('sidebar-name').textContent = currentUser.nombre;
  const roleEl = document.getElementById('sidebar-role');
  roleEl.textContent = currentUser.rol === 'cliente' ? 'Cliente' : 'Proveedor';
  roleEl.className = 'user-role role-' + currentUser.rol;
  buildNav();
}

function buildNav() {
  const nav = document.getElementById('sidebar-nav');
  let items = [];
  if (currentUser.rol === 'cliente') {
    items = [
      { id: 'nuevo-pedido', label: 'Nuevo Pedido', icon: ICONS.cart },
      { id: 'mis-pedidos', label: 'Mis Pedidos', icon: ICONS.incoming },
      { id: 'mi-cuenta', label: 'Mi Cuenta', icon: ICONS.revenue },
    ];
  } else {
    items = [
      { id: 'solicitudes-cot', label: 'Solicitudes', icon: ICONS.incoming },
      { id: 'ordenes-prov', label: 'Ordenes', icon: ICONS.orders },
      { id: 'mi-negocio', label: 'Mi Negocio', icon: ICONS.metrics },
      { id: 'mi-perfil', label: 'Mi Perfil', icon: ICONS.cart },
    ];
  }
  nav.innerHTML = items.map(i => `
    <div class="nav-item" data-view="${i.id}" onclick="navigateTo('${i.id}')">
      <span class="nav-icon">${i.icon}</span>
      <span>${i.label}</span>
    </div>
  `).join('');
  navigateTo(items[0].id);
}

function navigateTo(view) {
  currentView = view;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
  });
  closeSidebar();
  renderView(view);
}

/* ─── Sidebar mobile ─── */
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const bd = document.getElementById('sidebar-backdrop');
  sb.classList.toggle('open');
  bd.classList.toggle('show');
}
function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-backdrop').classList.remove('show');
}

/* ─── Render views ─── */
async function renderView(view) {
  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="loading-center"><span class="spinner"></span> Cargando...</div>';

  try {
    switch (view) {
      // Cliente
      case 'nuevo-pedido': await renderNuevoPedido(main); break;
      case 'mis-pedidos': await renderMisPedidosUnificado(main); break;
      case 'mi-cuenta': await renderMiCuentaUnificado(main); break;
      case 'carrito': await renderCarrito(main); break;
      case 'comparativa': await renderComparativa(main, activePedidoId); break;
      case 'presupuesto-detalle': await renderPresupuestoDetalle(main, activePresupuestoId); break;
      case 'crear-presupuesto': await renderCrearPresupuesto(main); break;
      // Proveedor
      case 'solicitudes-cot': await renderProveedorSolicitudes(main); break;
      case 'ordenes-prov': await renderProveedorOrdenesUnificado(main); break;
      case 'mi-negocio': await renderProveedorNegocio(main); break;
      case 'mi-perfil': await renderProveedorPerfilUnificado(main); break;
    }
  } catch (e) {
    main.innerHTML = '<div class="empty-state"><p>Error al cargar datos. Intenta de nuevo.</p></div>';
    console.error(e);
  }
}

/* ─── Format helpers ─── */
function fmtMoney(n) { return '$' + (n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function fmtDate(iso) {
  if (!iso) return '---';
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
}
function fmtDateTime(iso) {
  if (!iso) return '---';
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short' }) + ' ' +
         d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
}
function statusBadge(s) { return `<span class="badge badge-${s}">${STATUS_LABELS[s] || s}</span>`; }
function paymentBadge(paid) {
  return paid
    ? '<span class="badge badge-pagado">Pagado</span>'
    : '<span class="badge badge-pendiente">Pendiente</span>';
}

function ratingDots(score, max = 5) {
  const filled = Math.round(score || 0);
  let html = '<span class="rating-dots">';
  for (let i = 0; i < max; i++) {
    html += `<span class="rating-dot ${i < filled ? 'filled' : ''}"></span>`;
  }
  html += '</span>';
  return html;
}

function metricBar(label, value, max, colorClass) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return `<div class="metric-bar-container">
    <div class="metric-bar-label"><span class="name">${label}</span><span class="val">${Math.round(pct)}%</span></div>
    <div class="metric-bar"><div class="metric-bar-fill ${colorClass}" style="width:${pct}%"></div></div>
  </div>`;
}

function itemsSummary(items) {
  if (!items || !items.length) return 'Sin items';
  if (items.length === 1) {
    return items[0].nombre || items[0].material || items[0].descripcion || '1 item';
  }
  const first = items[0].nombre || items[0].material || items[0].descripcion || 'item';
  return first + ' +' + (items.length - 1) + ' mas';
}

/* ─── CLIENT: Orders ─── */
async function renderClienteOrdenes(main, filter) {
  const data = await api(`/api/cliente/${currentUser.id}/ordenes?status=${filter}`);
  ordersCache = data;
  const isActive = filter === 'activas';
  const title = isActive ? 'Ordenes Activas' : 'Historial de Ordenes';
  const desc = isActive ? 'Ordenes en proceso de entrega' : 'Ordenes completadas y canceladas';

  let tableRows = '';
  if (data.length === 0) {
    tableRows = `<tr><td colspan="6"><div class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>
      <p>No hay ordenes ${isActive ? 'activas' : 'en el historial'}</p>
    </div></td></tr>`;
  } else {
    tableRows = data.map(o => `
      <tr onclick="openOrderDetail(${o.id}, 'cliente')">
        <td><strong>#${o.id}</strong></td>
        <td>${itemsSummary(o.items)}</td>
        <td>${o.proveedor_nombre}</td>
        <td>${fmtMoney(o.total)}</td>
        <td>${statusBadge(o.status)}</td>
        <td>${fmtDate(o.created_at)}</td>
      </tr>
    `).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>${title}</h2><p class="page-desc">${desc}</p></div>
    <div class="card">
      <div class="card-header"><h3>${data.length} orden${data.length !== 1 ? 'es' : ''}</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr>
            <th>ID</th><th>Materiales</th><th>Proveedor</th><th>Total</th><th>Estado</th><th>Fecha</th>
          </tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── CLIENT: Costs ─── */
async function renderClienteCostos(main) {
  const data = await api(`/api/cliente/${currentUser.id}/resumen`);
  let breakdownHtml = '';
  const entries = Object.entries(data.desglose_material || {});
  if (entries.length > 0) {
    breakdownHtml = entries.map(([cat, amt]) => `
      <div class="detail-row"><span class="label">${cat}</span><span class="value">${fmtMoney(amt)}</span></div>
    `).join('');
  } else {
    breakdownHtml = '<p style="color:var(--gray-500);font-size:14px;padding:8px 0">Sin datos de desglose disponibles</p>';
  }

  main.innerHTML = `
    <div class="page-header"><h2>Resumen de Costos</h2><p class="page-desc">Tu gasto acumulado en materiales</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-orange">
        <div class="stat-label">Total gastado</div>
        <div class="stat-value">${fmtMoney(data.total_gastado)}</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Ordenes totales</div>
        <div class="stat-value">${data.total_ordenes}</div>
      </div>
      <div class="stat-card accent-green">
        <div class="stat-label">Promedio por orden</div>
        <div class="stat-value">${fmtMoney(data.promedio_por_orden)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Activas / Completadas</div>
        <div class="stat-value">${data.ordenes_activas} / ${data.ordenes_completadas}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h3>Desglose por tipo de material</h3></div>
      <div class="card-body padded">${breakdownHtml}</div>
    </div>
  `;
}

/* ─── CLIENT: Ratings ─── */
async function renderClienteCalificaciones(main) {
  const data = await api(`/api/cliente/${currentUser.id}/calificaciones`);
  let rows = '';
  if (data.length === 0) {
    rows = `<tr><td colspan="5"><div class="empty-state"><p>Aun no has calificado proveedores</p></div></td></tr>`;
  } else {
    rows = data.map(c => `
      <tr>
        <td>#${c.orden_id}</td>
        <td>${c.proveedor_nombre}</td>
        <td>${ratingDots(c.calificacion_total)} <span style="font-size:12px;color:var(--gray-500);margin-left:4px">${(c.calificacion_total || 0).toFixed(1)}</span></td>
        <td>${c.comentario_usuario || '---'}</td>
        <td>${fmtDate(c.created_at)}</td>
      </tr>
    `).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>Calificaciones</h2><p class="page-desc">Calificaciones que has dado a proveedores</p></div>
    <div class="card">
      <div class="card-header"><h3>${data.length} calificacion${data.length !== 1 ? 'es' : ''}</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr><th>Orden</th><th>Proveedor</th><th>Calificacion</th><th>Comentario</th><th>Fecha</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── SUPPLIER: Orders ─── */
async function renderProveedorOrdenes(main, filter) {
  const data = await api(`/api/proveedor/${currentUser.id}/ordenes?status=${filter}`);
  ordersCache = data;
  const isActive = filter === 'activas';
  const title = isActive ? 'Ordenes Entrantes' : 'Historial de Ordenes';
  const desc = isActive ? 'Ordenes asignadas pendientes de entrega' : 'Ordenes completadas y canceladas';

  let tableRows = '';
  if (data.length === 0) {
    tableRows = `<tr><td colspan="7"><div class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/></svg>
      <p>No hay ordenes ${isActive ? 'pendientes' : 'en el historial'}</p>
    </div></td></tr>`;
  } else {
    tableRows = data.map(o => {
      const nextAction = NEXT_STATUS[o.status]
        ? `<button class="btn-action btn-sm" onclick="event.stopPropagation();advanceOrder(${o.id},'${NEXT_STATUS[o.status]}',this)">${NEXT_STATUS_LABEL[o.status]}</button>`
        : '';
      return `<tr onclick="openOrderDetail(${o.id}, 'proveedor')">
        <td><strong>#${o.id}</strong></td>
        <td>${itemsSummary(o.items)}</td>
        <td>${o.cliente_nombre}</td>
        <td>${o.direccion_entrega || o.municipio_entrega || '---'}</td>
        <td>${fmtMoney(o.total)}</td>
        <td>${statusBadge(o.status)}</td>
        <td>${nextAction}</td>
      </tr>`;
    }).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>${title}</h2><p class="page-desc">${desc}</p></div>
    <div class="card">
      <div class="card-header"><h3>${data.length} orden${data.length !== 1 ? 'es' : ''}</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr>
            <th>ID</th><th>Materiales</th><th>Cliente</th><th>Destino</th><th>Total</th><th>Estado</th><th>Accion</th>
          </tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── SUPPLIER: Advance order ─── */
async function advanceOrder(ordenId, newStatus, btnEl) {
  // If moving to en_transito, show transport form
  if (newStatus === 'en_transito') {
    openTransportForm(ordenId);
    return;
  }
  if (btnEl) { btnEl.disabled = true; btnEl.textContent = 'Actualizando...'; }
  const res = await api(`/api/proveedor/${currentUser.id}/ordenes/${ordenId}/status`, {
    method: 'POST',
    body: { status: newStatus }
  });
  if (res.ok) {
    renderView(currentView);
  } else {
    alert(res.error || 'Error al actualizar');
    if (btnEl) { btnEl.disabled = false; btnEl.textContent = NEXT_STATUS_LABEL[newStatus] || 'Avanzar'; }
  }
}

function openTransportForm(ordenId) {
  const overlay = document.getElementById('detail-overlay');
  const panel = document.getElementById('detail-panel');
  overlay.classList.remove('hidden');
  panel.innerHTML = `
    <div class="detail-header">
      <h3>Datos de Transporte - Orden #${ordenId}</h3>
      <button class="detail-close" onclick="closeDetail()">&times;</button>
    </div>
    <div class="detail-body">
      <div class="detail-section">
        <h4>Informacion del transporte</h4>
        <p style="font-size:14px;color:var(--gray-500);margin-bottom:16px">Ingresa los datos del vehiculo y chofer para la entrega.</p>
        <div class="transport-form">
          <div class="form-row">
            <div class="form-group"><label>Nombre del chofer</label><input id="tf-chofer" placeholder="Nombre completo"></div>
            <div class="form-group"><label>Telefono del chofer</label><input id="tf-tel" placeholder="Telefono"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Placas del vehiculo</label><input id="tf-placas" placeholder="ABC-123"></div>
            <div class="form-group">
              <label>Tipo de vehiculo</label>
              <select id="tf-tipo">
                <option value="">Seleccionar...</option>
                <option value="camioneta">Camioneta</option>
                <option value="torton">Torton</option>
                <option value="trailer">Trailer</option>
                <option value="olla">Olla</option>
                <option value="otro">Otro</option>
              </select>
            </div>
          </div>
          <button class="btn-action" onclick="submitTransport(${ordenId})" id="tf-submit">Confirmar y marcar en transito</button>
        </div>
      </div>
    </div>
  `;
}

async function submitTransport(ordenId) {
  const btn = document.getElementById('tf-submit');
  btn.disabled = true; btn.textContent = 'Enviando...';
  const body = {
    status: 'en_transito',
    nombre_chofer: document.getElementById('tf-chofer').value,
    telefono_chofer: document.getElementById('tf-tel').value,
    placas_vehiculo: document.getElementById('tf-placas').value,
    tipo_vehiculo: document.getElementById('tf-tipo').value,
  };
  const res = await api(`/api/proveedor/${currentUser.id}/ordenes/${ordenId}/status`, {
    method: 'POST', body
  });
  if (res.ok) {
    closeDetail();
    renderView(currentView);
  } else {
    alert(res.error || 'Error');
    btn.disabled = false; btn.textContent = 'Confirmar y marcar en transito';
  }
}

/* ─── SUPPLIER: Ratings ─── */
async function renderProveedorCalificaciones(main) {
  const data = await api(`/api/proveedor/${currentUser.id}/calificaciones`);
  let avg = 0;
  if (data.length > 0) avg = data.reduce((s, c) => s + (c.calificacion_total || 0), 0) / data.length;

  let rows = '';
  if (data.length === 0) {
    rows = `<tr><td colspan="6"><div class="empty-state"><p>Aun no tienes calificaciones</p></div></td></tr>`;
  } else {
    rows = data.map(c => `
      <tr>
        <td>#${c.orden_id}</td>
        <td>${ratingDots(c.puntualidad)} ${(c.puntualidad||0).toFixed(1)}</td>
        <td>${ratingDots(c.cantidad_correcta)} ${(c.cantidad_correcta||0).toFixed(1)}</td>
        <td>${ratingDots(c.especificacion_correcta)} ${(c.especificacion_correcta||0).toFixed(1)}</td>
        <td>${ratingDots(c.calificacion_total)} <strong>${(c.calificacion_total||0).toFixed(1)}</strong></td>
        <td>${fmtDate(c.created_at)}</td>
      </tr>
    `).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>Mis Calificaciones</h2><p class="page-desc">Como te califican tus clientes</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-orange">
        <div class="stat-label">Calificacion promedio</div>
        <div class="stat-value">${avg.toFixed(1)}</div>
        <div class="stat-sub">${ratingDots(avg)}</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Total de calificaciones</div>
        <div class="stat-value">${data.length}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h3>Detalle por orden</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr><th>Orden</th><th>Puntualidad</th><th>Cantidad</th><th>Especificacion</th><th>Total</th><th>Fecha</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── SUPPLIER: Revenue ─── */
async function renderProveedorIngresos(main) {
  const data = await api(`/api/proveedor/${currentUser.id}/metricas`);
  main.innerHTML = `
    <div class="page-header"><h2>Ingresos</h2><p class="page-desc">Resumen financiero de tus ordenes</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-green">
        <div class="stat-label">Ingresos totales</div>
        <div class="stat-value">${fmtMoney(data.ingresos_total)}</div>
        <div class="stat-sub">${data.ordenes_completadas} ordenes completadas</div>
      </div>
      <div class="stat-card accent-orange">
        <div class="stat-label">Pendiente de cobro</div>
        <div class="stat-value">${fmtMoney(data.ingresos_pendiente)}</div>
        <div class="stat-sub">${data.ordenes_activas} ordenes activas</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Total ordenes</div>
        <div class="stat-value">${data.total_ordenes}</div>
      </div>
    </div>
  `;
}

/* ─── SUPPLIER: Performance ─── */
async function renderProveedorDesempeno(main) {
  const data = await api(`/api/proveedor/${currentUser.id}/metricas`);
  main.innerHTML = `
    <div class="page-header"><h2>Desempeno</h2><p class="page-desc">Metricas de cumplimiento y calidad</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-green">
        <div class="stat-label">Calificacion general</div>
        <div class="stat-value">${(data.calificacion || 0).toFixed(1)}</div>
        <div class="stat-sub">${ratingDots(data.calificacion)}</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Puntualidad</div>
        <div class="stat-value">${data.puntualidad_porcentaje}%</div>
      </div>
      <div class="stat-card accent-red">
        <div class="stat-label">Incidencias totales</div>
        <div class="stat-value">${data.total_incidencias}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h3>Metricas detalladas</h3></div>
      <div class="card-body padded">
        ${metricBar('Puntualidad en entregas', data.tasa_puntualidad, 1, 'green')}
        ${metricBar('Cantidad correcta', data.tasa_cantidad_correcta, 1, 'blue')}
        ${metricBar('Especificacion correcta', data.tasa_especificacion_correcta, 1, 'orange')}
      </div>
    </div>
  `;
}

/* ─── Order Detail ─── */
async function openOrderDetail(ordenId, rol) {
  const overlay = document.getElementById('detail-overlay');
  const panel = document.getElementById('detail-panel');
  overlay.classList.remove('hidden');
  panel.innerHTML = '<div class="loading-center"><span class="spinner"></span> Cargando...</div>';

  const order = ordersCache.find(o => o.id === ordenId);
  const timeline = await api(`/api/orden/${ordenId}/timeline`);

  const isPaid = order.pagado === true;
  const paymentStatus = isPaid ? 'Pagado' : 'Pendiente';
  const paymentBadgeClass = isPaid ? 'pagado' : 'pendiente';

  // Cost breakdown
  const subtotal = (order.total || 0) / 1.02;  // Remove 2% commission
  const commission = (order.total || 0) - subtotal;

  // Build items table
  let itemsHtml = '';
  if (order.items && order.items.length > 0) {
    itemsHtml = '<table style="margin-bottom:0"><thead><tr><th>Material</th><th>Cantidad</th><th>Precio</th></tr></thead><tbody>';
    for (const item of order.items) {
      const name = item.nombre || item.material || item.descripcion || '---';
      const qty = item.cantidad ? (item.cantidad + ' ' + (item.unidad || '')) : '---';
      const price = item.precio_unitario ? fmtMoney(item.precio_unitario) : (item.subtotal ? fmtMoney(item.subtotal) : '---');
      itemsHtml += `<tr style="cursor:default"><td>${name}</td><td>${qty}</td><td>${price}</td></tr>`;
    }
    itemsHtml += '</tbody></table>';
  }

  // Timeline HTML
  let timelineHtml = '<div class="timeline">';
  const statusOrder = ['confirmada', 'preparando', 'en_transito', 'en_obra', 'entregada'];
  const currentIdx = statusOrder.indexOf(order.status);
  for (const step of timeline.steps) {
    const stepIdx = statusOrder.indexOf(step.status);
    let dotClass = '';
    if (step.completed) dotClass = 'completed';
    else if (stepIdx === currentIdx + 1) dotClass = '';  // next step
    if (step.status === order.status && !step.completed) dotClass = 'current';
    if (step.status === order.status && step.completed) dotClass = 'completed';
    // If current status, mark as current (pulsing)
    if (step.status === order.status && order.status !== 'entregada') dotClass = 'current';

    const labelClass = step.completed || step.status === order.status ? '' : 'pending';
    timelineHtml += `
      <div class="timeline-step">
        <div class="timeline-dot ${dotClass}"></div>
        <div class="timeline-label ${labelClass}">${step.label}</div>
        <div class="timeline-time">${fmtDateTime(step.timestamp)}</div>
      </div>
    `;
  }
  timelineHtml += '</div>';

  // Supplier action (for supplier view)
  let actionHtml = '';
  if (rol === 'proveedor' && NEXT_STATUS[order.status]) {
    if (NEXT_STATUS[order.status] === 'en_transito') {
      actionHtml = `<div class="detail-section"><h4>Accion</h4>
        <button class="btn-action" onclick="closeDetail();openTransportForm(${order.id})">${NEXT_STATUS_LABEL[order.status]}</button>
      </div>`;
    } else {
      actionHtml = `<div class="detail-section"><h4>Accion</h4>
        <button class="btn-action" onclick="closeDetail();advanceOrder(${order.id},'${NEXT_STATUS[order.status]}',null)">${NEXT_STATUS_LABEL[order.status]}</button>
      </div>`;
    }
  }

  // Transport info
  let transportHtml = '';
  if (order.nombre_chofer || order.telefono_chofer || order.placas_vehiculo) {
    transportHtml = `<div class="detail-section"><h4>Transporte</h4>
      <div class="detail-row"><span class="label">Chofer</span><span class="value">${order.nombre_chofer || '---'}</span></div>
      <div class="detail-row"><span class="label">Tel. chofer</span><span class="value">${order.telefono_chofer || '---'}</span></div>
      <div class="detail-row"><span class="label">Placas</span><span class="value">${order.placas_vehiculo || '---'}</span></div>
      <div class="detail-row"><span class="label">Vehiculo</span><span class="value">${order.tipo_vehiculo || '---'}</span></div>
    </div>`;
  }

  panel.innerHTML = `
    <div class="detail-header">
      <h3>Orden #${order.id}</h3>
      <button class="detail-close" onclick="closeDetail()">&times;</button>
    </div>
    <div class="detail-body">
      <div class="detail-section">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px">
          ${statusBadge(order.status)}
          <span class="badge badge-${paymentBadgeClass}">${paymentStatus}</span>
        </div>
      </div>

      <div class="detail-section">
        <h4>Progreso de entrega</h4>
        ${timelineHtml}
      </div>

      ${actionHtml}

      <div class="detail-section">
        <h4>Materiales</h4>
        ${itemsHtml || '<p style="color:var(--gray-500);font-size:14px">Sin detalle de items</p>'}
      </div>

      <div class="detail-section">
        <h4>Informacion de entrega</h4>
        <div class="detail-row"><span class="label">Direccion</span><span class="value">${order.direccion_entrega || '---'}</span></div>
        <div class="detail-row"><span class="label">Municipio</span><span class="value">${order.municipio_entrega || '---'}</span></div>
        <div class="detail-row"><span class="label">Entrega prometida</span><span class="value">${fmtDateTime(order.fecha_entrega_prometida)}</span></div>
        <div class="detail-row"><span class="label">${rol === 'cliente' ? 'Proveedor' : 'Cliente'}</span><span class="value">${rol === 'cliente' ? (order.proveedor_nombre || '---') : (order.cliente_nombre || '---')}</span></div>
      </div>

      ${transportHtml}

      <div class="detail-section">
        <h4>Pago</h4>
        <div class="payment-breakdown">
          <div class="payment-line"><span>Subtotal materiales</span><span>${fmtMoney(subtotal)}</span></div>
          <div class="payment-line"><span>Comision ObraYa (2%)</span><span>${fmtMoney(commission)}</span></div>
          <div class="payment-line total"><span>Total</span><span>${fmtMoney(order.total)}</span></div>
        </div>
        ${!isPaid && rol === 'cliente' ? '<button class="btn-pay" onclick="pagarOrden(' + order.id + ')">Pagar con Stripe</button>' : ''}
        ${isPaid ? '<p style="color:var(--green);font-size:14px;margin-top:8px">&#10003; Pago completado</p>' : ''}
      </div>
    </div>
  `;
}

/* ═══ FASE 1: NUEVO PEDIDO — Catalogo + Carrito ═══ */

function saveCart() { localStorage.setItem('obraya_cart', JSON.stringify(cart)); }

function addToCart(item) {
  const existing = cart.find(c => c.catalogo_id === item.id);
  if (existing) { existing.cantidad += 1; }
  else { cart.push({ catalogo_id: item.id, nombre: item.nombre, categoria: item.categoria, unidad: item.unidad, precio_referencia: item.precio_referencia, cantidad: 1 }); }
  saveCart();
  renderView('nuevo-pedido');
}

function removeFromCart(idx) { cart.splice(idx, 1); saveCart(); }
function updateCartQty(idx, val) { cart[idx].cantidad = Math.max(1, parseInt(val) || 1); saveCart(); }

async function renderNuevoPedido(main) {
  const cats = await api('/api/catalogo/categorias');
  const searchQ = document.getElementById('cat-search')?.value || '';
  const activeCat = window._activeCat || '';
  let url = '/api/catalogo?q=' + encodeURIComponent(searchQ);
  if (activeCat) url += '&categoria=' + encodeURIComponent(activeCat);
  const items = await api(url);

  const cartCount = cart.reduce((s, c) => s + c.cantidad, 0);

  main.innerHTML = '<div class="page-header"><h2>Nuevo Pedido</h2><p class="subtitle">Busca materiales y agrega al carrito</p></div>' +
    '<div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;align-items:center">' +
      '<input type="text" id="cat-search" placeholder="Buscar material..." value="' + searchQ.replace(/"/g, '&quot;') + '" style="flex:1;min-width:200px;padding:10px 14px;border:1.5px solid var(--gray-300);border-radius:var(--radius);font-size:14px" onkeyup="if(event.key===&#39;Enter&#39;){window._activeCat=&#39;&#39;;renderView(&#39;nuevo-pedido&#39;)}">' +
      '<button onclick="navigateTo(&#39;carrito&#39;)" class="btn-primary" style="width:auto;padding:10px 20px;position:relative">Carrito (' + cartCount + ')</button>' +
    '</div>' +
    '<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">' +
      '<button class="cat-btn' + (!activeCat ? ' active' : '') + '" onclick="window._activeCat=&#39;&#39;;renderView(&#39;nuevo-pedido&#39;)">Todos</button>' +
      cats.map(c => '<button class="cat-btn' + (activeCat === c ? ' active' : '') + '" onclick="window._activeCat=&#39;' + c + '&#39;;renderView(&#39;nuevo-pedido&#39;)">' + c + '</button>').join('') +
    '</div>' +
    '<div class="product-grid">' +
      items.map(i => {
        const inCart = cart.find(c => c.catalogo_id === i.id);
        return '<div class="product-card">' +
          '<div class="product-cat">' + i.categoria + '</div>' +
          '<div class="product-name">' + i.nombre + '</div>' +
          '<div class="product-unit">' + i.unidad + '</div>' +
          (i.precio_referencia ? '<div class="product-price">Ref: ' + fmtMoney(i.precio_referencia) + '</div>' : '') +
          (inCart ? '<button class="btn-added" disabled>En carrito (' + inCart.cantidad + ')</button>' :
            '<button class="btn-add" onclick="addToCart(' + JSON.stringify(i).replace(/"/g, '&quot;') + ')">+ Agregar</button>') +
        '</div>';
      }).join('') +
      (items.length === 0 ? '<div class="empty-state"><p>No se encontraron productos</p></div>' : '') +
    '</div>';
}

async function renderCarrito(main) {
  if (cart.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Carrito</h2></div><div class="empty-state"><p>Tu carrito esta vacio.</p><button class="btn-primary" style="width:auto;padding:10px 20px;margin-top:12px" onclick="navigateTo(&#39;nuevo-pedido&#39;)">Buscar materiales</button></div>';
    return;
  }
  const subtotal = cart.reduce((s, c) => s + (c.precio_referencia || 0) * c.cantidad, 0);
  main.innerHTML = '<div class="page-header"><h2>Carrito</h2><p class="subtitle">' + cart.length + ' materiales</p></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>Material</th><th>Unidad</th><th>Cantidad</th><th>Ref. Precio</th><th></th></tr></thead><tbody>' +
    cart.map((c, i) =>
      '<tr><td>' + c.nombre + '</td><td>' + c.unidad + '</td>' +
      '<td><input type="number" min="1" value="' + c.cantidad + '" style="width:70px;padding:6px;border:1px solid var(--gray-300);border-radius:4px" onchange="updateCartQty(' + i + ',this.value);renderView(&#39;carrito&#39;)"></td>' +
      '<td>' + (c.precio_referencia ? fmtMoney(c.precio_referencia * c.cantidad) : '-') + '</td>' +
      '<td><button onclick="removeFromCart(' + i + ');renderView(&#39;carrito&#39;)" style="color:var(--red);background:none;border:none;font-size:18px;cursor:pointer">X</button></td></tr>'
    ).join('') +
    '</tbody></table>' +
    (subtotal > 0 ? '<div style="text-align:right;padding:12px;font-weight:600">Estimado: ' + fmtMoney(subtotal) + ' (precio final al cotizar)</div>' : '') +
    '</div>' +
    '<div class="card" style="margin-top:16px"><h3 style="margin-bottom:12px">Datos de entrega</h3>' +
      '<div class="form-group"><label>Direccion de entrega</label><input type="text" id="cart-direccion" placeholder="Ej. Calle 5 #123, Col. Centro, Guadalajara" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
      '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Municipio</label><input type="text" id="cart-municipio" placeholder="Ej. Zapopan" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
      '<div class="form-group" style="flex:1"><label>Fecha de entrega</label><input type="date" id="cart-fecha" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
      '<button class="btn-primary" style="margin-top:12px" onclick="submitPedido()">Solicitar Cotizaciones</button>' +
    '</div>';
}

async function submitPedido() {
  const dir = document.getElementById('cart-direccion')?.value || '';
  const mun = document.getElementById('cart-municipio')?.value || '';
  const fecha = document.getElementById('cart-fecha')?.value || '';
  if (!dir) { alert('Ingresa la direccion de entrega'); return; }
  const body = { usuario_id: currentUser.id, items: cart, direccion_entrega: dir, municipio_entrega: mun, fecha_entrega: fecha };
  const data = await api('/api/pedido', { method: 'POST', body: body });
  if (data.ok) {
    cart = []; saveCart();
    if (data.cotizaciones_count > 0) { activePedidoId = data.pedido_id; navigateTo('comparativa'); }
    else { navigateTo('mis-pedidos'); }
  } else { alert(data.error || 'Error al crear pedido'); }
}

async function renderMisPedidos(main) {
  const data = await api('/api/mis-pedidos/' + currentUser.id);
  let rows = '';
  if (data.length === 0) {
    rows = '<tr><td colspan="5"><div class="empty-state"><p>No tienes pedidos en proceso</p></div></td></tr>';
  } else {
    rows = data.map(p =>
      '<tr style="cursor:pointer" onclick="activePedidoId=' + p.id + ';navigateTo(&#39;comparativa&#39;)">' +
      '<td>#' + p.id + '</td><td>' + (p.items_resumen || '-') + '</td><td>' + statusBadge(p.status) + '</td>' +
      '<td>' + p.cotizaciones + ' cotizaciones</td><td>' + fmtDate(p.created_at) + '</td></tr>'
    ).join('');
  }
  main.innerHTML = '<div class="page-header"><h2>Mis Pedidos en Proceso</h2><p class="subtitle">Pedidos esperando cotizaciones o seleccion</p></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>ID</th><th>Materiales</th><th>Status</th><th>Cotizaciones</th><th>Fecha</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
}

async function renderComparativa(main, pedidoId) {
  if (!pedidoId) { navigateTo('mis-pedidos'); return; }
  const cotizaciones = await api('/api/pedido/' + pedidoId + '/cotizaciones');
  if (cotizaciones.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Comparativa - Pedido #' + pedidoId + '</h2></div><div class="empty-state"><p>Aun no hay cotizaciones disponibles. Espera a que los proveedores respondan.</p><button class="btn-primary" style="width:auto;padding:10px 20px;margin-top:12px" onclick="navigateTo(&#39;mis-pedidos&#39;)">Volver</button></div>';
    return;
  }
  const cards = cotizaciones.map((c, idx) => {
    const items = (c.items || []).map(it =>
      '<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:13px"><span>' + (it.producto || it.nombre || '-') + ' x' + (it.cantidad || 1) + '</span><span>' + fmtMoney(it.subtotal || it.precio_unitario || 0) + '</span></div>'
    ).join('');
    return '<div class="cot-card">' +
      '<div class="cot-header"><span class="cot-rank">#' + (idx + 1) + '</span><span class="cot-name">' + c.proveedor_nombre + '</span><span class="cot-rating">' + (c.proveedor_calificacion || 0).toFixed(1) + '/5</span></div>' +
      '<div class="cot-items">' + items + '</div>' +
      '<div class="cot-totals">' +
        '<div style="display:flex;justify-content:space-between"><span>Subtotal</span><span>' + fmtMoney(c.subtotal) + '</span></div>' +
        '<div style="display:flex;justify-content:space-between"><span>Flete</span><span>' + (c.costo_flete > 0 ? fmtMoney(c.costo_flete) : 'Incluido') + '</span></div>' +
        '<div style="display:flex;justify-content:space-between;font-weight:700;font-size:16px;border-top:1px solid var(--gray-200);padding-top:8px;margin-top:4px"><span>Total</span><span>' + fmtMoney(c.total) + '</span></div>' +
      '</div>' +
      '<div style="padding:12px;font-size:13px;color:var(--gray-500)">Entrega: ' + (c.tiempo_entrega || 'Consultar') + '</div>' +
      '<button class="btn-primary" onclick="elegirProveedor(' + pedidoId + ',' + c.cotizacion_id + ')">Elegir este proveedor</button>' +
    '</div>';
  }).join('');
  main.innerHTML = '<div class="page-header"><h2>Comparativa de Precios</h2><p class="subtitle">Pedido #' + pedidoId + ' - ' + cotizaciones.length + ' opciones</p></div><div class="cot-grid">' + cards + '</div>';
}

async function elegirProveedor(pedidoId, cotizacionId) {
  if (!confirm('Confirmas este proveedor?')) return;
  const data = await api('/api/pedido/' + pedidoId + '/elegir', { method: 'POST', body: { cotizacion_id: cotizacionId, usuario_id: currentUser.id } });
  if (data.ok) { alert('Orden #' + data.orden_id + ' creada! Total: ' + fmtMoney(data.total)); navigateTo('ordenes-activas'); }
  else { alert(data.error || 'Error al crear orden'); }
}

/* ═══ FASE 2: PAGOS ═══ */

async function pagarOrden(ordenId) {
  const data = await api('/api/pagar/' + ordenId, { method: 'POST' });
  if (data.ok) { window.location.href = data.url; }
  else { alert(data.error || 'Error al crear sesion de pago'); }
}

/* ═══ FASE 3: PRESUPUESTOS ═══ */

async function renderPresupuestos(main) {
  const data = await api('/api/presupuestos/' + currentUser.id);
  let cards = '';
  if (data.length === 0) {
    cards = '<div class="empty-state"><p>No tienes presupuestos de obra</p></div>';
  } else {
    cards = data.map(p => {
      const pct = p.porcentaje_consumido || 0;
      const color = pct >= 80 ? 'var(--red)' : pct >= 50 ? 'var(--orange)' : 'var(--green)';
      return '<div class="card" style="cursor:pointer;margin-bottom:12px" onclick="activePresupuestoId=' + p.id + ';navigateTo(&#39;presupuesto-detalle&#39;)">' +
        '<h3>' + p.nombre_obra + '</h3><p style="color:var(--gray-500);font-size:13px">' + (p.direccion || '') + '</p>' +
        '<div style="margin-top:12px"><div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px"><span>Consumido: ' + pct.toFixed(1) + '%</span><span>' + fmtMoney(p.gastado_total || 0) + ' / ' + fmtMoney(p.presupuesto_total || 0) + '</span></div>' +
        '<div style="background:var(--gray-200);border-radius:4px;height:8px;overflow:hidden"><div style="width:' + Math.min(pct, 100) + '%;height:100%;background:' + color + ';border-radius:4px"></div></div></div>' +
      '</div>';
    }).join('');
  }
  main.innerHTML = '<div class="page-header" style="display:flex;justify-content:space-between;align-items:center"><div><h2>Presupuestos de Obra</h2><p class="subtitle">Control de costos por proyecto</p></div><button class="btn-primary" style="width:auto;padding:8px 16px" onclick="navigateTo(&#39;crear-presupuesto&#39;)">+ Nuevo</button></div>' + cards;
}

async function renderPresupuestoDetalle(main, presId) {
  if (!presId) { navigateTo('presupuestos'); return; }
  const data = await api('/api/presupuesto/' + presId);
  if (!data.ok) { main.innerHTML = '<div class="empty-state"><p>Presupuesto no encontrado</p></div>'; return; }
  const p = data.presupuesto;
  const rows = data.partidas.map(pt => {
    const pct = pt.porcentaje_consumido || 0;
    const color = pt.bloqueado ? 'var(--red)' : pct >= 80 ? 'var(--orange)' : pct >= 50 ? '#f39c12' : 'var(--green)';
    return '<tr' + (pt.bloqueado ? ' style="opacity:0.6"' : '') + '><td>' + pt.nombre_material + '</td><td>' + pt.categoria + '</td><td>' + pt.unidad + '</td>' +
      '<td>' + (pt.cantidad_consumida || 0) + ' / ' + pt.cantidad_presupuestada + '</td>' +
      '<td><div style="display:flex;align-items:center;gap:8px"><div style="flex:1;background:var(--gray-200);border-radius:3px;height:6px"><div style="width:' + Math.min(pct, 100) + '%;height:100%;background:' + color + ';border-radius:3px"></div></div><span style="font-size:12px;min-width:40px">' + pct.toFixed(0) + '%</span></div></td>' +
      '<td>' + fmtMoney(pt.monto_gastado || 0) + ' / ' + fmtMoney(pt.monto_presupuestado || 0) + '</td>' +
      '<td>' + (pt.bloqueado ? '<span style="color:var(--red);font-size:12px">Bloqueado</span>' : '<button class="btn-sm" onclick="registrarConsumo(' + presId + ',' + pt.id + ')">+ Consumo</button>') + '</td></tr>';
  }).join('');
  main.innerHTML = '<div class="page-header"><button onclick="navigateTo(&#39;presupuestos&#39;)" style="background:none;border:none;color:var(--blue);cursor:pointer;font-size:14px;margin-bottom:8px">< Volver</button><h2>' + p.nombre_obra + '</h2><p class="subtitle">' + fmtMoney(p.gastado_total || 0) + ' de ' + fmtMoney(p.presupuesto_total || 0) + ' (' + (p.porcentaje_consumido || 0).toFixed(1) + '%)</p></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>Material</th><th>Categoria</th><th>Unidad</th><th>Cantidad</th><th>Progreso</th><th>Monto</th><th></th></tr></thead><tbody>' + rows + '</tbody></table></div>';
}

async function registrarConsumo(presId, partidaId) {
  const cant = prompt('Cantidad consumida:');
  if (!cant || isNaN(cant)) return;
  const data = await api('/api/presupuesto/' + presId + '/partidas/' + partidaId + '/consumo', { method: 'PUT', body: { cantidad: parseFloat(cant) } });
  if (data.ok) { renderView('presupuesto-detalle'); }
  else { alert(data.error || 'Error'); }
}

async function renderCrearPresupuesto(main) {
  main.innerHTML = '<div class="page-header"><button onclick="navigateTo(&#39;presupuestos&#39;)" style="background:none;border:none;color:var(--blue);cursor:pointer;font-size:14px;margin-bottom:8px">< Volver</button><h2>Nuevo Presupuesto</h2></div>' +
    '<div class="card"><div class="form-group"><label>Nombre de la obra</label><input type="text" id="pres-nombre" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="Ej. Casa habitacion Zapopan"></div>' +
    '<div class="form-group"><label>Direccion</label><input type="text" id="pres-dir" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Fecha inicio</label><input type="date" id="pres-inicio" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div class="form-group" style="flex:1"><label>Fecha fin estimada</label><input type="date" id="pres-fin" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
    '<div class="form-group"><label>Presupuesto total (MXN)</label><input type="number" id="pres-total" style="width:200px;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="0"></div>' +
    '<button class="btn-primary" style="margin-top:12px" onclick="submitPresupuesto()">Crear Presupuesto</button></div>';
}

async function submitPresupuesto() {
  const nombre = document.getElementById('pres-nombre')?.value;
  if (!nombre) { alert('Ingresa el nombre de la obra'); return; }
  const body = {
    usuario_id: currentUser.id,
    nombre_obra: nombre,
    direccion: document.getElementById('pres-dir')?.value || '',
    fecha_inicio: document.getElementById('pres-inicio')?.value || '',
    fecha_fin_estimada: document.getElementById('pres-fin')?.value || '',
    presupuesto_total: parseFloat(document.getElementById('pres-total')?.value) || 0,
    partidas: []
  };
  const data = await api('/api/presupuestos', { method: 'POST', body: body });
  if (data.ok) { activePresupuestoId = data.presupuesto_id; navigateTo('presupuesto-detalle'); }
  else { alert('Error al crear presupuesto'); }
}

/* ═══ FASE 4: APROBACIONES ═══ */

async function renderAprobaciones(main) {
  const data = await api('/api/aprobaciones/pendientes/' + currentUser.id);
  if (!data.es_aprobador) {
    main.innerHTML = '<div class="page-header"><h2>Aprobaciones</h2></div><div class="empty-state"><p>No eres aprobador en ninguna empresa. Contacta a tu administrador para obtener permisos.</p></div>';
    return;
  }
  if (data.pendientes.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Aprobaciones</h2></div><div class="empty-state"><p>No tienes aprobaciones pendientes</p></div>';
    return;
  }
  const cards = data.pendientes.map(a => {
    const items = (a.items || []).map(it => '<div style="font-size:13px">' + (it.producto || it.nombre || '-') + ' x' + (it.cantidad || 1) + '</div>').join('');
    return '<div class="card" style="margin-bottom:12px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center"><h3>Orden #' + a.orden_id + '</h3><span style="font-size:20px;font-weight:700;color:var(--orange)">' + fmtMoney(a.monto) + '</span></div>' +
      '<p style="color:var(--gray-500);font-size:13px">Solicitado por: ' + a.solicitante + ' - ' + fmtDate(a.solicitada_at) + '</p>' +
      (a.direccion ? '<p style="font-size:13px;margin-top:4px">Entrega: ' + a.direccion + '</p>' : '') +
      '<div style="margin:8px 0">' + items + '</div>' +
      '<div style="display:flex;gap:8px;margin-top:12px"><button class="btn-primary" style="flex:1" onclick="aprobarSolicitud(' + a.id + ')">Aprobar</button><button style="flex:1;padding:10px;background:var(--red);color:#fff;border:none;border-radius:var(--radius);font-weight:600;cursor:pointer" onclick="rechazarSolicitud(' + a.id + ')">Rechazar</button></div>' +
    '</div>';
  }).join('');
  main.innerHTML = '<div class="page-header"><h2>Aprobaciones Pendientes</h2><p class="subtitle">' + data.pendientes.length + ' solicitudes</p></div>' + cards;
}

async function aprobarSolicitud(id) {
  if (!confirm('Aprobar esta compra?')) return;
  const data = await api('/api/aprobaciones/' + id + '/aprobar', { method: 'POST' });
  if (data.ok) { renderView('aprobaciones'); } else { alert(data.error || 'Error'); }
}

async function rechazarSolicitud(id) {
  const motivo = prompt('Motivo del rechazo (opcional):');
  const data = await api('/api/aprobaciones/' + id + '/rechazar', { method: 'POST', body: { motivo: motivo || '' } });
  if (data.ok) { renderView('aprobaciones'); } else { alert(data.error || 'Error'); }
}

/* ═══ FASE 5: PORTAL VENDEDOR ═══ */

async function renderProveedorProductos(main) {
  const data = await api('/api/proveedor/' + currentUser.id + '/productos');
  const rows = data.map(p =>
    '<tr><td>' + p.nombre + '</td><td>' + p.categoria + '</td><td>' + p.unidad + '</td>' +
    '<td><input type="number" value="' + p.precio_unitario + '" style="width:100px;padding:6px;border:1px solid var(--gray-300);border-radius:4px" onchange="updateProductPrice(' + p.id + ',this.value)"></td>' +
    '<td>' + p.disponibilidad + '</td>' +
    '<td>' + (p.activo ? '<span style="color:var(--green)">Activo</span>' : '<span style="color:var(--red)">Inactivo</span>') + '</td>' +
    '<td><button class="btn-sm" style="color:var(--red)" onclick="deleteProduct(' + p.id + ')">Eliminar</button></td></tr>'
  ).join('');
  main.innerHTML = '<div class="page-header" style="display:flex;justify-content:space-between;align-items:center"><div><h2>Mis Productos</h2><p class="subtitle">' + data.length + ' productos en tu catalogo</p></div><button class="btn-primary" style="width:auto;padding:8px 16px" onclick="renderAgregarProducto()">+ Agregar</button></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>Producto</th><th>Categoria</th><th>Unidad</th><th>Precio (MXN)</th><th>Disponibilidad</th><th>Status</th><th></th></tr></thead><tbody>' +
    (rows || '<tr><td colspan="7"><div class="empty-state"><p>No tienes productos registrados</p></div></td></tr>') +
    '</tbody></table></div>';
}

async function updateProductPrice(prodId, newPrice) {
  await api('/api/proveedor/' + currentUser.id + '/productos/' + prodId, { method: 'PUT', body: { precio_unitario: parseFloat(newPrice) } });
}

async function deleteProduct(prodId) {
  if (!confirm('Eliminar este producto?')) return;
  await api('/api/proveedor/' + currentUser.id + '/productos/' + prodId, { method: 'DELETE' });
  renderView('mis-productos');
}

async function renderAgregarProducto() {
  const main = document.getElementById('main-content');
  const cats = await api('/api/catalogo/categorias');
  main.innerHTML = '<div class="page-header"><button onclick="navigateTo(&#39;mis-productos&#39;)" style="background:none;border:none;color:var(--blue);cursor:pointer;font-size:14px;margin-bottom:8px">< Volver</button><h2>Agregar Producto</h2></div>' +
    '<div class="card">' +
    '<div class="form-group"><label>Nombre del producto</label><input type="text" id="prod-nombre" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="Ej. Concreto premezclado FC 250"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Categoria</label><select id="prod-cat" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)">' + cats.map(c => '<option value="' + c + '">' + c + '</option>').join('') + '</select></div>' +
    '<div class="form-group" style="flex:1"><label>Unidad</label><select id="prod-unidad" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"><option>m3</option><option>pieza</option><option>kg</option><option>ton</option><option>bulto</option><option>cubeta</option><option>rollo</option><option>viaje</option></select></div></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Precio unitario (MXN)</label><input type="number" id="prod-precio" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="0"></div>' +
    '<div class="form-group" style="flex:1"><label>Disponibilidad</label><select id="prod-disp" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"><option value="inmediata">Inmediata</option><option value="24h">24 horas</option><option value="48h">48 horas</option><option value="sobre_pedido">Sobre pedido</option></select></div></div>' +
    '<button class="btn-primary" style="margin-top:12px" onclick="submitProducto()">Guardar Producto</button></div>';
}

async function submitProducto() {
  const body = {
    nombre: document.getElementById('prod-nombre')?.value || '',
    categoria: document.getElementById('prod-cat')?.value || '',
    unidad: document.getElementById('prod-unidad')?.value || '',
    precio_unitario: parseFloat(document.getElementById('prod-precio')?.value) || 0,
    disponibilidad: document.getElementById('prod-disp')?.value || 'inmediata',
  };
  if (!body.nombre || !body.precio_unitario) { alert('Completa nombre y precio'); return; }
  const data = await api('/api/proveedor/' + currentUser.id + '/productos', { method: 'POST', body: body });
  if (data.ok) { navigateTo('mis-productos'); }
  else { alert(data.error || 'Error al guardar'); }
}

async function renderProveedorSolicitudes(main) {
  const data = await api('/api/proveedor/' + currentUser.id + '/solicitudes');
  if (data.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Solicitudes de Cotizacion</h2></div><div class="empty-state"><p>No tienes solicitudes pendientes</p></div>';
    return;
  }
  const cards = data.map(s => {
    const items = (s.items || []).map(it => '<div style="font-size:13px;padding:2px 0">' + (it.producto || '-') + ' - ' + (it.cantidad || 1) + ' ' + (it.unidad || '') + '</div>').join('');
    return '<div class="card" style="margin-bottom:12px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center"><h3>Pedido #' + s.pedido_id + '</h3>' + statusBadge(s.status) + '</div>' +
      '<p style="color:var(--gray-500);font-size:13px">Recibida: ' + fmtDateTime(s.enviada_at) + (s.recordatorios > 0 ? ' (' + s.recordatorios + ' recordatorios)' : '') + '</p>' +
      (s.direccion_entrega ? '<p style="font-size:13px;margin-top:4px">Entrega: ' + s.direccion_entrega + (s.fecha_entrega ? ' - ' + s.fecha_entrega : '') + '</p>' : '') +
      '<div style="margin:8px 0;padding:8px;background:var(--gray-50);border-radius:var(--radius)">' + items + '</div>' +
      '<div style="margin-top:12px;border-top:1px solid var(--gray-200);padding-top:12px"><h4 style="font-size:14px;margin-bottom:8px">Responder cotizacion</h4>' +
      '<div style="display:flex;gap:12px;flex-wrap:wrap">' +
        '<div class="form-group" style="flex:1;min-width:120px"><label>Precio total (MXN)</label><input type="number" id="sol-precio-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="0"></div>' +
        '<div class="form-group" style="flex:1;min-width:120px"><label>Tiempo entrega</label><input type="text" id="sol-tiempo-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="Ej. manana 7am"></div>' +
        '<div class="form-group" style="flex:1;min-width:120px"><label>Costo flete</label><input type="number" id="sol-flete-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="0" value="0"></div>' +
      '</div>' +
      '<div class="form-group"><label>Notas</label><input type="text" id="sol-notas-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="Condiciones, observaciones..."></div>' +
      '<button class="btn-primary" onclick="responderSolicitud(' + s.id + ')">Enviar Cotizacion</button></div>' +
    '</div>';
  }).join('');
  main.innerHTML = '<div class="page-header"><h2>Solicitudes de Cotizacion</h2><p class="subtitle">' + data.length + ' pendientes</p></div>' + cards;
}

async function responderSolicitud(solId) {
  const precio = parseFloat(document.getElementById('sol-precio-' + solId)?.value);
  if (!precio || precio <= 0) { alert('Ingresa el precio total'); return; }
  const body = {
    precio_total: precio,
    tiempo_entrega: document.getElementById('sol-tiempo-' + solId)?.value || '24h',
    costo_flete: parseFloat(document.getElementById('sol-flete-' + solId)?.value) || 0,
    notas: document.getElementById('sol-notas-' + solId)?.value || '',
  };
  const data = await api('/api/proveedor/' + currentUser.id + '/solicitudes/' + solId + '/responder', { method: 'POST', body: body });
  if (data.ok) { alert('Cotizacion enviada!'); renderView('solicitudes-cot'); }
  else { alert(data.error || 'Error'); }
}

async function renderProveedorPerfil(main) {
  const data = await api('/api/proveedor/' + currentUser.id + '/perfil');
  if (!data.ok) { main.innerHTML = '<div class="empty-state"><p>Error al cargar perfil</p></div>'; return; }
  const p = data.perfil;
  const cats = (p.categorias || []).join(', ');
  main.innerHTML = '<div class="page-header"><h2>Mi Perfil</h2></div>' +
    '<div class="card">' +
    '<div class="form-group"><label>Nombre</label><input type="text" id="perf-nombre" value="' + (p.nombre || '').replace(/"/g, '&quot;') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>WhatsApp</label><input type="text" id="perf-tel" value="' + (p.telefono_whatsapp || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div class="form-group" style="flex:1"><label>Email</label><input type="email" id="perf-email" value="' + (p.email || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
    '<div class="form-group"><label>Direccion</label><input type="text" id="perf-dir" value="' + (p.direccion || '').replace(/"/g, '&quot;') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Municipio</label><input type="text" id="perf-muni" value="' + (p.municipio || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div class="form-group" style="flex:1"><label>Horario</label><input type="text" id="perf-horario" value="' + (p.horario_atencion || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
    '<div class="stats-grid" style="margin:16px 0"><div class="stat-card"><div class="stat-value">' + (p.calificacion || 0).toFixed(1) + '</div><div class="stat-label">Calificacion</div></div>' +
    '<div class="stat-card"><div class="stat-value">' + (p.total_pedidos || 0) + '</div><div class="stat-label">Pedidos</div></div>' +
    '<div class="stat-card"><div class="stat-value">' + (p.pedidos_cumplidos || 0) + '</div><div class="stat-label">Cumplidos</div></div></div>' +
    '<button class="btn-primary" style="margin-top:12px" onclick="guardarPerfil()">Guardar Cambios</button></div>';
}

async function guardarPerfil() {
  const body = {
    nombre: document.getElementById('perf-nombre')?.value,
    telefono_whatsapp: document.getElementById('perf-tel')?.value,
    email: document.getElementById('perf-email')?.value,
    direccion: document.getElementById('perf-dir')?.value,
    municipio: document.getElementById('perf-muni')?.value,
    horario_atencion: document.getElementById('perf-horario')?.value,
  };
  const data = await api('/api/proveedor/' + currentUser.id + '/perfil', { method: 'PUT', body: body });
  if (data.ok) { alert('Perfil actualizado'); } else { alert(data.error || 'Error'); }
}

/* ═══ FASE 6: MI CUENTA + VINCULACION ═══ */

async function renderMiCuenta(main) {
  const hasPhone = currentUser.telefono && currentUser.telefono.length >= 10;
  main.innerHTML = '<div class="page-header"><h2>Mi Cuenta</h2></div>' +
    '<div class="card"><h3>Datos de la cuenta</h3>' +
    '<div style="margin:12px 0"><div class="detail-row"><span class="label">Nombre</span><span class="value">' + currentUser.nombre + '</span></div>' +
    '<div class="detail-row"><span class="label">WhatsApp</span><span class="value">' + (hasPhone ? currentUser.telefono : '<span style="color:var(--orange)">No vinculado</span>') + '</span></div></div>' +
    (hasPhone ? '<p style="color:var(--green);font-size:14px">Tu cuenta web esta vinculada a WhatsApp. Las ordenes de ambos canales aparecen aqui.</p>' :
    '<div style="margin-top:16px;padding:16px;background:var(--gray-50);border-radius:var(--radius);border:1px solid var(--gray-200)">' +
      '<h4 style="margin-bottom:8px">Vincular WhatsApp</h4><p style="font-size:13px;color:var(--gray-500);margin-bottom:12px">Vincula tu numero para ver ordenes de WhatsApp en el portal.</p>' +
      '<div style="display:flex;gap:8px;align-items:end"><div class="form-group" style="flex:1"><label>Numero WhatsApp (10 digitos)</label><div class="phone-row"><select class="phone-country" id="link-country"><option value="52">+52</option><option value="1">+1</option></select><input type="tel" id="link-phone" class="phone-input" placeholder="33 1234 5678"></div></div>' +
      '<button class="btn-primary" style="width:auto;padding:10px 16px;margin-bottom:20px" onclick="vincularTelefono()">Vincular</button></div></div>') +
    '</div>';
}

async function vincularTelefono() {
  const code = document.getElementById('link-country')?.value || '52';
  const phone = document.getElementById('link-phone')?.value.replace(/[^0-9]/g, '');
  if (!phone || phone.length < 10) { alert('Ingresa un numero valido de 10 digitos'); return; }
  const fullPhone = code + phone;
  const data = await api('/api/vincular-telefono', { method: 'POST', body: { usuario_id: currentUser.id, telefono: fullPhone, codigo_pais: '+' + code } });
  if (data.ok) {
    currentUser.telefono = fullPhone;
    alert('Vinculado! ' + (data.ordenes_vinculadas > 0 ? data.ordenes_vinculadas + ' ordenes previas vinculadas.' : ''));
    renderView('mi-cuenta');
  } else { alert(data.error || 'Error'); }
}

/* ─── End of new views ─── */

function closeDetail() {
  document.getElementById('detail-overlay').classList.add('hidden');
}
function closeDetailIfOutside(e) {
  if (e.target === document.getElementById('detail-overlay')) closeDetail();
}

/* ─── Unified views with tabs ─── */

async function renderMisPedidosUnificado(main) {
  const tabs = [
    { id: 'pedidos', label: 'En proceso' },
    { id: 'activas', label: 'Ordenes activas' },
    { id: 'historial', label: 'Historial' },
  ];
  main.innerHTML = '<div class="page-header"><h2>Mis Pedidos</h2></div>' +
    '<div class="tabs">' + tabs.map(t =>
      '<button class="tab-btn" data-tab="' + t.id + '" onclick="switchTab(this, \\'mis-pedidos\\')">' + t.label + '</button>'
    ).join('') + '</div>' +
    '<div id="tab-content"></div>';
  main.querySelector('.tab-btn').classList.add('active');
  await renderTabContent('pedidos', 'mis-pedidos');
}

async function renderMiCuentaUnificado(main) {
  const tabs = [
    { id: 'cuenta', label: 'Mi cuenta' },
    { id: 'presupuestos', label: 'Presupuestos' },
    { id: 'costos', label: 'Costos' },
    { id: 'aprobaciones', label: 'Aprobaciones' },
  ];
  main.innerHTML = '<div class="page-header"><h2>Mi Cuenta</h2></div>' +
    '<div class="tabs">' + tabs.map(t =>
      '<button class="tab-btn" data-tab="' + t.id + '" onclick="switchTab(this, \\'mi-cuenta\\')">' + t.label + '</button>'
    ).join('') + '</div>' +
    '<div id="tab-content"></div>';
  main.querySelector('.tab-btn').classList.add('active');
  await renderTabContent('cuenta', 'mi-cuenta');
}

async function renderProveedorOrdenesUnificado(main) {
  const tabs = [
    { id: 'activas', label: 'Activas' },
    { id: 'historial', label: 'Historial' },
  ];
  main.innerHTML = '<div class="page-header"><h2>Ordenes</h2></div>' +
    '<div class="tabs">' + tabs.map(t =>
      '<button class="tab-btn" data-tab="' + t.id + '" onclick="switchTab(this, \\'ordenes-prov\\')">' + t.label + '</button>'
    ).join('') + '</div>' +
    '<div id="tab-content"></div>';
  main.querySelector('.tab-btn').classList.add('active');
  await renderTabContent('activas', 'ordenes-prov');
}

async function renderProveedorNegocio(main) {
  const tabs = [
    { id: 'calificaciones', label: 'Calificaciones' },
    { id: 'ingresos', label: 'Ingresos' },
    { id: 'desempeno', label: 'Desempeno' },
  ];
  main.innerHTML = '<div class="page-header"><h2>Mi Negocio</h2></div>' +
    '<div class="tabs">' + tabs.map(t =>
      '<button class="tab-btn" data-tab="' + t.id + '" onclick="switchTab(this, \\'mi-negocio\\')">' + t.label + '</button>'
    ).join('') + '</div>' +
    '<div id="tab-content"></div>';
  main.querySelector('.tab-btn').classList.add('active');
  await renderTabContent('calificaciones', 'mi-negocio');
}

async function renderProveedorPerfilUnificado(main) {
  const tabs = [
    { id: 'perfil', label: 'Datos' },
    { id: 'productos', label: 'Mis productos' },
  ];
  main.innerHTML = '<div class="page-header"><h2>Mi Perfil</h2></div>' +
    '<div class="tabs">' + tabs.map(t =>
      '<button class="tab-btn" data-tab="' + t.id + '" onclick="switchTab(this, \\'mi-perfil\\')">' + t.label + '</button>'
    ).join('') + '</div>' +
    '<div id="tab-content"></div>';
  main.querySelector('.tab-btn').classList.add('active');
  await renderTabContent('perfil', 'mi-perfil');
}

async function switchTab(btn, parentView) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  await renderTabContent(btn.dataset.tab, parentView);
}

async function renderTabContent(tab, parentView) {
  const tc = document.getElementById('tab-content');
  tc.innerHTML = '<div class="loading-center"><span class="spinner"></span></div>';
  try {
    if (parentView === 'mis-pedidos') {
      if (tab === 'pedidos') await renderMisPedidos(tc);
      else if (tab === 'activas') await renderClienteOrdenes(tc, 'activas');
      else if (tab === 'historial') await renderClienteOrdenes(tc, 'historial');
    } else if (parentView === 'mi-cuenta') {
      if (tab === 'cuenta') await renderMiCuenta(tc);
      else if (tab === 'presupuestos') await renderPresupuestos(tc);
      else if (tab === 'costos') await renderClienteCostos(tc);
      else if (tab === 'aprobaciones') await renderAprobaciones(tc);
    } else if (parentView === 'ordenes-prov') {
      if (tab === 'activas') await renderProveedorOrdenes(tc, 'activas');
      else if (tab === 'historial') await renderProveedorOrdenes(tc, 'historial');
    } else if (parentView === 'mi-negocio') {
      if (tab === 'calificaciones') await renderProveedorCalificaciones(tc);
      else if (tab === 'ingresos') await renderProveedorIngresos(tc);
      else if (tab === 'desempeno') await renderProveedorDesempeno(tc);
    } else if (parentView === 'mi-perfil') {
      if (tab === 'perfil') await renderProveedorPerfil(tc);
      else if (tab === 'productos') await renderProveedorProductos(tc);
    }
  } catch (e) {
    tc.innerHTML = '<div class="empty-state"><p>Error al cargar.</p></div>';
  }
}

/* ─── Keyboard ─── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDetail();
});
</script>
</body>
</html>"""
