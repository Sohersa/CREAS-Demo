"""
Dashboard ejecutivo tiempo real — con design system Claude Design (Stripe-inspired).
GET /dashboard — metricas en vivo del negocio
"""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.orden import Orden
from app.models.pedido import Pedido
from app.models.proveedor import Proveedor
from app.models.prospecto import ProspectoProveedor
from app.models.usuario import Usuario
from app.models.incidencia import IncidenciaEntrega

router = APIRouter(tags=["dashboard-v2"])


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_v2():
    return HTMLResponse(DASHBOARD_HTML)


@router.get("/api/v2/dashboard")
def api_dashboard(db: Session = Depends(get_db)):
    """Datos del dashboard ejecutivo."""
    ahora = datetime.now(timezone.utc)
    hace_30d = ahora - timedelta(days=30)
    hace_7d = ahora - timedelta(days=7)
    hace_24h = ahora - timedelta(hours=24)

    # KPIs globales
    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    total_proveedores = db.query(func.count(Proveedor.id)).filter(Proveedor.activo == True).scalar() or 0
    total_pedidos = db.query(func.count(Pedido.id)).scalar() or 0
    total_ordenes = db.query(func.count(Orden.id)).scalar() or 0

    # Actividad ultima semana
    pedidos_7d = db.query(func.count(Pedido.id)).filter(Pedido.created_at >= hace_7d).scalar() or 0
    ordenes_7d = db.query(func.count(Orden.id)).filter(Orden.created_at >= hace_7d).scalar() or 0

    # Conversion
    entregadas = db.query(func.count(Orden.id)).filter(Orden.status == "entregada").scalar() or 0
    entregadas_24h = db.query(func.count(Orden.id)).filter(
        Orden.entregada_at >= hace_24h
    ).scalar() or 0

    # GMV (gross merchandise volume) ultima 30d
    gmv_30d = db.query(func.coalesce(func.sum(Orden.total), 0)).filter(
        Orden.created_at >= hace_30d
    ).scalar() or 0

    # Comisiones ObraYa (2%)
    comisiones_30d = db.query(func.coalesce(func.sum(Orden.comision_obraya), 0)).filter(
        Orden.created_at >= hace_30d,
        Orden.pagado == True,
    ).scalar() or 0

    # Incidencias (tasa de problema)
    incidencias_30d = db.query(func.count(IncidenciaEntrega.id)).filter(
        IncidenciaEntrega.created_at >= hace_30d
    ).scalar() or 0

    # Funnel outreach B2B
    prospectos_total = db.query(func.count(ProspectoProveedor.id)).scalar() or 0
    prospectos_contactados = db.query(func.count(ProspectoProveedor.id)).filter(
        ProspectoProveedor.status.in_(["contactado", "dialogo_activo", "interesado",
                                       "rechazado", "sin_respuesta", "convertido", "opt_out"])
    ).scalar() or 0
    prospectos_interesados = db.query(func.count(ProspectoProveedor.id)).filter(
        ProspectoProveedor.status.in_(["interesado", "convertido"])
    ).scalar() or 0
    prospectos_convertidos = db.query(func.count(ProspectoProveedor.id)).filter(
        ProspectoProveedor.status == "convertido"
    ).scalar() or 0

    # Ordenes por estado (para pie chart)
    por_estado = {}
    for (s, c) in db.query(Orden.status, func.count(Orden.id)).group_by(Orden.status).all():
        por_estado[s or "?"] = c

    return {
        "timestamp": ahora.isoformat(),
        "kpis": {
            "usuarios": total_usuarios,
            "proveedores_activos": total_proveedores,
            "pedidos_total": total_pedidos,
            "ordenes_total": total_ordenes,
            "pedidos_7d": pedidos_7d,
            "ordenes_7d": ordenes_7d,
            "entregadas_24h": entregadas_24h,
            "gmv_30d": float(gmv_30d),
            "comisiones_30d": float(comisiones_30d),
            "incidencias_30d": incidencias_30d,
            "tasa_incidencia_pct": round((incidencias_30d / max(entregadas, 1)) * 100, 1),
        },
        "outreach": {
            "prospectos_total": prospectos_total,
            "contactados": prospectos_contactados,
            "interesados": prospectos_interesados,
            "convertidos": prospectos_convertidos,
            "conversion_pct": round((prospectos_convertidos / max(prospectos_contactados, 1)) * 100, 1),
        },
        "ordenes_por_estado": por_estado,
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es" data-accent="violet">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard — ObraYa</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/design/design/tokens.css">
<link rel="stylesheet" href="/static/design/design/mobile.css?v=1">
<style>
  body { background: var(--paper-2); padding: 0; margin: 0; }
  .dash-header {
    background: var(--paper);
    border-bottom: 1px solid var(--line);
    padding: 20px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .dash-header h1 { font-size: 22px; font-weight: 600; letter-spacing: -0.02em; }
  .dash-header .live {
    display: inline-flex; align-items: center; gap: 8px;
    font-family: var(--font-mono); font-size: 11px;
    color: var(--ink-muted); letter-spacing: 0.1em; text-transform: uppercase;
  }
  .dash-header .dot {
    width: 8px; height: 8px; border-radius: 50%; background: #00A95F;
    box-shadow: 0 0 8px rgba(0,169,95,0.6); animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

  .dash-wrap { max-width: 1600px; margin: 0 auto; padding: 32px; }

  .section-title {
    font-size: 13px; font-weight: 600; color: var(--ink-muted);
    letter-spacing: 0.08em; text-transform: uppercase;
    margin: 40px 0 16px;
  }
  .section-title:first-child { margin-top: 0; }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
  .kpi {
    background: var(--paper); border-radius: var(--r-3); padding: 24px;
    border: 1px solid var(--line);
    transition: all 0.2s var(--ease);
  }
  .kpi:hover { transform: translateY(-2px); border-color: var(--violet); }
  .kpi-label {
    font-size: 12px; color: var(--ink-muted);
    letter-spacing: 0.05em; text-transform: uppercase;
    font-weight: 500; margin-bottom: 8px;
  }
  .kpi-value {
    font-size: 36px; font-weight: 600; color: var(--ink);
    letter-spacing: -0.02em; line-height: 1;
    font-feature-settings: 'tnum';
  }
  .kpi-value.violet { color: var(--violet); }
  .kpi-value.orange { color: var(--orange); }
  .kpi-value.green { color: #00A95F; }
  .kpi-sub {
    font-size: 12px; color: var(--ink-dim); margin-top: 6px;
  }

  .row { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
  @media (max-width: 900px) { .row { grid-template-columns: 1fr; } }

  .card {
    background: var(--paper); border-radius: var(--r-3);
    padding: 24px; border: 1px solid var(--line);
  }
  .card h3 { font-size: 15px; font-weight: 600; margin-bottom: 16px; letter-spacing: -0.01em; }

  /* Funnel */
  .funnel { display: flex; flex-direction: column; gap: 10px; }
  .funnel-step {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 18px; border-radius: var(--r-2);
    background: var(--paper-2);
    font-size: 14px;
  }
  .funnel-step .label { font-weight: 500; }
  .funnel-step .num { font-family: var(--font-mono); font-weight: 500; color: var(--violet); }
  .funnel-bar {
    background: var(--paper);
    border-radius: var(--r-1);
    height: 8px;
    overflow: hidden;
    margin: 4px 0 0;
  }
  .funnel-bar-fill {
    background: linear-gradient(90deg, var(--violet), var(--cyan));
    height: 100%;
    transition: width 0.6s var(--ease);
  }

  /* Status pie */
  .status-list { display: flex; flex-direction: column; gap: 6px; }
  .status-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 12px; border-radius: var(--r-1);
    background: var(--paper-2);
    font-size: 13px;
  }
  .status-row .dot-s {
    width: 8px; height: 8px; border-radius: 50%;
    display: inline-block; margin-right: 8px;
  }
  .loader {
    text-align: center; padding: 60px; color: var(--ink-muted);
  }

  .refresh-info {
    margin-top: 24px; text-align: right;
    font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);
  }
</style>
</head>
<body>

<div class="dash-header">
  <h1>ObraYa · Dashboard ejecutivo</h1>
  <span class="live"><span class="dot"></span> LIVE</span>
</div>

<div class="dash-wrap" id="dash-root">
  <div class="loader">Cargando datos…</div>
</div>

<script>
async function loadDashboard() {
  const res = await fetch('/api/v2/dashboard');
  const data = await res.json();
  render(data);
}

function render(d) {
  const root = document.getElementById('dash-root');
  const k = d.kpis, o = d.outreach;

  root.innerHTML = `
    <div class="section-title">Negocio · ultimos 30 dias</div>
    <div class="kpi-grid">
      <div class="kpi">
        <div class="kpi-label">GMV 30d</div>
        <div class="kpi-value violet">$${fmt(k.gmv_30d)}</div>
        <div class="kpi-sub">MXN facturados</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Comision ObraYa</div>
        <div class="kpi-value orange">$${fmt(k.comisiones_30d)}</div>
        <div class="kpi-sub">2% recaudado</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Ordenes 7d</div>
        <div class="kpi-value">${k.ordenes_7d}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Entregadas 24h</div>
        <div class="kpi-value green">${k.entregadas_24h}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Tasa incidencia</div>
        <div class="kpi-value">${k.tasa_incidencia_pct}%</div>
        <div class="kpi-sub">${k.incidencias_30d} incidencias</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Usuarios</div>
        <div class="kpi-value">${k.usuarios}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Proveedores activos</div>
        <div class="kpi-value">${k.proveedores_activos}</div>
      </div>
    </div>

    <div class="section-title">Outreach B2B (agente outbound)</div>
    <div class="row">
      <div class="card">
        <h3>Funnel de prospeccion</h3>
        <div class="funnel">
          ${funnelStep('Prospectos en BD', o.prospectos_total, 100)}
          ${funnelStep('Contactados', o.contactados, pct(o.contactados, o.prospectos_total))}
          ${funnelStep('Interesados', o.interesados, pct(o.interesados, o.contactados))}
          ${funnelStep('Convertidos', o.convertidos, pct(o.convertidos, o.contactados))}
        </div>
      </div>
      <div class="card">
        <h3>Conversion rate</h3>
        <div class="kpi-value violet" style="font-size:48px;margin-top:10px;">${o.conversion_pct}%</div>
        <div class="kpi-sub">${o.convertidos} convertidos de ${o.contactados} contactados</div>
      </div>
    </div>

    <div class="section-title">Ordenes por estado</div>
    <div class="card">
      <div class="status-list">
        ${Object.entries(d.ordenes_por_estado).sort((a,b)=>b[1]-a[1]).map(([s, c]) => `
          <div class="status-row">
            <span><span class="dot-s" style="background:${colorStatus(s)}"></span>${s}</span>
            <span class="mono" style="font-weight:500;">${c}</span>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="refresh-info">Ultimo refresh: ${new Date(d.timestamp).toLocaleString('es-MX')} · auto cada 30s</div>
  `;
}

function funnelStep(label, num, pct) {
  return `
    <div>
      <div class="funnel-step">
        <span class="label">${label}</span>
        <span class="num">${num}</span>
      </div>
      <div class="funnel-bar"><div class="funnel-bar-fill" style="width:${pct}%;"></div></div>
    </div>
  `;
}

function fmt(n) { return Number(n).toLocaleString('es-MX', {maximumFractionDigits: 0}); }
function pct(a, b) { return b ? Math.round((a/b) * 100) : 0; }
function colorStatus(s) {
  const map = {
    'entregada': '#00A95F', 'preparando': '#FFB84D', 'en_transito': '#635BFF',
    'en_obra': '#00D4FF', 'confirmada': '#425466', 'cancelada': '#E85D2B',
    'pendiente_aprobacion': '#FF80B5', 'con_incidencia': '#FF7A45',
  };
  return map[s] || '#8792A2';
}

loadDashboard();
setInterval(loadDashboard, 30000);
</script>

</body>
</html>"""
