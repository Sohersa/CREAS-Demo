"""
Router de credito — perfil crediticio, elegibilidad, y ranking.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.services.credit_scoring import (
    calcular_score,
    obtener_perfil_crediticio,
    evaluar_elegibilidad_credito,
    ranking_usuarios_por_score,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credito", tags=["credito"])


# ─── Perfil crediticio ────────────────────────────────────────────

@router.get("/perfil/{usuario_id}")
def perfil_crediticio(usuario_id: int, db: Session = Depends(get_db)):
    """Retorna el perfil crediticio completo de un usuario."""
    perfil = obtener_perfil_crediticio(db, usuario_id)
    if "error" in perfil:
        raise HTTPException(status_code=404, detail=perfil["error"])
    return perfil


# ─── Evaluar elegibilidad ─────────────────────────────────────────

@router.get("/evaluar/{usuario_id}/{monto}")
def evaluar_credito(usuario_id: int, monto: float, db: Session = Depends(get_db)):
    """Evalua si un usuario puede obtener credito por el monto solicitado."""
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0")

    resultado = evaluar_elegibilidad_credito(db, usuario_id, monto)
    if resultado.get("score") == 0 and not resultado.get("elegible"):
        raise HTTPException(status_code=404, detail=resultado["motivo"])
    return resultado


# ─── Forzar recalculo de score ────────────────────────────────────

@router.post("/recalcular/{usuario_id}")
def recalcular_score(usuario_id: int, db: Session = Depends(get_db)):
    """Fuerza el recalculo del score crediticio de un usuario."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    score_anterior = usuario.score_credito or 50.0
    nuevo_score = calcular_score(db, usuario_id)
    usuario.score_credito = nuevo_score
    db.commit()

    return {
        "usuario_id": usuario_id,
        "score_anterior": score_anterior,
        "score_nuevo": nuevo_score,
        "cambio": round(nuevo_score - score_anterior, 2),
    }


# ─── Ranking de usuarios ──────────────────────────────────────────

@router.get("/ranking")
def ranking(limit: int = 20, db: Session = Depends(get_db)):
    """Top usuarios por score crediticio."""
    if limit < 1 or limit > 100:
        limit = 20
    return ranking_usuarios_por_score(db, limit)


# ─── Estadisticas generales de credito ────────────────────────────

@router.get("/stats")
def stats_credito(db: Session = Depends(get_db)):
    """Estadisticas generales del sistema de credit scoring."""

    # Usuarios con al menos 1 pedido
    usuarios_activos = (
        db.query(Usuario)
        .filter(Usuario.total_pedidos_completados > 0)
    )

    total_usuarios = usuarios_activos.count()

    if total_usuarios == 0:
        return {
            "total_usuarios_con_historial": 0,
            "score_promedio": 0,
            "score_mediana": 0,
            "distribucion": {
                "excelente": 0,
                "bueno": 0,
                "regular": 0,
                "malo": 0,
            },
            "elegibles_credito": 0,
            "volumen_total_gastado": 0,
        }

    # Score promedio
    score_promedio = db.query(
        func.avg(Usuario.score_credito)
    ).filter(
        Usuario.total_pedidos_completados > 0
    ).scalar() or 0

    # Distribucion por nivel
    excelente = usuarios_activos.filter(Usuario.score_credito >= 85).count()
    bueno = usuarios_activos.filter(
        Usuario.score_credito >= 70, Usuario.score_credito < 85
    ).count()
    regular = usuarios_activos.filter(
        Usuario.score_credito >= 50, Usuario.score_credito < 70
    ).count()
    malo = usuarios_activos.filter(Usuario.score_credito < 50).count()

    # Elegibles para credito (score >= 65 y >= 5 pedidos)
    elegibles = usuarios_activos.filter(
        Usuario.score_credito >= 65,
        Usuario.total_pedidos_completados >= 5,
    ).count()

    # Volumen total
    volumen_total = db.query(
        func.sum(Usuario.total_gastado)
    ).filter(
        Usuario.total_pedidos_completados > 0
    ).scalar() or 0

    # Promedio dias de pago global
    promedio_dias = db.query(
        func.avg(Usuario.promedio_dias_pago)
    ).filter(
        Usuario.total_pedidos_completados > 0,
        Usuario.promedio_dias_pago.isnot(None),
    ).scalar()

    return {
        "total_usuarios_con_historial": total_usuarios,
        "score_promedio": round(score_promedio, 2),
        "distribucion": {
            "excelente": excelente,
            "bueno": bueno,
            "regular": regular,
            "malo": malo,
        },
        "elegibles_credito": elegibles,
        "volumen_total_gastado": round(volumen_total, 2),
        "promedio_dias_pago_global": round(promedio_dias, 2) if promedio_dias else None,
    }


# ─── Dashboard HTML ──────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Credit Scoring - ObraYa</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e1a;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;min-height:100vh}
a{color:#ff6b2b;text-decoration:none}
a:hover{text-decoration:underline}

.header{display:flex;align-items:center;justify-content:space-between;padding:20px 32px;border-bottom:1px solid #2a3548}
.header h1{font-size:1.6rem;font-weight:700}
.header .back{font-size:.9rem;padding:8px 16px;border:1px solid #2a3548;border-radius:8px;transition:all .2s}
.header .back:hover{background:#1a2332;text-decoration:none}

.container{max-width:1280px;margin:0 auto;padding:24px 32px}

/* KPI cards */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:32px}
.kpi-card{background:#1a2332;border:1px solid #2a3548;border-radius:12px;padding:20px;transition:transform .2s,border-color .2s}
.kpi-card:hover{transform:translateY(-2px);border-color:#ff6b2b}
.kpi-card .label{font-size:.8rem;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.kpi-card .value{font-size:1.8rem;font-weight:700}
.kpi-card .value.orange{color:#ff6b2b}
.kpi-card .value.green{color:#22c55e}
.kpi-card .value.blue{color:#3b82f6}

/* Distribution mini-bars */
.dist-bars{display:flex;gap:8px;margin-top:12px}
.dist-bar{flex:1;text-align:center}
.dist-bar .bar-track{height:6px;background:#0a0e1a;border-radius:3px;overflow:hidden;margin-bottom:4px}
.dist-bar .bar-fill{height:100%;border-radius:3px;transition:width .6s ease}
.dist-bar .bar-label{font-size:.65rem;color:#64748b}
.dist-bar .bar-count{font-size:.8rem;font-weight:600}

/* Table */
.section-title{font-size:1.2rem;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.table-wrap{background:#1a2332;border:1px solid #2a3548;border-radius:12px;overflow:hidden;margin-bottom:32px}
table{width:100%;border-collapse:collapse}
th{background:#0f1729;text-align:left;padding:12px 16px;font-size:.75rem;color:#64748b;text-transform:uppercase;letter-spacing:.5px}
td{padding:12px 16px;border-top:1px solid #2a3548;font-size:.9rem}
tr:hover td{background:#1e293b}

.score-bar-cell{display:flex;align-items:center;gap:10px}
.score-bar-track{width:80px;height:8px;background:#0a0e1a;border-radius:4px;overflow:hidden}
.score-bar-fill{height:100%;border-radius:4px;transition:width .5s ease}
.score-num{font-weight:600;min-width:30px}

.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:600}
.badge-green{background:rgba(34,197,94,.15);color:#22c55e}
.badge-blue{background:rgba(59,130,246,.15);color:#3b82f6}
.badge-yellow{background:rgba(234,179,8,.15);color:#eab308}
.badge-red{background:rgba(239,68,68,.15);color:#ef4444}

/* Lookup section */
.lookup{background:#1a2332;border:1px solid #2a3548;border-radius:12px;padding:24px;margin-bottom:32px}
.lookup-row{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin-bottom:20px}
.field{display:flex;flex-direction:column;gap:4px}
.field label{font-size:.8rem;color:#94a3b8}
.field input{background:#0a0e1a;border:1px solid #2a3548;border-radius:8px;padding:10px 14px;color:#f1f5f9;font-size:.9rem;outline:none;transition:border-color .2s;width:180px}
.field input:focus{border-color:#ff6b2b}
.btn{padding:10px 20px;border:none;border-radius:8px;font-size:.85rem;font-weight:600;cursor:pointer;transition:all .2s}
.btn-primary{background:#ff6b2b;color:#fff}
.btn-primary:hover{background:#e55a1b}
.btn-secondary{background:#1e293b;color:#f1f5f9;border:1px solid #2a3548}
.btn-secondary:hover{background:#2a3548}
.btn:disabled{opacity:.5;cursor:not-allowed}

/* Profile card */
.profile-card{display:none;background:#0f1729;border:1px solid #2a3548;border-radius:12px;padding:24px;margin-top:16px}
.profile-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
.profile-item .pi-label{font-size:.75rem;color:#64748b;margin-bottom:4px}
.profile-item .pi-value{font-size:1.1rem;font-weight:600}

/* Eval result */
.eval-result{display:none;background:#0f1729;border:1px solid #2a3548;border-radius:12px;padding:24px;margin-top:16px}
.eval-result.approved{border-color:#22c55e}
.eval-result.denied{border-color:#ef4444}

/* Toast */
.toast{position:fixed;bottom:24px;right:24px;background:#1a2332;border:1px solid #2a3548;border-radius:10px;padding:14px 20px;font-size:.85rem;opacity:0;transform:translateY(10px);transition:all .3s;z-index:999;max-width:360px}
.toast.show{opacity:1;transform:translateY(0)}
.toast.error{border-color:#ef4444;color:#ef4444}
.toast.success{border-color:#22c55e;color:#22c55e}

/* Loading */
.spinner{display:inline-block;width:16px;height:16px;border:2px solid #2a3548;border-top-color:#ff6b2b;border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

.loading-placeholder{text-align:center;padding:40px;color:#64748b}

/* Responsive */
@media(max-width:768px){
  .header{padding:16px 20px}
  .container{padding:16px 20px}
  .kpi-grid{grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
  .lookup-row{flex-direction:column;align-items:stretch}
  .field input{width:100%}
  .table-wrap{overflow-x:auto}
  table{min-width:700px}
}
</style>
</head>
<body>

<div class="header">
  <h1>Credit Scoring</h1>
  <a href="/hub/" class="back">&#8592; Hub</a>
</div>

<div class="container">

  <!-- KPI Cards -->
  <div class="kpi-grid" id="kpiGrid">
    <div class="kpi-card"><div class="loading-placeholder"><div class="spinner"></div></div></div>
    <div class="kpi-card"><div class="loading-placeholder"><div class="spinner"></div></div></div>
    <div class="kpi-card"><div class="loading-placeholder"><div class="spinner"></div></div></div>
    <div class="kpi-card"><div class="loading-placeholder"><div class="spinner"></div></div></div>
    <div class="kpi-card"><div class="loading-placeholder"><div class="spinner"></div></div></div>
  </div>

  <!-- Ranking Table -->
  <div class="section-title">Ranking de Usuarios</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th><th>Nombre</th><th>Telefono</th><th>Score</th><th>Pedidos</th><th>Total Gastado</th><th>Clasificacion</th>
        </tr>
      </thead>
      <tbody id="rankingBody">
        <tr><td colspan="7" class="loading-placeholder"><div class="spinner"></div></td></tr>
      </tbody>
    </table>
  </div>

  <!-- Individual Lookup -->
  <div class="section-title">Consulta Individual</div>
  <div class="lookup">
    <div class="lookup-row">
      <div class="field">
        <label>ID de Usuario</label>
        <input type="number" id="lookupId" placeholder="Ej: 42" min="1">
      </div>
      <button class="btn btn-primary" onclick="fetchProfile()">Consultar Perfil</button>
      <button class="btn btn-secondary" onclick="recalcScore()">Recalcular Score</button>
    </div>
    <div class="lookup-row">
      <div class="field">
        <label>Monto a Evaluar ($)</label>
        <input type="number" id="evalMonto" placeholder="Ej: 5000" min="1" step="100">
      </div>
      <button class="btn btn-primary" onclick="evalCredit()">Evaluar Credito</button>
    </div>

    <div class="profile-card" id="profileCard"></div>
    <div class="eval-result" id="evalResult"></div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
const API = '/credito';

function toast(msg, type=''){
  const t=document.getElementById('toast');
  t.textContent=msg;
  t.className='toast show '+(type||'');
  clearTimeout(t._tid);
  t._tid=setTimeout(()=>t.className='toast',3500);
}

function fmt(n){return new Intl.NumberFormat('es-MX').format(n)}
function fmtMoney(n){return '$'+new Intl.NumberFormat('es-MX',{minimumFractionDigits:2}).format(n)}

async function loadStats(){
  try{
    const r=await fetch(API+'/stats');
    if(!r.ok) throw new Error('Error '+r.status);
    const d=await r.json();
    const dist=d.distribucion||{};
    const total=Math.max((dist.excelente||0)+(dist.bueno||0)+(dist.regular||0)+(dist.malo||0),1);
    document.getElementById('kpiGrid').innerHTML=`
      <div class="kpi-card">
        <div class="label">Usuarios con Historial</div>
        <div class="value orange">${fmt(d.total_usuarios_con_historial)}</div>
      </div>
      <div class="kpi-card">
        <div class="label">Score Promedio</div>
        <div class="value blue">${d.score_promedio}</div>
      </div>
      <div class="kpi-card">
        <div class="label">Distribucion</div>
        <div class="dist-bars">
          <div class="dist-bar">
            <div class="bar-count" style="color:#22c55e">${dist.excelente||0}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${(dist.excelente||0)/total*100}%;background:#22c55e"></div></div>
            <div class="bar-label">Excelente</div>
          </div>
          <div class="dist-bar">
            <div class="bar-count" style="color:#3b82f6">${dist.bueno||0}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${(dist.bueno||0)/total*100}%;background:#3b82f6"></div></div>
            <div class="bar-label">Bueno</div>
          </div>
          <div class="dist-bar">
            <div class="bar-count" style="color:#eab308">${dist.regular||0}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${(dist.regular||0)/total*100}%;background:#eab308"></div></div>
            <div class="bar-label">Regular</div>
          </div>
          <div class="dist-bar">
            <div class="bar-count" style="color:#ef4444">${dist.malo||0}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${(dist.malo||0)/total*100}%;background:#ef4444"></div></div>
            <div class="bar-label">Malo</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="label">Elegibles para Credito</div>
        <div class="value green">${fmt(d.elegibles_credito)}</div>
      </div>
      <div class="kpi-card">
        <div class="label">Volumen Total Gastado</div>
        <div class="value">${fmtMoney(d.volumen_total_gastado)}</div>
      </div>`;
  }catch(e){toast('Error cargando stats: '+e.message,'error')}
}

function scoreColor(s){
  if(s>=85) return '#22c55e';
  if(s>=70) return '#3b82f6';
  if(s>=50) return '#eab308';
  return '#ef4444';
}
function scoreBadge(s){
  if(s>=85) return '<span class="badge badge-green">Excelente</span>';
  if(s>=70) return '<span class="badge badge-blue">Bueno</span>';
  if(s>=50) return '<span class="badge badge-yellow">Regular</span>';
  return '<span class="badge badge-red">Riesgo</span>';
}

async function loadRanking(){
  try{
    const r=await fetch(API+'/ranking?limit=30');
    if(!r.ok) throw new Error('Error '+r.status);
    const data=await r.json();
    const rows=data.map||data;
    const list=Array.isArray(rows)?rows:(rows.ranking||[]);
    if(!list.length){
      document.getElementById('rankingBody').innerHTML='<tr><td colspan="7" style="text-align:center;color:#64748b;padding:32px">Sin datos de ranking</td></tr>';
      return;
    }
    document.getElementById('rankingBody').innerHTML=list.map((u,i)=>{
      const sc=u.score||u.score_credito||0;
      return `<tr>
        <td>${i+1}</td>
        <td>${u.nombre||u.name||'-'}</td>
        <td>${u.telefono||u.phone||'-'}</td>
        <td><div class="score-bar-cell">
          <span class="score-num" style="color:${scoreColor(sc)}">${sc}</span>
          <div class="score-bar-track"><div class="score-bar-fill" style="width:${sc}%;background:${scoreColor(sc)}"></div></div>
        </div></td>
        <td>${u.total_pedidos||u.pedidos||0}</td>
        <td>${fmtMoney(u.total_gastado||0)}</td>
        <td>${scoreBadge(sc)}</td>
      </tr>`}).join('');
  }catch(e){
    document.getElementById('rankingBody').innerHTML='<tr><td colspan="7" style="text-align:center;color:#ef4444;padding:32px">Error: '+e.message+'</td></tr>';
  }
}

async function fetchProfile(){
  const id=document.getElementById('lookupId').value;
  if(!id){toast('Ingresa un ID de usuario','error');return}
  const card=document.getElementById('profileCard');
  card.style.display='block';
  card.innerHTML='<div class="loading-placeholder"><div class="spinner"></div> Cargando perfil...</div>';
  try{
    const r=await fetch(API+'/perfil/'+id);
    if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error '+r.status)}
    const p=r.ok?await r.json():null;
    const sc=p.score||p.score_credito||0;
    card.innerHTML=`
      <h3 style="margin-bottom:16px;display:flex;align-items:center;gap:12px">
        Perfil: ${p.nombre||p.name||'Usuario '+id}
        ${scoreBadge(sc)}
      </h3>
      <div class="profile-grid">
        <div class="profile-item"><div class="pi-label">Score Crediticio</div><div class="pi-value" style="color:${scoreColor(sc)}">${sc}</div></div>
        <div class="profile-item"><div class="pi-label">Total Pedidos</div><div class="pi-value">${p.total_pedidos||p.total_pedidos_completados||0}</div></div>
        <div class="profile-item"><div class="pi-label">Total Gastado</div><div class="pi-value">${fmtMoney(p.total_gastado||0)}</div></div>
        <div class="profile-item"><div class="pi-label">Promedio Dias Pago</div><div class="pi-value">${p.promedio_dias_pago!=null?p.promedio_dias_pago+' dias':'N/A'}</div></div>
        <div class="profile-item"><div class="pi-label">Pedidos a Tiempo</div><div class="pi-value">${p.pedidos_a_tiempo!=null?p.pedidos_a_tiempo:'N/A'}</div></div>
        <div class="profile-item"><div class="pi-label">Pedidos Tardios</div><div class="pi-value">${p.pedidos_tardios!=null?p.pedidos_tardios:'N/A'}</div></div>
        <div class="profile-item"><div class="pi-label">Telefono</div><div class="pi-value">${p.telefono||p.phone||'-'}</div></div>
        <div class="profile-item"><div class="pi-label">Elegible</div><div class="pi-value">${p.elegible?'<span style="color:#22c55e">Si</span>':'<span style="color:#ef4444">No</span>'}</div></div>
      </div>`;
  }catch(e){
    card.innerHTML='<div style="color:#ef4444">'+e.message+'</div>';
  }
}

async function recalcScore(){
  const id=document.getElementById('lookupId').value;
  if(!id){toast('Ingresa un ID de usuario','error');return}
  try{
    const r=await fetch(API+'/recalcular/'+id,{method:'POST'});
    if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error '+r.status)}
    const d=await r.json();
    const sign=d.cambio>=0?'+':'';
    toast('Score recalculado: '+d.score_anterior+' -> '+d.score_nuevo+' ('+sign+d.cambio+')','success');
    loadRanking();
    fetchProfile();
  }catch(e){toast('Error: '+e.message,'error')}
}

async function evalCredit(){
  const id=document.getElementById('lookupId').value;
  const monto=document.getElementById('evalMonto').value;
  if(!id){toast('Ingresa un ID de usuario','error');return}
  if(!monto||monto<=0){toast('Ingresa un monto valido','error');return}
  const box=document.getElementById('evalResult');
  box.style.display='block';
  box.className='eval-result';
  box.innerHTML='<div class="loading-placeholder"><div class="spinner"></div> Evaluando...</div>';
  try{
    const r=await fetch(API+'/evaluar/'+id+'/'+monto);
    if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error '+r.status)}
    const d=await r.json();
    const ok=d.elegible;
    box.className='eval-result '+(ok?'approved':'denied');
    box.innerHTML=`
      <h3 style="margin-bottom:12px;color:${ok?'#22c55e':'#ef4444'}">${ok?'Credito Aprobado':'Credito Denegado'}</h3>
      <div class="profile-grid">
        <div class="profile-item"><div class="pi-label">Monto Solicitado</div><div class="pi-value">${fmtMoney(monto)}</div></div>
        <div class="profile-item"><div class="pi-label">Score</div><div class="pi-value" style="color:${scoreColor(d.score||0)}">${d.score||0}</div></div>
        <div class="profile-item"><div class="pi-label">Limite Sugerido</div><div class="pi-value">${d.limite_sugerido!=null?fmtMoney(d.limite_sugerido):'N/A'}</div></div>
        <div class="profile-item"><div class="pi-label">Motivo</div><div class="pi-value">${d.motivo||'-'}</div></div>
      </div>`;
  }catch(e){
    box.className='eval-result denied';
    box.innerHTML='<div style="color:#ef4444">'+e.message+'</div>';
  }
}

loadStats();
loadRanking();
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
def dashboard_credito():
    """Dashboard HTML de Credit Scoring."""
    return DASHBOARD_HTML
