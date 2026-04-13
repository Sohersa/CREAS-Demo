"""
Hub Central — Pagina maestra de administracion de ObraYa.
Acceso rapido a todos los modulos, KPIs en tiempo real, y estado del sistema.
"""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta

from app.database import get_db
from app.models.orden import Orden
from app.models.pedido import Pedido
from app.models.proveedor import Proveedor
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.miembro_empresa import MiembroEmpresa
from app.models.solicitud_proveedor import SolicitudProveedor
from app.models.aprobacion import Aprobacion
from app.models.cotizacion import Cotizacion
from app.utils.telefono import normalizar_telefono_mx

router = APIRouter(prefix="/hub", tags=["hub"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pydantic models for Gestion
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ProveedorInput(BaseModel):
    nombre: str
    telefono_whatsapp: str
    tipo: str = "mediano"
    municipio: str = ""
    direccion: str = ""
    categorias: str = "[]"
    email: str = ""


class UsuarioInput(BaseModel):
    telefono: str
    nombre: str
    email: str = ""
    tipo: str = "residente"
    empresa: str = ""
    municipio_principal: str = ""


class EmpresaInput(BaseModel):
    nombre: str
    rfc: str = ""
    direccion: str = ""
    telefono: str = ""
    email: str = ""
    requiere_aprobacion: bool = True
    limite_sin_aprobacion: float = 100000.0


class MiembroInput(BaseModel):
    usuario_id: int
    rol: str = "residente"
    puede_pedir: bool = True
    puede_aprobar: bool = False
    puede_pagar: bool = False
    limite_aprobacion: float = 50000.0


@router.get("/api/stats")
def hub_stats(db: Session = Depends(get_db)):
    """KPIs rapidos para el hub."""
    hoy = datetime.utcnow().date()
    hace_7d = datetime.utcnow() - timedelta(days=7)
    hace_30d = datetime.utcnow() - timedelta(days=30)

    # Contadores principales
    total_ordenes = db.query(func.count(Orden.id)).scalar() or 0
    ordenes_activas = db.query(func.count(Orden.id)).filter(
        Orden.status.notin_(["entregada", "cancelada"])
    ).scalar() or 0
    ordenes_hoy = db.query(func.count(Orden.id)).filter(
        func.date(Orden.created_at) == hoy
    ).scalar() or 0

    total_proveedores = db.query(func.count(Proveedor.id)).filter(Proveedor.activo == True).scalar() or 0
    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0

    pedidos_semana = db.query(func.count(Pedido.id)).filter(
        Pedido.created_at >= hace_7d
    ).scalar() or 0

    # Solicitudes pendientes de respuesta
    solicitudes_pendientes = db.query(func.count(SolicitudProveedor.id)).filter(
        SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"])
    ).scalar() or 0

    # Aprobaciones pendientes
    try:
        aprobaciones_pendientes = db.query(func.count(Aprobacion.id)).filter(
            Aprobacion.status == "pendiente"
        ).scalar() or 0
    except Exception:
        aprobaciones_pendientes = 0

    # Revenue (ordenes completadas ultimo mes)
    try:
        revenue_mes = db.query(func.sum(Orden.total)).filter(
            Orden.status == "entregada",
            Orden.created_at >= hace_30d
        ).scalar() or 0
    except Exception:
        revenue_mes = 0

    return {
        "total_ordenes": total_ordenes,
        "ordenes_activas": ordenes_activas,
        "ordenes_hoy": ordenes_hoy,
        "total_proveedores": total_proveedores,
        "total_usuarios": total_usuarios,
        "pedidos_semana": pedidos_semana,
        "solicitudes_pendientes": solicitudes_pendientes,
        "aprobaciones_pendientes": aprobaciones_pendientes,
        "revenue_mes": round(revenue_mes, 2),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GESTION — CRUD endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# --- Proveedores ---

@router.get("/api/proveedores")
def listar_proveedores(db: Session = Depends(get_db)):
    """Lista todos los proveedores activos."""
    proveedores = db.query(Proveedor).filter(Proveedor.activo == True).order_by(Proveedor.nombre).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "telefono": p.telefono_whatsapp,
            "municipio": p.municipio,
            "categorias": p.categorias,
            "calificacion": p.calificacion,
            "tipo": p.tipo,
            "email": p.email or "",
            "direccion": p.direccion or "",
        }
        for p in proveedores
    ]


@router.post("/api/proveedores")
def crear_proveedor_hub(body: ProveedorInput, db: Session = Depends(get_db)):
    """Crear proveedor + usuario asociado."""
    telefono_normalizado = normalizar_telefono_mx(body.telefono_whatsapp) if body.telefono_whatsapp else ""

    # Create proveedor
    proveedor = Proveedor(
        nombre=body.nombre,
        tipo=body.tipo,
        municipio=body.municipio,
        telefono_whatsapp=telefono_normalizado,
        categorias=body.categorias,
        email=body.email,
        direccion=body.direccion,
        activo=True,
    )
    db.add(proveedor)
    db.flush()

    # Create associated usuario (so provider can log in)
    usuario_existente = None
    if telefono_normalizado:
        usuario_existente = db.query(Usuario).filter(Usuario.telefono == telefono_normalizado).first()

    if not usuario_existente:
        usuario = Usuario(
            telefono=telefono_normalizado or None,
            nombre=body.nombre,
            email=body.email or None,
            tipo="proveedor",
            es_proveedor=True,
            proveedor_id=proveedor.id,
            municipio_principal=body.municipio,
        )
        db.add(usuario)

    db.commit()
    return {"ok": True, "id": proveedor.id, "nombre": proveedor.nombre}


@router.post("/api/proveedores/{proveedor_id}/onboarding")
def generar_link_onboarding(proveedor_id: int, db: Session = Depends(get_db)):
    """
    Genera un codigo de registro y link de WhatsApp para onboarding de proveedor.
    El proveedor manda 'REGISTRO {codigo}' por WhatsApp y queda vinculado.
    """
    import secrets
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return {"ok": False, "error": "Proveedor no encontrado"}

    # Generar codigo unico de 6 chars
    if not proveedor.codigo_registro:
        codigo = secrets.token_hex(3).upper()  # 6 chars hex
        proveedor.codigo_registro = codigo
        db.commit()
    else:
        codigo = proveedor.codigo_registro

    # Generar link de WhatsApp con mensaje pre-llenado
    from app.config import settings
    phone_id = settings.WHATSAPP_PHONE_ID
    wa_link = f"https://wa.me/?text=REGISTRO+{codigo}"

    return {
        "ok": True,
        "codigo": codigo,
        "link_whatsapp": wa_link,
        "instrucciones": f"El proveedor debe enviar 'REGISTRO {codigo}' por WhatsApp para vincularse.",
    }


# --- Usuarios / Clientes ---

@router.get("/api/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    """Lista todos los usuarios con info de empresa."""
    usuarios = db.query(Usuario).order_by(Usuario.nombre).all()
    return [
        {
            "id": u.id,
            "nombre": u.nombre or "",
            "telefono": u.telefono or "",
            "email": u.email or "",
            "tipo": u.tipo or "",
            "empresa": u.empresa or "",
            "empresa_id": u.empresa_id,
            "municipio": u.municipio_principal or "",
            "es_proveedor": u.es_proveedor or False,
            "proveedor_id": u.proveedor_id,
            "rol_empresa": u.rol_empresa or "",
            "created_at": u.created_at.isoformat() if u.created_at else "",
        }
        for u in usuarios
    ]


@router.post("/api/usuarios")
def crear_usuario_hub(body: UsuarioInput, db: Session = Depends(get_db)):
    """Crear usuario / cliente."""
    telefono_normalizado = normalizar_telefono_mx(body.telefono) if body.telefono else ""

    # Check existing
    if telefono_normalizado:
        existente = db.query(Usuario).filter(Usuario.telefono == telefono_normalizado).first()
        if existente:
            return {"error": f"Ya existe un usuario con telefono {telefono_normalizado}", "id": existente.id}

    usuario = Usuario(
        telefono=telefono_normalizado or None,
        nombre=body.nombre,
        email=body.email or None,
        tipo=body.tipo,
        empresa=body.empresa,
        municipio_principal=body.municipio_principal,
    )
    db.add(usuario)
    db.commit()
    return {"ok": True, "id": usuario.id, "nombre": usuario.nombre}


# --- Empresas ---

@router.get("/api/empresas")
def listar_empresas(db: Session = Depends(get_db)):
    """Lista todas las empresas con conteo de miembros."""
    empresas = db.query(Empresa).filter(Empresa.activo == True).order_by(Empresa.nombre).all()
    resultado = []
    for e in empresas:
        miembros_count = db.query(func.count(MiembroEmpresa.id)).filter(
            MiembroEmpresa.empresa_id == e.id,
            MiembroEmpresa.activo == True,
        ).scalar() or 0
        resultado.append({
            "id": e.id,
            "nombre": e.nombre,
            "rfc": e.rfc or "",
            "direccion": e.direccion or "",
            "telefono": e.telefono or "",
            "email": e.email or "",
            "requiere_aprobacion": e.requiere_aprobacion,
            "limite_sin_aprobacion": e.limite_sin_aprobacion or 0,
            "miembros": miembros_count,
        })
    return resultado


@router.post("/api/empresas")
def crear_empresa_hub(body: EmpresaInput, db: Session = Depends(get_db)):
    """Crear empresa constructora."""
    empresa = Empresa(
        nombre=body.nombre,
        rfc=body.rfc,
        direccion=body.direccion,
        telefono=body.telefono,
        email=body.email,
        requiere_aprobacion=body.requiere_aprobacion,
        limite_sin_aprobacion=body.limite_sin_aprobacion,
        activo=True,
    )
    db.add(empresa)
    db.commit()
    return {"ok": True, "id": empresa.id, "nombre": empresa.nombre}


@router.get("/api/empresas/{empresa_id}/miembros")
def listar_miembros(empresa_id: int, db: Session = Depends(get_db)):
    """Miembros de una empresa con roles y permisos."""
    miembros = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.empresa_id == empresa_id,
        MiembroEmpresa.activo == True,
    ).all()
    resultado = []
    for m in miembros:
        usuario = db.query(Usuario).filter(Usuario.id == m.usuario_id).first()
        resultado.append({
            "id": m.id,
            "usuario_id": m.usuario_id,
            "nombre": usuario.nombre if usuario else "?",
            "telefono": usuario.telefono if usuario else "",
            "rol": m.rol,
            "puede_pedir": m.puede_pedir,
            "puede_aprobar": m.puede_aprobar,
            "puede_pagar": m.puede_pagar,
            "limite_aprobacion": m.limite_aprobacion or 0,
        })
    return resultado


@router.post("/api/empresas/{empresa_id}/miembros")
def agregar_miembro_hub(empresa_id: int, body: MiembroInput, db: Session = Depends(get_db)):
    """Agregar miembro a empresa con rol y permisos."""
    # Verify empresa exists
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        return {"error": "Empresa no encontrada"}

    # Verify usuario exists
    usuario = db.query(Usuario).filter(Usuario.id == body.usuario_id).first()
    if not usuario:
        return {"error": "Usuario no encontrado"}

    # Check not already a member
    existente = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.empresa_id == empresa_id,
        MiembroEmpresa.usuario_id == body.usuario_id,
        MiembroEmpresa.activo == True,
    ).first()
    if existente:
        return {"error": "Este usuario ya es miembro de esta empresa"}

    miembro = MiembroEmpresa(
        empresa_id=empresa_id,
        usuario_id=body.usuario_id,
        rol=body.rol,
        puede_pedir=body.puede_pedir,
        puede_aprobar=body.puede_aprobar,
        puede_pagar=body.puede_pagar,
        limite_aprobacion=body.limite_aprobacion,
        activo=True,
    )
    db.add(miembro)

    # Update the usuario's empresa link
    usuario.empresa_id = empresa_id
    usuario.rol_empresa = body.rol
    usuario.empresa = empresa.nombre

    db.commit()
    return {"ok": True, "id": miembro.id, "nombre": usuario.nombre, "rol": body.rol}


@router.get("/", response_class=HTMLResponse)
def hub_page():
    """Master Admin Hub — pagina maestra."""
    return HTMLResponse(HUB_HTML)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTML / CSS / JS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HUB_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ObraYa — Hub Central</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --bg: #0a0e1a;
  --bg2: #111827;
  --card: #1a2332;
  --card-hover: #1f2b3d;
  --border: #2a3548;
  --orange: #ff6b2b;
  --orange-glow: rgba(255,107,43,0.15);
  --green: #22c55e;
  --blue: #3b82f6;
  --yellow: #eab308;
  --red: #ef4444;
  --text: #f1f5f9;
  --text2: #94a3b8;
  --text3: #64748b;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

/* ── Header ── */
.hub-header {
  background: linear-gradient(135deg, var(--bg2) 0%, #0f172a 100%);
  border-bottom: 1px solid var(--border);
  padding: 20px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hub-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--orange);
}
.hub-header h1 span { color: var(--text); font-weight: 400; }
.hub-header .status-dot {
  width: 10px; height: 10px;
  background: var(--green);
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.hub-header .status-text { color: var(--text2); font-size: 13px; }

/* ── KPIs ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  padding: 24px 32px;
}
.kpi-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.kpi-card .kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}
.kpi-card .kpi-label {
  font-size: 12px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.kpi-card.accent .kpi-value { color: var(--orange); }
.kpi-card.green .kpi-value { color: var(--green); }
.kpi-card.blue .kpi-value { color: var(--blue); }
.kpi-card.yellow .kpi-value { color: var(--yellow); }

/* ── Sections ── */
.hub-sections {
  padding: 0 32px 40px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 32px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* ── Module cards ── */
.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.module-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  color: var(--text);
  display: block;
  position: relative;
  overflow: hidden;
}
.module-card:hover {
  background: var(--card-hover);
  border-color: var(--orange);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
.module-card .module-icon {
  font-size: 32px;
  margin-bottom: 12px;
  display: block;
}
.module-card .module-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
}
.module-card .module-desc {
  font-size: 13px;
  color: var(--text3);
  line-height: 1.4;
}
.module-card .module-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  background: var(--orange);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
}
.module-card .module-badge.green { background: var(--green); }
.module-card .module-badge.blue { background: var(--blue); }
.module-card .module-badge.yellow { background: var(--yellow); }
.module-card .module-badge.red { background: var(--red); }

/* ── Flow diagrams ── */
.flow-container {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
}
.flow-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--orange);
}
.flow-steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.flow-step {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 13px;
  color: var(--text);
  text-align: center;
  min-width: 120px;
}
.flow-step.active { border-color: var(--green); background: rgba(34,197,94,0.1); }
.flow-step.pending { border-color: var(--yellow); background: rgba(234,179,8,0.1); }
.flow-arrow {
  color: var(--text3);
  font-size: 18px;
  flex-shrink: 0;
}

/* ── System status ── */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.status-item .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-item .dot.ok { background: var(--green); }
.status-item .dot.warn { background: var(--yellow); }
.status-item .dot.err { background: var(--red); }
.status-item .name { font-size: 13px; color: var(--text); flex:1; }
.status-item .detail { font-size: 11px; color: var(--text3); }

/* ── Gestion tabs ── */
.gestion-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.gestion-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
}
.gestion-tab {
  flex: 1;
  padding: 14px 20px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--text3);
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
  background: none;
  border-top: none;
  border-left: none;
  border-right: none;
}
.gestion-tab:hover { color: var(--text2); background: var(--bg2); }
.gestion-tab.active { color: var(--orange); border-bottom-color: var(--orange); background: var(--bg2); }
.gestion-panel { display: none; padding: 24px; }
.gestion-panel.active { display: block; }

/* ── Tables ── */
.g-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 20px;
}
.g-table th {
  text-align: left;
  padding: 10px 12px;
  color: var(--text3);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
.g-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(42,53,72,0.5);
  color: var(--text);
}
.g-table tr:hover td { background: rgba(255,107,43,0.04); }

/* ── Badges ── */
.g-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}
.g-badge.grande { background: rgba(59,130,246,0.15); color: var(--blue); }
.g-badge.mediano { background: rgba(234,179,8,0.15); color: var(--yellow); }
.g-badge.pequeno { background: rgba(148,163,184,0.15); color: var(--text2); }
.g-badge.demo { background: rgba(239,68,68,0.15); color: var(--red); }
.g-badge.perm-yes { background: rgba(34,197,94,0.15); color: var(--green); }
.g-badge.perm-no { background: rgba(148,163,184,0.1); color: var(--text3); }
.g-badge.rol { background: rgba(255,107,43,0.15); color: var(--orange); }

/* ── Forms ── */
.g-form {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
}
.g-form h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--orange);
  margin-bottom: 14px;
}
.g-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.g-form-group { display: flex; flex-direction: column; gap: 4px; }
.g-form-group label { font-size: 11px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.3px; }
.g-form-group input,
.g-form-group select {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--text);
  font-size: 13px;
  outline: none;
}
.g-form-group input:focus,
.g-form-group select:focus { border-color: var(--orange); }
.g-btn {
  background: var(--orange);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 14px;
  transition: opacity 0.2s;
}
.g-btn:hover { opacity: 0.85; }
.g-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.g-msg {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-top: 10px;
  display: none;
}
.g-msg.ok { display: block; background: rgba(34,197,94,0.12); color: var(--green); border: 1px solid rgba(34,197,94,0.3); }
.g-msg.err { display: block; background: rgba(239,68,68,0.12); color: var(--red); border: 1px solid rgba(239,68,68,0.3); }

/* ── Empresa detail ── */
.empresa-row { cursor: pointer; }
.empresa-row:hover td { background: rgba(255,107,43,0.08); }
.empresa-detail {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}
.empresa-detail h4 { color: var(--orange); margin-bottom: 12px; }
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}
.filter-bar select {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 12px;
  color: var(--text);
  font-size: 13px;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .hub-header { padding: 16px; }
  .kpi-grid { padding: 16px; grid-template-columns: repeat(2, 1fr); }
  .hub-sections { padding: 0 16px 32px; }
  .modules-grid { grid-template-columns: 1fr; }
  .flow-steps { flex-direction: column; }
  .flow-arrow { transform: rotate(90deg); }
  .gestion-tabs { flex-direction: column; }
  .g-form-grid { grid-template-columns: 1fr; }
  .g-table { font-size: 12px; }
  .g-table th, .g-table td { padding: 8px 6px; }
}
</style>
</head>
<body>

<!-- Header -->
<div class="hub-header">
  <div>
    <h1>ObraYa <span>Hub Central</span></h1>
  </div>
  <div style="display:flex;align-items:center;gap:8px">
    <span class="status-dot"></span>
    <span class="status-text" id="statusText">Conectando...</span>
  </div>
</div>

<!-- KPIs -->
<div class="kpi-grid" id="kpiGrid">
  <div class="kpi-card accent"><div class="kpi-value" id="kpiOrdenesActivas">-</div><div class="kpi-label">Ordenes Activas</div></div>
  <div class="kpi-card green"><div class="kpi-value" id="kpiOrdenesHoy">-</div><div class="kpi-label">Ordenes Hoy</div></div>
  <div class="kpi-card blue"><div class="kpi-value" id="kpiProveedores">-</div><div class="kpi-label">Proveedores</div></div>
  <div class="kpi-card"><div class="kpi-value" id="kpiUsuarios">-</div><div class="kpi-label">Usuarios</div></div>
  <div class="kpi-card yellow"><div class="kpi-value" id="kpiSolicitudes">-</div><div class="kpi-label">Cotizaciones Pendientes</div></div>
  <div class="kpi-card"><div class="kpi-value" id="kpiPedidosSemana">-</div><div class="kpi-label">Pedidos (7 dias)</div></div>
  <div class="kpi-card green"><div class="kpi-value" id="kpiRevenue">-</div><div class="kpi-label">Revenue (30 dias)</div></div>
  <div class="kpi-card" id="kpiAprobCard"><div class="kpi-value" id="kpiAprobaciones">-</div><div class="kpi-label">Aprobaciones Pendientes</div></div>
</div>

<div class="hub-sections">

  <!-- ═══ MODULOS PRINCIPALES ═══ -->
  <div class="section-title">Modulos Principales</div>
  <div class="modules-grid">
    <a class="module-card" href="/admin/" target="_blank">
      <span class="module-icon">&#9881;</span>
      <div class="module-name">Panel Admin</div>
      <div class="module-desc">Proveedores, catalogo, ordenes, WhatsApp masivo, gestionar todo el backend</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/dashboard/" target="_blank">
      <span class="module-icon">&#128202;</span>
      <div class="module-name">Dashboard Analytics</div>
      <div class="module-desc">KPIs de negocio, pricing intelligence, metricas de proveedores y usuarios</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/portal/" target="_blank">
      <span class="module-icon">&#128722;</span>
      <div class="module-name">Portal Clientes</div>
      <div class="module-desc">Crear pedidos, comparar cotizaciones, seguimiento de ordenes, pagos</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/portal/" target="_blank">
      <span class="module-icon">&#128666;</span>
      <div class="module-name">Portal Proveedores</div>
      <div class="module-desc">Ordenes entrantes, productos/precios, calificaciones, ingresos, desempeno</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/sim/" target="_blank">
      <span class="module-icon">&#129518;</span>
      <div class="module-name">Simulador WhatsApp</div>
      <div class="module-desc">Probar conversaciones con Nico sin usar WhatsApp real — testing completo</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/" target="_blank">
      <span class="module-icon">&#127968;</span>
      <div class="module-name">Landing Page</div>
      <div class="module-desc">Pagina publica de ObraYa — registro de usuarios, login OAuth</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/precios/" target="_blank">
      <span class="module-icon">&#128176;</span>
      <div class="module-name">Inteligencia de Precios</div>
      <div class="module-desc">Mega base de datos de costos — busqueda, historial, ranking y analisis por producto, proveedor y zona</div>
      <span class="module-badge green">Completo</span>
    </a>
  </div>

  <!-- ═══ MODULOS FINANCIEROS ═══ -->
  <div class="section-title">Financiero y Control</div>
  <div class="modules-grid">
    <a class="module-card" href="/presupuesto/" target="_blank">
      <span class="module-icon">&#128200;</span>
      <div class="module-name">Presupuestos de Obra</div>
      <div class="module-desc">Crear presupuestos por obra, partidas, tracking de consumo vs planeado</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/aprobaciones/" target="_blank">
      <span class="module-icon">&#9989;</span>
      <div class="module-name">Aprobaciones</div>
      <div class="module-desc">Flujo de aprobacion entre obra y oficina — aprobar/rechazar compras</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/credito/" target="_blank">
      <span class="module-icon">&#127974;</span>
      <div class="module-name">Credit Scoring</div>
      <div class="module-desc">Perfiles crediticios, historial de pago, evaluacion de riesgo</div>
      <span class="module-badge green">Completo</span>
    </a>
    <a class="module-card" href="/pagos/checkout/test" target="_blank">
      <span class="module-icon">&#128179;</span>
      <div class="module-name">Sistema de Pagos</div>
      <div class="module-desc">Stripe Checkout con 2% comision ObraYa — pagos por orden</div>
      <span class="module-badge yellow">Falta Stripe Key</span>
    </a>
  </div>

  <!-- ═══ FLUJOS DEL SISTEMA ═══ -->
  <div class="section-title">Flujos del Sistema</div>

  <!-- Flujo de Pedido -->
  <div class="flow-container">
    <div class="flow-title">Flujo de Pedido (WhatsApp o Web)</div>
    <div class="flow-steps">
      <div class="flow-step active">Cliente pide materiales</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">IA genera lista + cantidades</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Cotizacion a N proveedores via WhatsApp</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Proveedores responden con precios</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Comparativa al cliente</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Cliente elige proveedor</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Orden creada</div>
    </div>
  </div>

  <!-- Flujo de Aprobacion -->
  <div class="flow-container">
    <div class="flow-title">Flujo de Aprobacion (Empresa)</div>
    <div class="flow-steps">
      <div class="flow-step active">Personal de obra crea pedido</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Sistema verifica monto vs limite</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">WhatsApp al aprobador con detalle</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Aprobador responde APROBAR / RECHAZAR</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Orden se crea o se cancela</div>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--text3)">
      Reglas: Si monto &gt; limite del rol → requiere aprobacion. Expira en 24h. Aprobadores reciben WhatsApp con resumen del pedido.
    </div>
  </div>

  <!-- Flujo de Pagos -->
  <div class="flow-container">
    <div class="flow-title">Flujo de Pagos (Stripe)</div>
    <div class="flow-steps">
      <div class="flow-step active">Orden confirmada</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Desglose: subtotal + 2% comision</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Sesion Stripe Checkout</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step pending">Cliente paga (falta STRIPE_SECRET_KEY)</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Webhook confirma pago</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Orden marcada como pagada</div>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--text3)">
      Pendiente: Configurar STRIPE_SECRET_KEY y STRIPE_WEBHOOK_SECRET en Railway para activar pagos reales.
    </div>
  </div>

  <!-- Flujo de Credito -->
  <div class="flow-container">
    <div class="flow-title">Flujo de Credit Scoring</div>
    <div class="flow-steps">
      <div class="flow-step active">Historial de compras + pagos</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Score 0-100 (puntualidad, volumen, consistencia)</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Clasificacion: Excelente/Bueno/Regular/Riesgo</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Limite de credito recomendado</div>
      <span class="flow-arrow">&#10132;</span>
      <div class="flow-step active">Aprobacion automatica o manual</div>
    </div>
  </div>

  <!-- ═══ ESTADO DEL SISTEMA ═══ -->
  <div class="section-title">Estado de Integraciones</div>
  <div class="status-grid" id="statusGrid">
    <div class="status-item"><div class="dot ok"></div><div class="name">WhatsApp (Meta Cloud API)</div><div class="detail">Activo</div></div>
    <div class="status-item"><div class="dot ok"></div><div class="name">WhatsApp (Twilio Fallback)</div><div class="detail">Activo</div></div>
    <div class="status-item"><div class="dot ok"></div><div class="name">Anthropic Claude (IA)</div><div class="detail">Agente Nico</div></div>
    <div class="status-item"><div class="dot ok"></div><div class="name">Groq Whisper (Transcripcion)</div><div class="detail">Audio → Texto</div></div>
    <div class="status-item"><div class="dot ok"></div><div class="name">Google OAuth</div><div class="detail">Login web</div></div>
    <div class="status-item"><div class="dot warn"></div><div class="name">Stripe Payments</div><div class="detail">Falta API Key</div></div>
    <div class="status-item"><div class="dot ok"></div><div class="name">Nominatim Geocoding</div><div class="detail">Ubicaciones</div></div>
    <div class="status-item"><div class="dot ok"></div><div class="name">SQLite Database</div><div class="detail">Operativa</div></div>
  </div>

  <!-- ═══ APIS Y ENDPOINTS ═══ -->
  <div class="section-title">APIs Disponibles (para integraciones)</div>
  <div class="modules-grid">
    <div class="module-card" onclick="window.open('/docs','_blank')">
      <span class="module-icon">&#128214;</span>
      <div class="module-name">Swagger / OpenAPI</div>
      <div class="module-desc">Documentacion interactiva de TODOS los endpoints — /docs</div>
    </div>
    <div class="module-card" onclick="window.open('/health','_blank')">
      <span class="module-icon">&#128154;</span>
      <div class="module-name">Health Check</div>
      <div class="module-desc">GET /health — estado del servidor</div>
    </div>
    <div class="module-card" onclick="window.open('/admin/api/logs','_blank')">
      <span class="module-icon">&#128220;</span>
      <div class="module-name">Server Logs</div>
      <div class="module-desc">Ultimos 200 logs del servidor en tiempo real</div>
    </div>
  </div>

  <!-- ═══ GESTION — ALTA DE PROVEEDORES, CLIENTES Y EQUIPOS ═══ -->
  <div class="section-title">Gestion — Alta de Proveedores, Clientes y Equipos</div>
  <div class="gestion-card">
    <div class="gestion-tabs">
      <button class="gestion-tab active" onclick="switchGTab('proveedores')">Proveedores</button>
      <button class="gestion-tab" onclick="switchGTab('usuarios')">Clientes / Usuarios</button>
      <button class="gestion-tab" onclick="switchGTab('empresas')">Empresas y Equipos</button>
    </div>

    <!-- TAB 1: Proveedores -->
    <div class="gestion-panel active" id="gpanel-proveedores">
      <div id="proveedores-table-wrap">
        <table class="g-table">
          <thead><tr>
            <th>Nombre</th><th>Telefono</th><th>Municipio</th><th>Categorias</th><th>Calif.</th><th>Tipo</th>
          </tr></thead>
          <tbody id="proveedores-tbody"><tr><td colspan="6" style="color:var(--text3);text-align:center">Cargando...</td></tr></tbody>
        </table>
      </div>
      <div class="g-form">
        <h4>+ Nuevo Proveedor</h4>
        <div class="g-form-grid">
          <div class="g-form-group"><label>Nombre *</label><input id="prov-nombre" placeholder="Materiales El Sol"></div>
          <div class="g-form-group"><label>WhatsApp *</label><input id="prov-tel" placeholder="3312345678"></div>
          <div class="g-form-group"><label>Tipo</label>
            <select id="prov-tipo"><option value="grande">Grande</option><option value="mediano" selected>Mediano</option><option value="pequeno">Pequeno</option></select>
          </div>
          <div class="g-form-group"><label>Municipio</label><input id="prov-mun" placeholder="Zapopan"></div>
          <div class="g-form-group"><label>Email</label><input id="prov-email" placeholder="contacto@ejemplo.com"></div>
          <div class="g-form-group"><label>Direccion</label><input id="prov-dir" placeholder="Av. Vallarta 1234"></div>
          <div class="g-form-group"><label>Categorias (JSON)</label><input id="prov-cats" placeholder='["concreto","acero"]' value="[]"></div>
        </div>
        <button class="g-btn" onclick="crearProveedor()">Crear Proveedor</button>
        <div class="g-msg" id="prov-msg"></div>
      </div>
    </div>

    <!-- TAB 2: Clientes / Usuarios -->
    <div class="gestion-panel" id="gpanel-usuarios">
      <div class="filter-bar">
        <label style="font-size:12px;color:var(--text3)">Filtrar por tipo:</label>
        <select id="usuarios-filtro" onchange="filtrarUsuarios()">
          <option value="">Todos</option>
          <option value="residente">Residente</option>
          <option value="maestro_obra">Maestro de Obra</option>
          <option value="comprador">Comprador</option>
          <option value="particular">Particular</option>
          <option value="proveedor">Proveedor</option>
        </select>
      </div>
      <div id="usuarios-table-wrap">
        <table class="g-table">
          <thead><tr>
            <th>Nombre</th><th>Telefono</th><th>Email</th><th>Tipo</th><th>Empresa</th><th>Municipio</th>
          </tr></thead>
          <tbody id="usuarios-tbody"><tr><td colspan="6" style="color:var(--text3);text-align:center">Cargando...</td></tr></tbody>
        </table>
      </div>
      <div class="g-form">
        <h4>+ Nuevo Usuario / Cliente</h4>
        <div class="g-form-grid">
          <div class="g-form-group"><label>Nombre *</label><input id="usr-nombre" placeholder="Juan Perez"></div>
          <div class="g-form-group"><label>Telefono *</label><input id="usr-tel" placeholder="3312345678"></div>
          <div class="g-form-group"><label>Email</label><input id="usr-email" placeholder="juan@ejemplo.com"></div>
          <div class="g-form-group"><label>Tipo</label>
            <select id="usr-tipo"><option value="residente">Residente</option><option value="maestro_obra">Maestro de Obra</option><option value="comprador">Comprador</option><option value="particular">Particular</option></select>
          </div>
          <div class="g-form-group"><label>Empresa</label><input id="usr-empresa" placeholder="Constructora ABC"></div>
          <div class="g-form-group"><label>Municipio</label><input id="usr-mun" placeholder="Guadalajara"></div>
        </div>
        <button class="g-btn" onclick="crearUsuario()">Crear Usuario</button>
        <div class="g-msg" id="usr-msg"></div>
      </div>
    </div>

    <!-- TAB 3: Empresas y Equipos -->
    <div class="gestion-panel" id="gpanel-empresas">
      <div id="empresas-list-wrap">
        <table class="g-table">
          <thead><tr>
            <th>Empresa</th><th>RFC</th><th>Telefono</th><th>Email</th><th>Miembros</th><th>Aprobacion</th><th>Limite s/Aprob</th>
          </tr></thead>
          <tbody id="empresas-tbody"><tr><td colspan="7" style="color:var(--text3);text-align:center">Cargando...</td></tr></tbody>
        </table>
      </div>

      <div id="empresa-detail-wrap" style="display:none">
        <div class="empresa-detail">
          <h4 id="empresa-detail-title">Miembros de ...</h4>
          <table class="g-table">
            <thead><tr>
              <th>Nombre</th><th>Telefono</th><th>Rol</th><th>Pedir</th><th>Aprobar</th><th>Pagar</th><th>Limite</th>
            </tr></thead>
            <tbody id="miembros-tbody"></tbody>
          </table>
          <button class="g-btn" style="background:var(--text3);margin-bottom:12px" onclick="cerrarDetalle()">Cerrar</button>
        </div>

        <!-- Add member form -->
        <div class="g-form" id="agregar-miembro-form">
          <h4>+ Agregar Miembro a <span id="miembro-empresa-nombre">...</span></h4>
          <div class="g-form-grid">
            <div class="g-form-group"><label>Usuario</label>
              <select id="miembro-usuario"><option value="">Cargando usuarios...</option></select>
            </div>
            <div class="g-form-group"><label>Rol</label>
              <select id="miembro-rol"><option value="residente">Residente</option><option value="superintendente">Superintendente</option><option value="compras">Compras</option><option value="director">Director</option><option value="admin">Admin</option></select>
            </div>
            <div class="g-form-group"><label>Puede Pedir</label><select id="miembro-pedir"><option value="true">Si</option><option value="false">No</option></select></div>
            <div class="g-form-group"><label>Puede Aprobar</label><select id="miembro-aprobar"><option value="false">No</option><option value="true">Si</option></select></div>
            <div class="g-form-group"><label>Puede Pagar</label><select id="miembro-pagar"><option value="false">No</option><option value="true">Si</option></select></div>
            <div class="g-form-group"><label>Limite Aprobacion</label><input id="miembro-limite" type="number" value="50000"></div>
          </div>
          <button class="g-btn" onclick="agregarMiembro()">Agregar Miembro</button>
          <div class="g-msg" id="miembro-msg"></div>
        </div>
      </div>

      <div class="g-form" style="margin-top:20px">
        <h4>+ Nueva Empresa</h4>
        <div class="g-form-grid">
          <div class="g-form-group"><label>Nombre *</label><input id="emp-nombre" placeholder="Constructora XYZ"></div>
          <div class="g-form-group"><label>RFC</label><input id="emp-rfc" placeholder="CXY123456AB1"></div>
          <div class="g-form-group"><label>Direccion</label><input id="emp-dir" placeholder="Av. Americas 500"></div>
          <div class="g-form-group"><label>Telefono</label><input id="emp-tel" placeholder="3398765432"></div>
          <div class="g-form-group"><label>Email</label><input id="emp-email" placeholder="admin@constructora.com"></div>
          <div class="g-form-group"><label>Requiere Aprobacion</label><select id="emp-aprob"><option value="true">Si</option><option value="false">No</option></select></div>
          <div class="g-form-group"><label>Limite sin Aprobacion</label><input id="emp-limite" type="number" value="100000"></div>
        </div>
        <button class="g-btn" onclick="crearEmpresa()">Crear Empresa</button>
        <div class="g-msg" id="emp-msg"></div>
      </div>
    </div>
  </div>

</div>

<script>
async function loadKPIs() {
  try {
    const r = await fetch('/hub/api/stats');
    const d = await r.json();
    document.getElementById('kpiOrdenesActivas').textContent = d.ordenes_activas;
    document.getElementById('kpiOrdenesHoy').textContent = d.ordenes_hoy;
    document.getElementById('kpiProveedores').textContent = d.total_proveedores;
    document.getElementById('kpiUsuarios').textContent = d.total_usuarios;
    document.getElementById('kpiSolicitudes').textContent = d.solicitudes_pendientes;
    document.getElementById('kpiPedidosSemana').textContent = d.pedidos_semana;
    document.getElementById('kpiRevenue').textContent = '$' + (d.revenue_mes || 0).toLocaleString('es-MX');
    document.getElementById('kpiAprobaciones').textContent = d.aprobaciones_pendientes;
    if (d.aprobaciones_pendientes > 0) {
      document.getElementById('kpiAprobCard').classList.add('yellow');
    }
    document.getElementById('statusText').textContent = 'Sistema operativo';
  } catch(e) {
    document.getElementById('statusText').textContent = 'Error cargando datos';
  }
}
loadKPIs();
setInterval(loadKPIs, 30000);

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// GESTION — Tab switching, data loading, forms
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let _allUsuarios = [];
let _selectedEmpresaId = null;

function switchGTab(tab) {
  document.querySelectorAll('.gestion-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.gestion-panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('gpanel-' + tab).classList.add('active');
}

// ── Proveedores ──
async function loadProveedores() {
  try {
    const r = await fetch('/hub/api/proveedores');
    const data = await r.json();
    const tbody = document.getElementById('proveedores-tbody');
    if (!data.length) { tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text3);text-align:center">Sin proveedores registrados</td></tr>'; return; }
    tbody.innerHTML = data.map(p => {
      let cats = '—';
      try { const arr = JSON.parse(p.categorias || '[]'); cats = arr.length ? arr.join(', ') : '—'; } catch(e) { cats = p.categorias || '—'; }
      const tipoCls = p.tipo === 'grande' ? 'grande' : p.tipo === 'mediano' ? 'mediano' : 'pequeno';
      const demoTag = (p.nombre || '').toLowerCase().includes('demo') ? ' <span class="g-badge demo">Demo</span>' : '';
      return '<tr>' +
        '<td>' + (p.nombre || '') + demoTag + '</td>' +
        '<td>' + (p.telefono || '') + '</td>' +
        '<td>' + (p.municipio || '') + '</td>' +
        '<td>' + cats + '</td>' +
        '<td>' + (p.calificacion != null ? p.calificacion.toFixed(1) : '—') + '</td>' +
        '<td><span class="g-badge ' + tipoCls + '">' + (p.tipo || '') + '</span></td>' +
      '</tr>';
    }).join('');
  } catch(e) { console.error('loadProveedores', e); }
}

async function crearProveedor() {
  const nombre = document.getElementById('prov-nombre').value.trim();
  const tel = document.getElementById('prov-tel').value.trim();
  if (!nombre || !tel) { showMsg('prov-msg', 'Nombre y WhatsApp son obligatorios', true); return; }
  try {
    const r = await fetch('/hub/api/proveedores', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        nombre, telefono_whatsapp: tel,
        tipo: document.getElementById('prov-tipo').value,
        municipio: document.getElementById('prov-mun').value,
        email: document.getElementById('prov-email').value,
        direccion: document.getElementById('prov-dir').value,
        categorias: document.getElementById('prov-cats').value || '[]',
      })
    });
    const d = await r.json();
    if (d.error) { showMsg('prov-msg', d.error, true); return; }
    showMsg('prov-msg', 'Proveedor "' + d.nombre + '" creado (ID ' + d.id + ') + usuario asociado', false);
    ['prov-nombre','prov-tel','prov-mun','prov-email','prov-dir'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('prov-cats').value = '[]';
    loadProveedores();
    loadKPIs();
  } catch(e) { showMsg('prov-msg', 'Error de red: ' + e.message, true); }
}

// ── Usuarios ──
async function loadUsuarios() {
  try {
    const r = await fetch('/hub/api/usuarios');
    _allUsuarios = await r.json();
    renderUsuarios(_allUsuarios);
    populateUsuarioSelect();
  } catch(e) { console.error('loadUsuarios', e); }
}

function filtrarUsuarios() {
  const tipo = document.getElementById('usuarios-filtro').value;
  const filtered = tipo ? _allUsuarios.filter(u => u.tipo === tipo) : _allUsuarios;
  renderUsuarios(filtered);
}

function renderUsuarios(list) {
  const tbody = document.getElementById('usuarios-tbody');
  if (!list.length) { tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text3);text-align:center">Sin usuarios</td></tr>'; return; }
  tbody.innerHTML = list.map(u => {
    const demoTag = (u.nombre || '').toLowerCase().includes('demo') ? ' <span class="g-badge demo">Demo</span>' : '';
    const provTag = u.es_proveedor ? ' <span class="g-badge rol">Prov</span>' : '';
    return '<tr>' +
      '<td>' + (u.nombre || '—') + demoTag + provTag + '</td>' +
      '<td>' + (u.telefono || '') + '</td>' +
      '<td>' + (u.email || '') + '</td>' +
      '<td>' + (u.tipo || '') + '</td>' +
      '<td>' + (u.empresa || '') + '</td>' +
      '<td>' + (u.municipio || '') + '</td>' +
    '</tr>';
  }).join('');
}

async function crearUsuario() {
  const nombre = document.getElementById('usr-nombre').value.trim();
  const tel = document.getElementById('usr-tel').value.trim();
  if (!nombre || !tel) { showMsg('usr-msg', 'Nombre y Telefono son obligatorios', true); return; }
  try {
    const r = await fetch('/hub/api/usuarios', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        nombre, telefono: tel,
        email: document.getElementById('usr-email').value,
        tipo: document.getElementById('usr-tipo').value,
        empresa: document.getElementById('usr-empresa').value,
        municipio_principal: document.getElementById('usr-mun').value,
      })
    });
    const d = await r.json();
    if (d.error) { showMsg('usr-msg', d.error, true); return; }
    showMsg('usr-msg', 'Usuario "' + d.nombre + '" creado (ID ' + d.id + ')', false);
    ['usr-nombre','usr-tel','usr-email','usr-empresa','usr-mun'].forEach(id => document.getElementById(id).value = '');
    loadUsuarios();
    loadKPIs();
  } catch(e) { showMsg('usr-msg', 'Error de red: ' + e.message, true); }
}

// ── Empresas ──
async function loadEmpresas() {
  try {
    const r = await fetch('/hub/api/empresas');
    const data = await r.json();
    const tbody = document.getElementById('empresas-tbody');
    if (!data.length) { tbody.innerHTML = '<tr><td colspan="7" style="color:var(--text3);text-align:center">Sin empresas registradas</td></tr>'; return; }
    tbody.innerHTML = data.map(e => {
      const safeNombre = (e.nombre || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;');
      return '<tr class="empresa-row" data-eid="' + e.id + '" data-ename="' + safeNombre + '" onclick="verMiembros(this.dataset.eid, this.dataset.ename)">' +
        '<td><strong>' + (e.nombre || '') + '</strong></td>' +
        '<td>' + (e.rfc || '—') + '</td>' +
        '<td>' + (e.telefono || '') + '</td>' +
        '<td>' + (e.email || '') + '</td>' +
        '<td><span class="g-badge rol">' + e.miembros + '</span></td>' +
        '<td>' + (e.requiere_aprobacion ? '<span class="g-badge perm-yes">Si</span>' : '<span class="g-badge perm-no">No</span>') + '</td>' +
        '<td>$' + (e.limite_sin_aprobacion || 0).toLocaleString('es-MX') + '</td>' +
      '</tr>';
    }).join('');
  } catch(e) { console.error('loadEmpresas', e); }
}

async function verMiembros(empresaId, nombre) {
  _selectedEmpresaId = parseInt(empresaId);
  document.getElementById('empresa-detail-wrap').style.display = 'block';
  document.getElementById('empresa-detail-title').textContent = 'Miembros de ' + nombre;
  document.getElementById('miembro-empresa-nombre').textContent = nombre;
  try {
    const r = await fetch('/hub/api/empresas/' + empresaId + '/miembros');
    const data = await r.json();
    const tbody = document.getElementById('miembros-tbody');
    if (!data.length) { tbody.innerHTML = '<tr><td colspan="7" style="color:var(--text3);text-align:center">Sin miembros</td></tr>'; return; }
    tbody.innerHTML = data.map(m => {
      const permBadge = (val, label) => val ? '<span class="g-badge perm-yes">' + label + '</span>' : '<span class="g-badge perm-no">—</span>';
      return '<tr>' +
        '<td>' + (m.nombre || '') + '</td>' +
        '<td>' + (m.telefono || '') + '</td>' +
        '<td><span class="g-badge rol">' + (m.rol || '') + '</span></td>' +
        '<td>' + permBadge(m.puede_pedir, 'Pedir') + '</td>' +
        '<td>' + permBadge(m.puede_aprobar, 'Aprobar') + '</td>' +
        '<td>' + permBadge(m.puede_pagar, 'Pagar') + '</td>' +
        '<td>$' + (m.limite_aprobacion || 0).toLocaleString('es-MX') + '</td>' +
      '</tr>';
    }).join('');
  } catch(e) { console.error('verMiembros', e); }
}

function cerrarDetalle() {
  document.getElementById('empresa-detail-wrap').style.display = 'none';
  _selectedEmpresaId = null;
}

function populateUsuarioSelect() {
  const sel = document.getElementById('miembro-usuario');
  const nonProv = _allUsuarios.filter(u => !u.es_proveedor);
  sel.innerHTML = '<option value="">-- Seleccionar usuario --</option>' +
    nonProv.map(u => '<option value="' + u.id + '">' + (u.nombre || 'ID ' + u.id) + ' (' + (u.telefono || u.email || '') + ')</option>').join('');
}

async function agregarMiembro() {
  if (!_selectedEmpresaId) { showMsg('miembro-msg', 'Selecciona una empresa primero', true); return; }
  const uid = document.getElementById('miembro-usuario').value;
  if (!uid) { showMsg('miembro-msg', 'Selecciona un usuario', true); return; }
  try {
    const r = await fetch('/hub/api/empresas/' + _selectedEmpresaId + '/miembros', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        usuario_id: parseInt(uid),
        rol: document.getElementById('miembro-rol').value,
        puede_pedir: document.getElementById('miembro-pedir').value === 'true',
        puede_aprobar: document.getElementById('miembro-aprobar').value === 'true',
        puede_pagar: document.getElementById('miembro-pagar').value === 'true',
        limite_aprobacion: parseFloat(document.getElementById('miembro-limite').value) || 50000,
      })
    });
    const d = await r.json();
    if (d.error) { showMsg('miembro-msg', d.error, true); return; }
    showMsg('miembro-msg', d.nombre + ' agregado como ' + d.rol, false);
    verMiembros(_selectedEmpresaId, document.getElementById('empresa-detail-title').textContent.replace('Miembros de ', ''));
    loadEmpresas();
  } catch(e) { showMsg('miembro-msg', 'Error: ' + e.message, true); }
}

async function crearEmpresa() {
  const nombre = document.getElementById('emp-nombre').value.trim();
  if (!nombre) { showMsg('emp-msg', 'El nombre es obligatorio', true); return; }
  try {
    const r = await fetch('/hub/api/empresas', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        nombre,
        rfc: document.getElementById('emp-rfc').value,
        direccion: document.getElementById('emp-dir').value,
        telefono: document.getElementById('emp-tel').value,
        email: document.getElementById('emp-email').value,
        requiere_aprobacion: document.getElementById('emp-aprob').value === 'true',
        limite_sin_aprobacion: parseFloat(document.getElementById('emp-limite').value) || 100000,
      })
    });
    const d = await r.json();
    if (d.error) { showMsg('emp-msg', d.error, true); return; }
    showMsg('emp-msg', 'Empresa "' + d.nombre + '" creada (ID ' + d.id + ')', false);
    ['emp-nombre','emp-rfc','emp-dir','emp-tel','emp-email'].forEach(id => document.getElementById(id).value = '');
    loadEmpresas();
  } catch(e) { showMsg('emp-msg', 'Error: ' + e.message, true); }
}

// ── Helpers ──
function showMsg(id, text, isErr) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = 'g-msg ' + (isErr ? 'err' : 'ok');
  setTimeout(() => { el.className = 'g-msg'; el.textContent = ''; }, 5000);
}

// Load all gestion data on page load
loadProveedores();
loadUsuarios();
loadEmpresas();
</script>

</body>
</html>"""
