"""
Inteligencia de Precios — Dashboard de la mega base de datos de costos.
Busqueda, historial, ranking y analisis de precios por producto/proveedor/zona.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional

from app.database import get_db
from app.models.precio_historico import PrecioHistorico
from app.models.catalogo import CatalogoMaestro
from app.models.proveedor import Proveedor

router = APIRouter(prefix="/precios", tags=["precios"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/api/resumen")
def resumen_precios(db: Session = Depends(get_db)):
    """Estadisticas generales de la base de precios."""
    total_registros = db.query(func.count(PrecioHistorico.id)).scalar() or 0
    productos_unicos = db.query(func.count(distinct(PrecioHistorico.producto_normalizado))).scalar() or 0
    proveedores_unicos = db.query(func.count(distinct(PrecioHistorico.proveedor_id))).filter(
        PrecioHistorico.proveedor_id.isnot(None)
    ).scalar() or 0
    zonas_unicas = db.query(func.count(distinct(PrecioHistorico.zona))).filter(
        PrecioHistorico.zona.isnot(None)
    ).scalar() or 0

    fecha_min = db.query(func.min(PrecioHistorico.fecha)).scalar()
    fecha_max = db.query(func.max(PrecioHistorico.fecha)).scalar()

    return {
        "total_registros": total_registros,
        "productos_unicos": productos_unicos,
        "proveedores_unicos": proveedores_unicos,
        "zonas_unicas": zonas_unicas,
        "fecha_min": str(fecha_min) if fecha_min else None,
        "fecha_max": str(fecha_max) if fecha_max else None,
    }


@router.get("/api/buscar")
def buscar_precios(
    q: str = Query("", description="Buscar por nombre de producto"),
    zona: Optional[str] = Query(None, description="Filtrar por zona"),
    proveedor_id: Optional[int] = Query(None, description="Filtrar por proveedor"),
    db: Session = Depends(get_db),
):
    """Buscar precios por producto, zona y/o proveedor."""
    query = db.query(PrecioHistorico)

    if q:
        term = f"%{q}%"
        query = query.filter(
            (PrecioHistorico.producto_normalizado.ilike(term))
            | (PrecioHistorico.producto_nombre.ilike(term))
        )
    if zona:
        query = query.filter(PrecioHistorico.zona.ilike(f"%{zona}%"))
    if proveedor_id:
        query = query.filter(PrecioHistorico.proveedor_id == proveedor_id)

    records = query.order_by(PrecioHistorico.fecha.desc()).limit(200).all()

    # Agrupar por producto
    productos = {}
    for r in records:
        key = r.producto_normalizado or r.producto_nombre
        if key not in productos:
            productos[key] = {
                "producto": key,
                "categoria": r.categoria,
                "catalogo_id": r.catalogo_id,
                "precios": [],
            }
        productos[key]["precios"].append({
            "id": r.id,
            "proveedor_id": r.proveedor_id,
            "proveedor_nombre": r.proveedor_nombre,
            "precio_unitario": r.precio_unitario,
            "precio_efectivo": r.precio_efectivo,
            "unidad": r.unidad,
            "zona": r.zona,
            "fecha": str(r.fecha) if r.fecha else None,
            "incluye_flete": r.incluye_flete,
            "costo_flete": r.costo_flete,
            "tiempo_entrega": r.tiempo_entrega,
            "disponibilidad": r.disponibilidad,
            "es_outlier": r.es_outlier,
            "confianza": r.confianza,
        })

    return {"resultados": list(productos.values()), "total": len(records)}


@router.get("/api/producto/{catalogo_id}/historial")
def historial_producto(catalogo_id: int, db: Session = Depends(get_db)):
    """Historial de precios para un producto especifico del catalogo."""
    records = (
        db.query(PrecioHistorico)
        .filter(PrecioHistorico.catalogo_id == catalogo_id)
        .order_by(PrecioHistorico.fecha.desc())
        .all()
    )

    if not records:
        return {"catalogo_id": catalogo_id, "proveedores": [], "resumen": None}

    # Info del catalogo
    catalogo = db.query(CatalogoMaestro).filter(CatalogoMaestro.id == catalogo_id).first()

    # Agrupar por proveedor
    por_proveedor = {}
    all_prices = []
    for r in records:
        prov_key = r.proveedor_id or r.proveedor_nombre or "Desconocido"
        if prov_key not in por_proveedor:
            por_proveedor[prov_key] = {
                "proveedor_id": r.proveedor_id,
                "proveedor_nombre": r.proveedor_nombre,
                "precios": [],
            }
        precio = r.precio_efectivo or r.precio_unitario
        por_proveedor[prov_key]["precios"].append({
            "precio": precio,
            "unidad": r.unidad,
            "zona": r.zona,
            "fecha": str(r.fecha) if r.fecha else None,
            "incluye_flete": r.incluye_flete,
            "costo_flete": r.costo_flete,
        })
        all_prices.append(precio)

    # Calcular tendencia
    resumen = None
    if all_prices:
        resumen = {
            "min": round(min(all_prices), 2),
            "max": round(max(all_prices), 2),
            "avg": round(sum(all_prices) / len(all_prices), 2),
            "ultimo": all_prices[0],
            "total_registros": len(all_prices),
        }

    return {
        "catalogo_id": catalogo_id,
        "producto": catalogo.nombre if catalogo else records[0].producto_normalizado,
        "categoria": catalogo.categoria if catalogo else records[0].categoria,
        "proveedores": list(por_proveedor.values()),
        "resumen": resumen,
    }


@router.get("/api/ranking-materiales")
def ranking_materiales(db: Session = Depends(get_db)):
    """Top 20 materiales mas cotizados con rango de precios."""
    results = (
        db.query(
            PrecioHistorico.producto_normalizado,
            PrecioHistorico.categoria,
            PrecioHistorico.unidad,
            func.count(PrecioHistorico.id).label("total_cotizaciones"),
            func.min(PrecioHistorico.precio_unitario).label("precio_min"),
            func.max(PrecioHistorico.precio_unitario).label("precio_max"),
            func.avg(PrecioHistorico.precio_unitario).label("precio_avg"),
            func.count(distinct(PrecioHistorico.proveedor_id)).label("num_proveedores"),
        )
        .filter(PrecioHistorico.producto_normalizado.isnot(None))
        .group_by(
            PrecioHistorico.producto_normalizado,
            PrecioHistorico.categoria,
            PrecioHistorico.unidad,
        )
        .order_by(func.count(PrecioHistorico.id).desc())
        .limit(20)
        .all()
    )

    ranking = []
    for r in results:
        ranking.append({
            "producto": r.producto_normalizado,
            "categoria": r.categoria,
            "unidad": r.unidad,
            "total_cotizaciones": r.total_cotizaciones,
            "precio_min": round(r.precio_min, 2) if r.precio_min else None,
            "precio_max": round(r.precio_max, 2) if r.precio_max else None,
            "precio_avg": round(float(r.precio_avg), 2) if r.precio_avg else None,
            "num_proveedores": r.num_proveedores,
        })

    return {"ranking": ranking}


@router.get("/api/zonas")
def listar_zonas(db: Session = Depends(get_db)):
    """Lista de todas las zonas con registros de precios."""
    zonas = (
        db.query(PrecioHistorico.zona)
        .filter(PrecioHistorico.zona.isnot(None))
        .distinct()
        .order_by(PrecioHistorico.zona)
        .all()
    )
    return {"zonas": [z[0] for z in zonas]}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTML Dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/", response_class=HTMLResponse)
def precios_dashboard():
    """Dashboard de Inteligencia de Precios."""
    return HTMLResponse(PRECIOS_HTML)


PRECIOS_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ObraYa — Inteligencia de Precios</title>
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

/* Header */
.header {
  background: linear-gradient(135deg, var(--bg2) 0%, #0f172a 100%);
  border-bottom: 1px solid var(--border);
  padding: 20px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--orange);
}
.header h1 span { color: var(--text); font-weight: 400; }
.header a {
  color: var(--text2);
  text-decoration: none;
  font-size: 13px;
  padding: 6px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  transition: all 0.2s;
}
.header a:hover {
  border-color: var(--orange);
  color: var(--orange);
}

/* KPIs */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
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
.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}
.kpi-label {
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.kpi-card.orange .kpi-value { color: var(--orange); }
.kpi-card.green .kpi-value { color: var(--green); }
.kpi-card.blue .kpi-value { color: var(--blue); }
.kpi-card.yellow .kpi-value { color: var(--yellow); }

/* Search */
.search-section {
  padding: 0 32px 24px;
}
.search-bar {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: end;
}
.search-field {
  flex: 1;
  min-width: 200px;
}
.search-field label {
  display: block;
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.search-field input, .search-field select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.search-field input:focus, .search-field select:focus {
  border-color: var(--orange);
}
.search-field select option {
  background: var(--bg2);
  color: var(--text);
}
.btn-search {
  padding: 10px 28px;
  background: var(--orange);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.btn-search:hover {
  background: #e55a1b;
  transform: translateY(-1px);
}

/* Content */
.content {
  padding: 0 32px 40px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* Results table */
.results-container {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  display: none;
}
.results-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.results-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--orange);
}
.results-count {
  font-size: 13px;
  color: var(--text3);
}
.results-table {
  width: 100%;
  border-collapse: collapse;
}
.results-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
  background: var(--bg2);
  position: sticky;
  top: 0;
}
.results-table td {
  padding: 10px 16px;
  font-size: 13px;
  border-bottom: 1px solid rgba(42,53,72,0.5);
  color: var(--text2);
}
.results-table tr:hover td {
  background: rgba(255,107,43,0.05);
}
.results-table .price-cell {
  font-weight: 700;
  font-size: 14px;
}
.price-low { color: var(--green) !important; }
.price-high { color: var(--red) !important; }
.price-mid { color: var(--yellow) !important; }
.flete-si { color: var(--green); font-size: 11px; }
.flete-no { color: var(--text3); font-size: 11px; }
.outlier-badge {
  background: rgba(239,68,68,0.15);
  color: var(--red);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.product-link {
  color: var(--blue);
  cursor: pointer;
  text-decoration: none;
}
.product-link:hover {
  text-decoration: underline;
}
.table-scroll {
  max-height: 500px;
  overflow-y: auto;
}

/* Ranking */
.ranking-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}
.ranking-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.2s;
  cursor: pointer;
}
.ranking-card:hover {
  border-color: var(--orange);
  background: var(--card-hover);
}
.ranking-pos {
  font-size: 22px;
  font-weight: 700;
  color: var(--text3);
  min-width: 36px;
  text-align: center;
}
.ranking-pos.top3 { color: var(--orange); }
.ranking-info { flex: 1; }
.ranking-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}
.ranking-meta {
  font-size: 11px;
  color: var(--text3);
}
.ranking-bar-container {
  width: 120px;
  height: 8px;
  background: var(--bg2);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}
.ranking-bar {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--green), var(--yellow), var(--red));
}
.ranking-prices {
  text-align: right;
  min-width: 100px;
}
.ranking-prices .price-range {
  font-size: 12px;
  color: var(--text2);
}
.ranking-prices .price-avg {
  font-size: 14px;
  font-weight: 700;
  color: var(--orange);
}

/* Detail modal */
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 1000;
  justify-content: center;
  align-items: center;
  padding: 20px;
}
.modal-overlay.active { display: flex; }
.modal-content {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: 100%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
  padding: 32px;
}
.modal-close {
  float: right;
  background: none;
  border: none;
  color: var(--text3);
  font-size: 24px;
  cursor: pointer;
}
.modal-close:hover { color: var(--text); }
.modal-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--orange);
  margin-bottom: 4px;
}
.modal-subtitle {
  font-size: 13px;
  color: var(--text3);
  margin-bottom: 20px;
}
.modal-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.modal-stat {
  text-align: center;
}
.modal-stat .val {
  font-size: 24px;
  font-weight: 700;
}
.modal-stat .lbl {
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
}
.modal-stat.green .val { color: var(--green); }
.modal-stat.red .val { color: var(--red); }
.modal-stat.blue .val { color: var(--blue); }
.modal-stat.orange .val { color: var(--orange); }

.prov-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
}
.prov-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--blue);
  margin-bottom: 10px;
}
.prov-prices {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.prov-price-chip {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
}
.prov-price-chip .amt {
  font-weight: 700;
  color: var(--text);
}
.prov-price-chip .dt {
  color: var(--text3);
  margin-left: 6px;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text3);
}
.empty-state .icon { font-size: 48px; margin-bottom: 12px; }
.empty-state .msg { font-size: 16px; }

/* Loading */
.loading {
  text-align: center;
  padding: 40px;
  color: var(--text3);
}

/* Responsive */
@media (max-width: 768px) {
  .header { padding: 16px; }
  .kpi-grid { padding: 16px; grid-template-columns: repeat(2, 1fr); }
  .search-section { padding: 0 16px 16px; }
  .search-bar { flex-direction: column; }
  .search-field { min-width: 100%; }
  .content { padding: 0 16px 32px; }
  .ranking-grid { grid-template-columns: 1fr; }
  .ranking-bar-container { display: none; }
  .modal-content { padding: 20px; }
  .modal-stats { gap: 16px; }
  .results-table { font-size: 12px; }
  .results-table th, .results-table td { padding: 8px 10px; }
}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div>
    <h1>Inteligencia de <span>Precios</span></h1>
  </div>
  <a href="/hub/">&#8592; Hub Central</a>
</div>

<!-- KPIs -->
<div class="kpi-grid" id="kpiGrid">
  <div class="kpi-card orange"><div class="kpi-value" id="kpiTotal">-</div><div class="kpi-label">Registros de Precios</div></div>
  <div class="kpi-card green"><div class="kpi-value" id="kpiProductos">-</div><div class="kpi-label">Productos Unicos</div></div>
  <div class="kpi-card blue"><div class="kpi-value" id="kpiProveedores">-</div><div class="kpi-label">Proveedores</div></div>
  <div class="kpi-card yellow"><div class="kpi-value" id="kpiZonas">-</div><div class="kpi-label">Zonas / Ciudades</div></div>
  <div class="kpi-card"><div class="kpi-value" id="kpiFechas" style="font-size:14px;">-</div><div class="kpi-label">Rango de Fechas</div></div>
</div>

<!-- Search -->
<div class="search-section">
  <div class="search-bar">
    <div class="search-field" style="flex:2;">
      <label>Buscar Producto</label>
      <input type="text" id="searchInput" placeholder="Ej: acero, concreto, block, varilla..." />
    </div>
    <div class="search-field" style="flex:1;">
      <label>Zona / Ciudad</label>
      <select id="zonaSelect">
        <option value="">Todas las zonas</option>
      </select>
    </div>
    <button class="btn-search" onclick="buscar()">Buscar</button>
  </div>
</div>

<!-- Results -->
<div class="content">
  <div class="results-container" id="resultsContainer">
    <div class="results-header">
      <h3>Resultados de Busqueda</h3>
      <span class="results-count" id="resultsCount"></span>
    </div>
    <div class="table-scroll">
      <table class="results-table">
        <thead>
          <tr>
            <th>Producto</th>
            <th>Proveedor</th>
            <th>Precio Unit.</th>
            <th>Precio Efec.</th>
            <th>Unidad</th>
            <th>Zona</th>
            <th>Fecha</th>
            <th>Flete</th>
          </tr>
        </thead>
        <tbody id="resultsBody"></tbody>
      </table>
    </div>
  </div>

  <!-- Top Materials -->
  <div class="section-title">Top Materiales Mas Cotizados</div>
  <div class="ranking-grid" id="rankingGrid">
    <div class="loading">Cargando ranking...</div>
  </div>
</div>

<!-- Product detail modal -->
<div class="modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()">
  <div class="modal-content">
    <button class="modal-close" onclick="closeModal()">&#10005;</button>
    <div id="modalBody">
      <div class="loading">Cargando historial...</div>
    </div>
  </div>
</div>

<script>
// ── Load KPIs ──
async function loadKPIs() {
  try {
    const r = await fetch('/precios/api/resumen');
    const d = await r.json();
    document.getElementById('kpiTotal').textContent = d.total_registros.toLocaleString('es-MX');
    document.getElementById('kpiProductos').textContent = d.productos_unicos.toLocaleString('es-MX');
    document.getElementById('kpiProveedores').textContent = d.proveedores_unicos.toLocaleString('es-MX');
    document.getElementById('kpiZonas').textContent = d.zonas_unicas.toLocaleString('es-MX');
    if (d.fecha_min && d.fecha_max) {
      const fmin = d.fecha_min.split(' ')[0];
      const fmax = d.fecha_max.split(' ')[0];
      document.getElementById('kpiFechas').textContent = fmin + ' → ' + fmax;
    } else {
      document.getElementById('kpiFechas').textContent = 'Sin datos';
    }
  } catch(e) {
    console.error('Error loading KPIs:', e);
  }
}

// ── Load zonas ──
async function loadZonas() {
  try {
    const r = await fetch('/precios/api/zonas');
    const d = await r.json();
    const sel = document.getElementById('zonaSelect');
    d.zonas.forEach(z => {
      const opt = document.createElement('option');
      opt.value = z;
      opt.textContent = z;
      sel.appendChild(opt);
    });
  } catch(e) {}
}

// ── Search ──
async function buscar() {
  const q = document.getElementById('searchInput').value.trim();
  const zona = document.getElementById('zonaSelect').value;
  if (!q && !zona) return;

  const container = document.getElementById('resultsContainer');
  const body = document.getElementById('resultsBody');
  container.style.display = 'block';
  body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:30px;color:var(--text3);">Buscando...</td></tr>';

  try {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (zona) params.set('zona', zona);
    const r = await fetch('/precios/api/buscar?' + params.toString());
    const d = await r.json();

    document.getElementById('resultsCount').textContent = d.total + ' registros encontrados';

    if (d.total === 0) {
      body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text3);">No se encontraron resultados</td></tr>';
      return;
    }

    // Flatten all prices and find min/max per product for color coding
    let rows = [];
    d.resultados.forEach(prod => {
      const prices = prod.precios.map(p => p.precio_unitario).filter(p => p > 0);
      const minP = Math.min(...prices);
      const maxP = Math.max(...prices);
      prod.precios.forEach(p => {
        rows.push({...p, producto: prod.producto, catalogo_id: prod.catalogo_id, minP, maxP});
      });
    });

    body.innerHTML = rows.map(r => {
      let priceClass = 'price-mid';
      if (r.minP !== r.maxP) {
        if (r.precio_unitario === r.minP) priceClass = 'price-low';
        else if (r.precio_unitario === r.maxP) priceClass = 'price-high';
      }
      const outlier = r.es_outlier ? ' <span class="outlier-badge">OUTLIER</span>' : '';
      const flete = r.incluye_flete
        ? '<span class="flete-si">Incluido' + (r.costo_flete ? ' ($' + r.costo_flete.toLocaleString('es-MX') + ')' : '') + '</span>'
        : '<span class="flete-no">No incluido</span>';
      const prodLink = r.catalogo_id
        ? '<a class="product-link" onclick="verHistorial(' + r.catalogo_id + ')">' + esc(r.producto) + '</a>'
        : esc(r.producto);
      const fecha = r.fecha ? r.fecha.split(' ')[0] : '-';
      const pEfec = r.precio_efectivo ? '$' + r.precio_efectivo.toLocaleString('es-MX', {minimumFractionDigits:2}) : '-';
      return '<tr>'
        + '<td>' + prodLink + outlier + '</td>'
        + '<td>' + esc(r.proveedor_nombre || '-') + '</td>'
        + '<td class="price-cell ' + priceClass + '">$' + r.precio_unitario.toLocaleString('es-MX', {minimumFractionDigits:2}) + '</td>'
        + '<td style="color:var(--text2)">' + pEfec + '</td>'
        + '<td>' + esc(r.unidad || '-') + '</td>'
        + '<td>' + esc(r.zona || '-') + '</td>'
        + '<td>' + fecha + '</td>'
        + '<td>' + flete + '</td>'
        + '</tr>';
    }).join('');
  } catch(e) {
    body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:30px;color:var(--red);">Error buscando precios</td></tr>';
  }
}

// ── Ranking ──
async function loadRanking() {
  try {
    const r = await fetch('/precios/api/ranking-materiales');
    const d = await r.json();
    const grid = document.getElementById('rankingGrid');

    if (!d.ranking || d.ranking.length === 0) {
      grid.innerHTML = '<div class="empty-state"><div class="icon">&#128200;</div><div class="msg">No hay datos de precios todavia</div></div>';
      return;
    }

    const maxCot = Math.max(...d.ranking.map(r => r.total_cotizaciones));

    grid.innerHTML = d.ranking.map((item, i) => {
      const barW = Math.max(10, (item.total_cotizaciones / maxCot) * 100);
      const posClass = i < 3 ? 'top3' : '';
      return '<div class="ranking-card" onclick="buscarProducto(\\'' + esc(item.producto) + '\\')">'
        + '<div class="ranking-pos ' + posClass + '">#' + (i+1) + '</div>'
        + '<div class="ranking-info">'
        + '<div class="ranking-name">' + esc(item.producto) + '</div>'
        + '<div class="ranking-meta">' + esc(item.categoria || '') + ' | ' + item.total_cotizaciones + ' cotizaciones | ' + item.num_proveedores + ' proveedores</div>'
        + '</div>'
        + '<div class="ranking-bar-container"><div class="ranking-bar" style="width:' + barW + '%"></div></div>'
        + '<div class="ranking-prices">'
        + '<div class="price-range">$' + (item.precio_min||0).toLocaleString('es-MX') + ' - $' + (item.precio_max||0).toLocaleString('es-MX') + '</div>'
        + '<div class="price-avg">Prom: $' + (item.precio_avg||0).toLocaleString('es-MX') + '</div>'
        + '</div>'
        + '</div>';
    }).join('');
  } catch(e) {
    document.getElementById('rankingGrid').innerHTML = '<div class="empty-state"><div class="msg">Error cargando ranking</div></div>';
  }
}

// ── Product history modal ──
async function verHistorial(catalogoId) {
  document.getElementById('modalOverlay').classList.add('active');
  document.getElementById('modalBody').innerHTML = '<div class="loading">Cargando historial...</div>';

  try {
    const r = await fetch('/precios/api/producto/' + catalogoId + '/historial');
    const d = await r.json();

    if (!d.proveedores || d.proveedores.length === 0) {
      document.getElementById('modalBody').innerHTML = '<div class="empty-state"><div class="msg">Sin historial de precios para este producto</div></div>';
      return;
    }

    let html = '<div class="modal-title">' + esc(d.producto || 'Producto') + '</div>';
    html += '<div class="modal-subtitle">' + esc(d.categoria || '') + ' | Catalogo #' + d.catalogo_id + '</div>';

    if (d.resumen) {
      html += '<div class="modal-stats">';
      html += '<div class="modal-stat green"><div class="val">$' + d.resumen.min.toLocaleString('es-MX') + '</div><div class="lbl">Minimo</div></div>';
      html += '<div class="modal-stat red"><div class="val">$' + d.resumen.max.toLocaleString('es-MX') + '</div><div class="lbl">Maximo</div></div>';
      html += '<div class="modal-stat blue"><div class="val">$' + d.resumen.avg.toLocaleString('es-MX') + '</div><div class="lbl">Promedio</div></div>';
      html += '<div class="modal-stat orange"><div class="val">$' + d.resumen.ultimo.toLocaleString('es-MX') + '</div><div class="lbl">Ultimo</div></div>';
      html += '<div class="modal-stat"><div class="val">' + d.resumen.total_registros + '</div><div class="lbl">Total Registros</div></div>';
      html += '</div>';
    }

    d.proveedores.forEach(prov => {
      html += '<div class="prov-section">';
      html += '<div class="prov-name">' + esc(prov.proveedor_nombre || 'Proveedor #' + (prov.proveedor_id || '?')) + '</div>';
      html += '<div class="prov-prices">';
      prov.precios.forEach(p => {
        const fecha = p.fecha ? p.fecha.split(' ')[0] : '';
        html += '<div class="prov-price-chip"><span class="amt">$' + p.precio.toLocaleString('es-MX', {minimumFractionDigits:2}) + '</span><span class="dt">' + fecha + '</span></div>';
      });
      html += '</div></div>';
    });

    document.getElementById('modalBody').innerHTML = html;
  } catch(e) {
    document.getElementById('modalBody').innerHTML = '<div class="empty-state"><div class="msg">Error cargando historial</div></div>';
  }
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('active');
}

function buscarProducto(nombre) {
  document.getElementById('searchInput').value = nombre;
  buscar();
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// Enter key triggers search
document.getElementById('searchInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') buscar();
});

// Init
loadKPIs();
loadZonas();
loadRanking();
</script>

</body>
</html>"""
