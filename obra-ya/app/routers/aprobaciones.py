"""
Router de aprobaciones corporativas.
API endpoints para gestionar flujo de aprobacion de compras.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.aprobacion import Aprobacion
from app.models.orden import Orden
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.miembro_empresa import MiembroEmpresa
from app.services.aprobacion_service import (
    necesita_aprobacion,
    solicitar_aprobacion,
    aprobar_orden,
    rechazar_orden,
    obtener_aprobaciones_pendientes,
    verificar_expiradas,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/aprobaciones", tags=["aprobaciones"])


# ─── Schemas ─────────────────────────────────────────────────────

class SolicitudInput(BaseModel):
    orden_id: int
    usuario_id: int
    nota: str = ""

class AccionInput(BaseModel):
    aprobador_id: int
    nota: str = ""

class EmpresaInput(BaseModel):
    nombre: str
    rfc: str = ""
    requiere_aprobacion: bool = True
    limite_sin_aprobacion: float = 5000.0

class MiembroInput(BaseModel):
    usuario_id: int
    empresa_id: int
    rol: str = "residente"
    puede_aprobar: bool = False
    limite_aprobacion: float | None = None


# ─── Verificar si necesita aprobacion ────────────────────────────

@router.get("/verificar/{usuario_id}/{monto}")
def verificar(usuario_id: int, monto: float, db: Session = Depends(get_db)):
    """Verifica si un usuario necesita aprobacion para un monto dado."""
    requiere = necesita_aprobacion(db, usuario_id, monto)
    return {"necesita_aprobacion": requiere, "usuario_id": usuario_id, "monto": monto}


# ─── Solicitar aprobacion ────────────────────────────────────────

@router.post("/solicitar")
async def solicitar(data: SolicitudInput, db: Session = Depends(get_db)):
    """Crea una solicitud de aprobacion y notifica aprobadores via WhatsApp."""
    aprobacion = await solicitar_aprobacion(db, data.orden_id, data.usuario_id, data.nota)
    if not aprobacion:
        raise HTTPException(status_code=400, detail="No se pudo crear la solicitud")
    return {
        "ok": True,
        "aprobacion_id": aprobacion.id,
        "status": aprobacion.status,
        "expira_at": aprobacion.expira_at.isoformat() if aprobacion.expira_at else None,
    }


# ─── Aprobar ─────────────────────────────────────────────────────

@router.post("/{aprobacion_id}/aprobar")
def aprobar(aprobacion_id: int, data: AccionInput, db: Session = Depends(get_db)):
    """Aprueba una solicitud pendiente."""
    aprobacion = aprobar_orden(db, aprobacion_id, data.aprobador_id, data.nota)
    if not aprobacion:
        raise HTTPException(status_code=400, detail="No se pudo aprobar. Verifica permisos y que este pendiente.")
    return {
        "ok": True,
        "aprobacion_id": aprobacion.id,
        "status": aprobacion.status,
        "orden_id": aprobacion.orden_id,
    }


# ─── Rechazar ────────────────────────────────────────────────────

@router.post("/{aprobacion_id}/rechazar")
def rechazar(aprobacion_id: int, data: AccionInput, db: Session = Depends(get_db)):
    """Rechaza una solicitud pendiente."""
    aprobacion = rechazar_orden(db, aprobacion_id, data.aprobador_id, data.nota)
    if not aprobacion:
        raise HTTPException(status_code=400, detail="No se pudo rechazar. Verifica permisos.")
    return {
        "ok": True,
        "aprobacion_id": aprobacion.id,
        "status": aprobacion.status,
        "orden_id": aprobacion.orden_id,
    }


# ─── Pendientes por aprobador ───────────────────────────────────

@router.get("/pendientes/{aprobador_id}")
def pendientes(aprobador_id: int, db: Session = Depends(get_db)):
    """Lista aprobaciones pendientes para un aprobador."""
    lista = obtener_aprobaciones_pendientes(db, aprobador_id)
    return {
        "total": len(lista),
        "aprobaciones": [
            {
                "id": a.id,
                "orden_id": a.orden_id,
                "monto": a.monto,
                "solicitante_id": a.solicitante_id,
                "nota_solicitud": a.nota_solicitud,
                "solicitada_at": a.solicitada_at.isoformat() if a.solicitada_at else None,
                "expira_at": a.expira_at.isoformat() if a.expira_at else None,
            }
            for a in lista
        ],
    }


# ─── Historial de una empresa ───────────────────────────────────

@router.get("/historial/{empresa_id}")
def historial(empresa_id: int, db: Session = Depends(get_db)):
    """Historial de aprobaciones de una empresa."""
    aprobaciones = db.query(Aprobacion).filter(
        Aprobacion.empresa_id == empresa_id
    ).order_by(Aprobacion.solicitada_at.desc()).limit(50).all()

    return {
        "empresa_id": empresa_id,
        "total": len(aprobaciones),
        "aprobaciones": [
            {
                "id": a.id,
                "orden_id": a.orden_id,
                "monto": a.monto,
                "status": a.status,
                "solicitante_id": a.solicitante_id,
                "aprobador_id": a.aprobador_id,
                "nota_solicitud": a.nota_solicitud,
                "nota_respuesta": a.nota_respuesta,
                "solicitada_at": a.solicitada_at.isoformat() if a.solicitada_at else None,
                "respondida_at": a.respondida_at.isoformat() if a.respondida_at else None,
            }
            for a in aprobaciones
        ],
    }


# ─── Limpiar expiradas ──────────────────────────────────────────

@router.post("/limpiar-expiradas")
def limpiar_expiradas(db: Session = Depends(get_db)):
    """Marca como expiradas las aprobaciones que pasaron el limite."""
    expiradas = verificar_expiradas(db)
    return {"ok": True, "expiradas": len(expiradas)}


# ─── CRUD Empresas ──────────────────────────────────────────────

@router.post("/empresas")
def crear_empresa(data: EmpresaInput, db: Session = Depends(get_db)):
    """Crea una nueva empresa con configuracion de aprobacion."""
    empresa = Empresa(
        nombre=data.nombre,
        rfc=data.rfc,
        requiere_aprobacion=data.requiere_aprobacion,
        limite_sin_aprobacion=data.limite_sin_aprobacion,
    )
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return {
        "ok": True,
        "empresa_id": empresa.id,
        "nombre": empresa.nombre,
        "requiere_aprobacion": empresa.requiere_aprobacion,
        "limite_sin_aprobacion": empresa.limite_sin_aprobacion,
    }


@router.get("/empresas")
def listar_empresas(db: Session = Depends(get_db)):
    """Lista todas las empresas registradas."""
    empresas = db.query(Empresa).filter(Empresa.activo == True).all()
    return {
        "total": len(empresas),
        "empresas": [
            {
                "id": e.id,
                "nombre": e.nombre,
                "rfc": e.rfc,
                "requiere_aprobacion": e.requiere_aprobacion,
                "limite_sin_aprobacion": e.limite_sin_aprobacion,
            }
            for e in empresas
        ],
    }


# ─── CRUD Miembros ──────────────────────────────────────────────

@router.post("/miembros")
def agregar_miembro(data: MiembroInput, db: Session = Depends(get_db)):
    """Agrega un usuario como miembro de una empresa."""
    existente = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.usuario_id == data.usuario_id,
        MiembroEmpresa.empresa_id == data.empresa_id,
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="El usuario ya es miembro de esta empresa")

    miembro = MiembroEmpresa(
        usuario_id=data.usuario_id,
        empresa_id=data.empresa_id,
        rol=data.rol,
        puede_aprobar=data.puede_aprobar,
        limite_aprobacion=data.limite_aprobacion,
    )
    db.add(miembro)

    # Actualizar empresa_id y rol en usuario
    usuario = db.query(Usuario).filter(Usuario.id == data.usuario_id).first()
    if usuario:
        usuario.empresa_id = data.empresa_id
        usuario.rol_empresa = data.rol

    db.commit()
    db.refresh(miembro)
    return {
        "ok": True,
        "miembro_id": miembro.id,
        "rol": miembro.rol,
        "puede_aprobar": miembro.puede_aprobar,
    }


@router.get("/miembros/{empresa_id}")
def listar_miembros(empresa_id: int, db: Session = Depends(get_db)):
    """Lista miembros de una empresa."""
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
            "telefono": usuario.telefono if usuario else "?",
            "rol": m.rol,
            "puede_aprobar": m.puede_aprobar,
            "limite_aprobacion": m.limite_aprobacion,
        })

    return {"empresa_id": empresa_id, "total": len(resultado), "miembros": resultado}


# ─── API: Todas las pendientes (admin view) ────────────────────

@router.get("/api/todas-pendientes")
def todas_pendientes(db: Session = Depends(get_db)):
    """Retorna TODAS las aprobaciones pendientes para vista admin."""
    pendientes = db.query(Aprobacion).filter(
        Aprobacion.status == "pendiente"
    ).order_by(Aprobacion.solicitada_at.desc()).all()
    return {
        "total": len(pendientes),
        "aprobaciones": [
            {
                "id": a.id,
                "orden_id": a.orden_id,
                "empresa_id": a.empresa_id,
                "monto": a.monto,
                "solicitante_id": a.solicitante_id,
                "nota_solicitud": a.nota_solicitud,
                "solicitada_at": a.solicitada_at.isoformat() if a.solicitada_at else None,
                "expira_at": a.expira_at.isoformat() if a.expira_at else None,
            }
            for a in pendientes
        ],
    }


# ─── API: Historial global ─────────────────────────────────────

@router.get("/api/historial-global")
def historial_global(db: Session = Depends(get_db)):
    """Retorna las ultimas 50 aprobaciones de todas las empresas."""
    aprobaciones = db.query(Aprobacion).order_by(
        Aprobacion.solicitada_at.desc()
    ).limit(50).all()
    return {
        "total": len(aprobaciones),
        "aprobaciones": [
            {
                "id": a.id,
                "orden_id": a.orden_id,
                "empresa_id": a.empresa_id,
                "monto": a.monto,
                "status": a.status,
                "solicitante_id": a.solicitante_id,
                "aprobador_id": a.aprobador_id,
                "nota_solicitud": a.nota_solicitud,
                "nota_respuesta": a.nota_respuesta,
                "solicitada_at": a.solicitada_at.isoformat() if a.solicitada_at else None,
                "respondida_at": a.respondida_at.isoformat() if a.respondida_at else None,
            }
            for a in aprobaciones
        ],
    }


# ─── Dashboard HTML ────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aprobaciones Corporativas | ObraYa</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0e1a;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;min-height:100vh}
a{color:#ff6b2b;text-decoration:none}
a:hover{text-decoration:underline}

.header{background:linear-gradient(135deg,#1a2332 0%,#0f1724 100%);border-bottom:1px solid #2a3548;padding:20px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.header h1{font-size:1.5rem;font-weight:700;color:#f1f5f9}
.header h1 span{color:#ff6b2b}
.back-link{display:inline-flex;align-items:center;gap:6px;color:#94a3b8;font-size:.875rem;padding:6px 14px;border-radius:8px;border:1px solid #2a3548;transition:all .2s}
.back-link:hover{color:#ff6b2b;border-color:#ff6b2b;text-decoration:none}

.tabs{display:flex;gap:4px;padding:16px 24px 0;border-bottom:1px solid #2a3548;overflow-x:auto}
.tab{padding:10px 20px;font-size:.875rem;font-weight:500;color:#94a3b8;cursor:pointer;border:none;background:none;border-bottom:2px solid transparent;transition:all .2s;white-space:nowrap}
.tab:hover{color:#f1f5f9}
.tab.active{color:#ff6b2b;border-bottom-color:#ff6b2b}

.content{padding:24px;max-width:1200px;margin:0 auto}
.tab-panel{display:none}
.tab-panel.active{display:block}

.card{background:#1a2332;border:1px solid #2a3548;border-radius:12px;padding:20px;margin-bottom:16px;transition:border-color .2s}
.card:hover{border-color:#3a4a60}

.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:#1a2332;border:1px solid #2a3548;border-radius:12px;padding:20px;text-align:center}
.stat-card .number{font-size:2rem;font-weight:700;color:#ff6b2b}
.stat-card .label{font-size:.8rem;color:#94a3b8;margin-top:4px}

.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:600}
.badge-pendiente{background:rgba(234,179,8,.15);color:#eab308}
.badge-aprobada{background:rgba(34,197,94,.15);color:#22c55e}
.badge-rechazada{background:rgba(239,68,68,.15);color:#ef4444}
.badge-expirada{background:rgba(100,116,139,.15);color:#64748b}

.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;border:none;transition:all .2s}
.btn-green{background:#22c55e;color:#fff}
.btn-green:hover{background:#16a34a}
.btn-red{background:#ef4444;color:#fff}
.btn-red:hover{background:#dc2626}
.btn-orange{background:#ff6b2b;color:#fff}
.btn-orange:hover{background:#e55a1b}
.btn-outline{background:transparent;border:1px solid #2a3548;color:#94a3b8}
.btn-outline:hover{border-color:#ff6b2b;color:#ff6b2b}
.btn:disabled{opacity:.5;cursor:not-allowed}

.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:16px}
.form-group label{display:block;font-size:.8rem;color:#94a3b8;margin-bottom:4px}
.form-group input,.form-group select{width:100%;padding:8px 12px;border-radius:8px;border:1px solid #2a3548;background:#0f1724;color:#f1f5f9;font-size:.875rem}
.form-group input:focus,.form-group select:focus{outline:none;border-color:#ff6b2b}

.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th{text-align:left;padding:10px 12px;color:#64748b;font-weight:600;border-bottom:1px solid #2a3548;white-space:nowrap}
td{padding:10px 12px;border-bottom:1px solid #1e293b;color:#94a3b8}
tr:hover td{background:rgba(255,107,43,.03)}

.empty{text-align:center;padding:40px;color:#64748b}
.loading{text-align:center;padding:40px;color:#94a3b8}

.approval-card{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.approval-info{flex:1;min-width:200px}
.approval-info h3{font-size:1rem;color:#f1f5f9;margin-bottom:4px}
.approval-info p{font-size:.8rem;color:#94a3b8;margin:2px 0}
.approval-actions{display:flex;gap:8px;align-items:center;flex-shrink:0}

.nota-input{width:200px;padding:6px 10px;border-radius:6px;border:1px solid #2a3548;background:#0f1724;color:#f1f5f9;font-size:.8rem}
.nota-input:focus{outline:none;border-color:#ff6b2b}

.section-title{font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:16px}

@media(max-width:640px){
  .header{padding:16px}
  .header h1{font-size:1.2rem}
  .content{padding:16px}
  .form-grid{grid-template-columns:1fr}
  .approval-card{flex-direction:column}
  .approval-actions{width:100%;justify-content:flex-end}
  .nota-input{width:100%}
  .tabs{padding:12px 16px 0}
  .tab{padding:8px 14px;font-size:.8rem}
}
</style>
</head>
<body>

<div class="header">
  <h1><span>&#9632;</span> Aprobaciones Corporativas</h1>
  <a href="/hub/" class="back-link">&larr; Volver al Hub</a>
</div>

<div class="tabs">
  <button class="tab active" data-tab="pendientes">Pendientes</button>
  <button class="tab" data-tab="empresas">Empresas</button>
  <button class="tab" data-tab="miembros">Miembros</button>
  <button class="tab" data-tab="historial">Historial</button>
</div>

<div class="content">

  <!-- TAB: Pendientes -->
  <div class="tab-panel active" id="panel-pendientes">
    <div class="stats-row" id="pendientes-stats"></div>
    <div class="section-title">Solicitudes Pendientes</div>
    <div id="pendientes-list"><div class="loading">Cargando...</div></div>
  </div>

  <!-- TAB: Empresas -->
  <div class="tab-panel" id="panel-empresas">
    <div class="card" style="margin-bottom:24px">
      <div class="section-title">Nueva Empresa</div>
      <div class="form-grid">
        <div class="form-group"><label>Nombre</label><input id="emp-nombre" placeholder="Nombre de la empresa"></div>
        <div class="form-group"><label>RFC</label><input id="emp-rfc" placeholder="RFC (opcional)"></div>
        <div class="form-group"><label>Limite sin aprobacion ($)</label><input id="emp-limite" type="number" value="5000"></div>
        <div class="form-group"><label>Requiere aprobacion</label>
          <select id="emp-requiere"><option value="true">Si</option><option value="false">No</option></select>
        </div>
      </div>
      <button class="btn btn-orange" onclick="crearEmpresa()">Crear Empresa</button>
    </div>
    <div class="section-title">Empresas Registradas</div>
    <div id="empresas-list"><div class="loading">Cargando...</div></div>
  </div>

  <!-- TAB: Miembros -->
  <div class="tab-panel" id="panel-miembros">
    <div class="card" style="margin-bottom:24px">
      <div class="section-title">Agregar Miembro</div>
      <div class="form-grid">
        <div class="form-group"><label>Empresa</label><select id="mie-empresa"><option value="">Seleccionar...</option></select></div>
        <div class="form-group"><label>ID Usuario</label><input id="mie-usuario" type="number" placeholder="ID del usuario"></div>
        <div class="form-group"><label>Rol</label>
          <select id="mie-rol"><option value="residente">Residente</option><option value="gerente">Gerente</option><option value="director">Director</option><option value="admin">Admin</option></select>
        </div>
        <div class="form-group"><label>Puede aprobar</label>
          <select id="mie-aprueba"><option value="false">No</option><option value="true">Si</option></select>
        </div>
        <div class="form-group"><label>Limite aprobacion ($)</label><input id="mie-limite" type="number" placeholder="Sin limite"></div>
      </div>
      <button class="btn btn-orange" onclick="agregarMiembro()">Agregar Miembro</button>
    </div>
    <div class="section-title">Miembros por Empresa</div>
    <div class="form-group" style="max-width:300px;margin-bottom:16px">
      <select id="mie-ver-empresa" onchange="cargarMiembros()"><option value="">Seleccionar empresa...</option></select>
    </div>
    <div id="miembros-list"><div class="empty">Selecciona una empresa para ver sus miembros</div></div>
  </div>

  <!-- TAB: Historial -->
  <div class="tab-panel" id="panel-historial">
    <div class="section-title">Ultimas 50 Aprobaciones</div>
    <div id="historial-list"><div class="loading">Cargando...</div></div>
  </div>

</div>

<script>
const API = '/aprobaciones';

// ─── Tab switching ────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById('panel-' + t.dataset.tab).classList.add('active');
    if (t.dataset.tab === 'pendientes') cargarPendientes();
    if (t.dataset.tab === 'empresas') cargarEmpresas();
    if (t.dataset.tab === 'miembros') cargarEmpresasSelect();
    if (t.dataset.tab === 'historial') cargarHistorial();
  });
});

// ─── Helpers ──────────────────────────────────────────────────
function fmt(n){ return n != null ? '$' + Number(n).toLocaleString('es-MX', {minimumFractionDigits:2}) : '$0.00'; }
function fmtDate(iso){ if(!iso) return '-'; const d=new Date(iso); return d.toLocaleDateString('es-MX',{day:'2-digit',month:'short',year:'numeric'}) + ' ' + d.toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit'}); }
function timeAgo(iso){
  if(!iso) return '';
  const diff = new Date(iso) - new Date();
  if(diff < 0) return 'Expirado';
  const hrs = Math.floor(diff/3600000);
  const mins = Math.floor((diff%3600000)/60000);
  return hrs + 'h ' + mins + 'm';
}
function badgeFor(status){
  const map = {pendiente:'badge-pendiente',aprobada:'badge-aprobada',rechazada:'badge-rechazada',expirada:'badge-expirada'};
  return '<span class="badge '+(map[status]||'badge-pendiente')+'">'+status+'</span>';
}

async function apiFetch(url, opts){
  try {
    const r = await fetch(url, opts);
    if(!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail || r.statusText); }
    return r.json();
  } catch(e) { alert('Error: ' + e.message); throw e; }
}

// ─── Pendientes ───────────────────────────────────────────────
async function cargarPendientes(){
  const el = document.getElementById('pendientes-list');
  const st = document.getElementById('pendientes-stats');
  el.innerHTML = '<div class="loading">Cargando...</div>';
  try {
    const data = await apiFetch(API + '/api/todas-pendientes');
    st.innerHTML = '<div class="stat-card"><div class="number">'+data.total+'</div><div class="label">Pendientes</div></div>';
    if(!data.aprobaciones.length){ el.innerHTML='<div class="empty">No hay aprobaciones pendientes</div>'; return; }
    el.innerHTML = data.aprobaciones.map(a => `
      <div class="card">
        <div class="approval-card">
          <div class="approval-info">
            <h3>Orden #${a.orden_id} &mdash; ${fmt(a.monto)}</h3>
            <p>Solicitante ID: ${a.solicitante_id} &bull; Empresa ID: ${a.empresa_id}</p>
            <p>Solicitada: ${fmtDate(a.solicitada_at)}</p>
            ${a.expira_at ? '<p>Expira en: <strong>'+timeAgo(a.expira_at)+'</strong></p>' : ''}
            ${a.nota_solicitud ? '<p style="color:#64748b;margin-top:4px">Nota: '+a.nota_solicitud+'</p>' : ''}
          </div>
          <div class="approval-actions">
            <input class="nota-input" id="nota-${a.id}" placeholder="Nota (opcional)">
            <button class="btn btn-green" onclick="accionAprobar(${a.id})">Aprobar</button>
            <button class="btn btn-red" onclick="accionRechazar(${a.id})">Rechazar</button>
          </div>
        </div>
      </div>
    `).join('');
  } catch(e){ el.innerHTML='<div class="empty">Error al cargar</div>'; }
}

async function accionAprobar(id){
  const nota = document.getElementById('nota-'+id)?.value || '';
  const aprobadorId = prompt('Tu ID de aprobador:');
  if(!aprobadorId) return;
  await apiFetch(API+'/'+id+'/aprobar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({aprobador_id:parseInt(aprobadorId),nota})});
  cargarPendientes();
}
async function accionRechazar(id){
  const nota = document.getElementById('nota-'+id)?.value || '';
  const aprobadorId = prompt('Tu ID de aprobador:');
  if(!aprobadorId) return;
  await apiFetch(API+'/'+id+'/rechazar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({aprobador_id:parseInt(aprobadorId),nota})});
  cargarPendientes();
}

// ─── Empresas ─────────────────────────────────────────────────
async function cargarEmpresas(){
  const el = document.getElementById('empresas-list');
  el.innerHTML = '<div class="loading">Cargando...</div>';
  try {
    const data = await apiFetch(API + '/empresas');
    if(!data.empresas.length){ el.innerHTML='<div class="empty">No hay empresas registradas</div>'; return; }
    el.innerHTML = '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Nombre</th><th>RFC</th><th>Requiere Aprob.</th><th>Limite</th></tr></thead><tbody>'
      + data.empresas.map(e => `<tr><td>${e.id}</td><td style="color:#f1f5f9;font-weight:500">${e.nombre}</td><td>${e.rfc||'-'}</td><td>${e.requiere_aprobacion ? '<span class="badge badge-pendiente">Si</span>' : '<span class="badge badge-expirada">No</span>'}</td><td>${fmt(e.limite_sin_aprobacion)}</td></tr>`).join('')
      + '</tbody></table></div>';
  } catch(e){ el.innerHTML='<div class="empty">Error al cargar</div>'; }
}

async function crearEmpresa(){
  const nombre = document.getElementById('emp-nombre').value.trim();
  if(!nombre){ alert('Nombre es requerido'); return; }
  await apiFetch(API+'/empresas',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    nombre,
    rfc: document.getElementById('emp-rfc').value.trim(),
    requiere_aprobacion: document.getElementById('emp-requiere').value === 'true',
    limite_sin_aprobacion: parseFloat(document.getElementById('emp-limite').value) || 5000
  })});
  document.getElementById('emp-nombre').value='';
  document.getElementById('emp-rfc').value='';
  cargarEmpresas();
}

// ─── Miembros ─────────────────────────────────────────────────
async function cargarEmpresasSelect(){
  try {
    const data = await apiFetch(API + '/empresas');
    const opts = '<option value="">Seleccionar...</option>' + data.empresas.map(e => `<option value="${e.id}">${e.nombre}</option>`).join('');
    document.getElementById('mie-empresa').innerHTML = opts;
    document.getElementById('mie-ver-empresa').innerHTML = '<option value="">Seleccionar empresa...</option>' + data.empresas.map(e => `<option value="${e.id}">${e.nombre}</option>`).join('');
  } catch(e){}
}

async function cargarMiembros(){
  const empresaId = document.getElementById('mie-ver-empresa').value;
  const el = document.getElementById('miembros-list');
  if(!empresaId){ el.innerHTML='<div class="empty">Selecciona una empresa para ver sus miembros</div>'; return; }
  el.innerHTML = '<div class="loading">Cargando...</div>';
  try {
    const data = await apiFetch(API + '/miembros/' + empresaId);
    if(!data.miembros.length){ el.innerHTML='<div class="empty">No hay miembros en esta empresa</div>'; return; }
    el.innerHTML = '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Usuario</th><th>Telefono</th><th>Rol</th><th>Puede Aprobar</th><th>Limite</th></tr></thead><tbody>'
      + data.miembros.map(m => `<tr><td>${m.id}</td><td style="color:#f1f5f9;font-weight:500">${m.nombre}</td><td>${m.telefono}</td><td>${m.rol}</td><td>${m.puede_aprobar ? '<span class="badge badge-aprobada">Si</span>' : '<span class="badge badge-expirada">No</span>'}</td><td>${m.limite_aprobacion != null ? fmt(m.limite_aprobacion) : 'Sin limite'}</td></tr>`).join('')
      + '</tbody></table></div>';
  } catch(e){ el.innerHTML='<div class="empty">Error al cargar</div>'; }
}

async function agregarMiembro(){
  const empresaId = document.getElementById('mie-empresa').value;
  const usuarioId = document.getElementById('mie-usuario').value;
  if(!empresaId || !usuarioId){ alert('Empresa y usuario son requeridos'); return; }
  const limite = document.getElementById('mie-limite').value;
  await apiFetch(API+'/miembros',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    usuario_id: parseInt(usuarioId),
    empresa_id: parseInt(empresaId),
    rol: document.getElementById('mie-rol').value,
    puede_aprobar: document.getElementById('mie-aprueba').value === 'true',
    limite_aprobacion: limite ? parseFloat(limite) : null
  })});
  document.getElementById('mie-usuario').value='';
  document.getElementById('mie-limite').value='';
  const selEmpresa = document.getElementById('mie-ver-empresa');
  selEmpresa.value = empresaId;
  cargarMiembros();
}

// ─── Historial ────────────────────────────────────────────────
async function cargarHistorial(){
  const el = document.getElementById('historial-list');
  el.innerHTML = '<div class="loading">Cargando...</div>';
  try {
    const data = await apiFetch(API + '/api/historial-global');
    if(!data.aprobaciones.length){ el.innerHTML='<div class="empty">No hay historial de aprobaciones</div>'; return; }
    el.innerHTML = '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Orden</th><th>Monto</th><th>Status</th><th>Solicitante</th><th>Aprobador</th><th>Fecha</th></tr></thead><tbody>'
      + data.aprobaciones.map(a => `<tr><td>${a.id}</td><td>#${a.orden_id}</td><td>${fmt(a.monto)}</td><td>${badgeFor(a.status)}</td><td>ID ${a.solicitante_id}</td><td>${a.aprobador_id ? 'ID '+a.aprobador_id : '-'}</td><td>${fmtDate(a.solicitada_at)}</td></tr>`).join('')
      + '</tbody></table></div>';
  } catch(e){ el.innerHTML='<div class="empty">Error al cargar</div>'; }
}

// ─── Init ─────────────────────────────────────────────────────
cargarPendientes();
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
def dashboard_aprobaciones():
    """Dashboard HTML para gestion de aprobaciones corporativas."""
    return DASHBOARD_HTML
