"""
Router de pagos — Stripe Checkout, webhooks, y endpoints de estado.
"""
import logging

import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.orden import Orden
from app.services.pagos import (
    calcular_desglose,
    crear_sesion_pago,
    confirmar_pago,
    registrar_pago_proveedor,
    simular_pago,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pagos", tags=["pagos"])


# ─── Crear sesion de Stripe Checkout ──────────────────────────────

@router.post("/crear-sesion/{orden_id}")
def crear_sesion(orden_id: int, db: Session = Depends(get_db)):
    """Crea una sesion de Stripe Checkout y retorna la URL de pago."""
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if orden.pagado:
        raise HTTPException(status_code=400, detail="Esta orden ya fue pagada")

    if not orden.total or orden.total <= 0:
        raise HTTPException(status_code=400, detail="La orden no tiene un total valido")

    try:
        resultado = crear_sesion_pago(orden_id, orden.total)
        return {
            "ok": True,
            "session_id": resultado["session_id"],
            "url": resultado["url"],
            "desglose": calcular_desglose(orden.total),
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error de Stripe al crear sesion: {e}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)}")


# ─── Callback de exito ────────────────────────────────────────────

@router.get("/exito")
def pago_exito(session_id: str, db: Session = Depends(get_db)):
    """Callback de Stripe tras pago exitoso. Confirma el pago en BD."""
    try:
        orden = confirmar_pago(db, session_id)
        if not orden:
            raise HTTPException(status_code=404, detail="No se pudo confirmar el pago")

        desglose = calcular_desglose(orden.total)
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Pago Exitoso - ObraYa</title>
            <style>
                body {{ font-family: system-ui, sans-serif; max-width: 500px; margin: 40px auto; padding: 20px; text-align: center; }}
                .success {{ color: #16a34a; font-size: 48px; }}
                .card {{ background: #f0fdf4; border-radius: 12px; padding: 24px; margin: 20px 0; }}
                .row {{ display: flex; justify-content: space-between; padding: 8px 0; }}
                .label {{ color: #666; }}
                .total {{ font-weight: bold; font-size: 1.2em; border-top: 2px solid #ccc; padding-top: 12px; margin-top: 8px; }}
                a {{ color: #f97316; text-decoration: none; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="success">&#10003;</div>
            <h1>Pago recibido</h1>
            <p>Tu pago para la <strong>Orden #{orden.id}</strong> ha sido procesado correctamente.</p>
            <div class="card">
                <div class="row"><span class="label">Materiales</span><span>${desglose['subtotal']:,.2f} MXN</span></div>
                <div class="row"><span class="label">Comision de servicio (2%)</span><span>${desglose['comision_2pct']:,.2f} MXN</span></div>
                <div class="row total"><span>Total cobrado</span><span>${desglose['total_con_comision']:,.2f} MXN</span></div>
            </div>
            <p>Tu proveedor ya fue notificado y prepara tu pedido.</p>
            <p><a href="/portal">Ir al portal de seguimiento &rarr;</a></p>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error(f"Error en callback de exito: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar el pago")


# ─── Callback de cancelacion ──────────────────────────────────────

@router.get("/cancelado")
def pago_cancelado():
    """Callback cuando el usuario cancela el pago en Stripe."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pago Cancelado - ObraYa</title>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 500px; margin: 40px auto; padding: 20px; text-align: center; }
            .cancel { color: #dc2626; font-size: 48px; }
            a { color: #f97316; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="cancel">&#10007;</div>
        <h1>Pago cancelado</h1>
        <p>No se realizo ningun cobro. Puedes intentar de nuevo cuando quieras.</p>
        <p><a href="/portal">Volver al portal &rarr;</a></p>
    </body>
    </html>
    """)


# ─── Webhook de Stripe ────────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook de Stripe para confirmar pagos de forma segura.
    Stripe envia eventos aqui cuando un pago se completa.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload invalido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma invalida")

    # Procesar evento de pago completado
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        orden = confirmar_pago(db, session["id"])
        if orden:
            logger.info(f"Webhook: pago confirmado para orden {orden.id}")
        else:
            logger.error(f"Webhook: no se pudo confirmar pago para session {session['id']}")

    return {"received": True}


# ─── Simular pago (testing) ───────────────────────────────────────

@router.post("/simular/{orden_id}")
def simular_pago_endpoint(orden_id: int, db: Session = Depends(get_db)):
    """
    Simula un pago exitoso sin Stripe. Solo para desarrollo/testing.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="No disponible en produccion")

    orden = simular_pago(db, orden_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    return {
        "ok": True,
        "mensaje": f"Pago simulado para orden {orden_id}",
        "orden_id": orden.id,
        "pagado": orden.pagado,
        "metodo_pago": orden.metodo_pago,
        "desglose": calcular_desglose(orden.total),
        "monto_proveedor": orden.monto_proveedor,
        "comision_obraya": orden.comision_obraya,
    }


# ─── Estado de pago ───────────────────────────────────────────────

@router.get("/estado/{orden_id}")
def estado_pago(orden_id: int, db: Session = Depends(get_db)):
    """Consulta el estado de pago de una orden."""
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    desglose = calcular_desglose(orden.total) if orden.total else None

    return {
        "orden_id": orden.id,
        "total": orden.total,
        "pagado": orden.pagado,
        "metodo_pago": orden.metodo_pago,
        "fecha_pago": orden.fecha_pago.isoformat() if orden.fecha_pago else None,
        "desglose": desglose,
        "comision_obraya": orden.comision_obraya,
        "monto_proveedor": orden.monto_proveedor,
        "pago_proveedor_status": orden.pago_proveedor_status,
        "pago_proveedor_fecha": orden.pago_proveedor_fecha.isoformat() if orden.pago_proveedor_fecha else None,
    }


# ─── Resumen para dashboard ─────────────────────────────────────

@router.get("/api/resumen")
def resumen_pagos(db: Session = Depends(get_db)):
    """Resumen de pagos para el dashboard."""
    total_ordenes = db.query(func.count(Orden.id)).scalar() or 0
    ordenes_pagadas = db.query(func.count(Orden.id)).filter(Orden.pagado == True).scalar() or 0
    ordenes_pendientes = db.query(func.count(Orden.id)).filter(
        Orden.pagado == False, Orden.status != "cancelada"
    ).scalar() or 0
    total_cobrado = db.query(func.sum(Orden.total)).filter(Orden.pagado == True).scalar() or 0
    total_comisiones = db.query(func.sum(Orden.comision_obraya)).filter(Orden.pagado == True).scalar() or 0

    # Recent orders with payment info
    ordenes = db.query(Orden).order_by(Orden.created_at.desc()).limit(30).all()

    return {
        "total_ordenes": total_ordenes,
        "ordenes_pagadas": ordenes_pagadas,
        "ordenes_pendientes": ordenes_pendientes,
        "total_cobrado": round(total_cobrado, 2),
        "total_comisiones": round(total_comisiones, 2),
        "ordenes": [
            {
                "id": o.id,
                "total": o.total,
                "pagado": o.pagado,
                "metodo_pago": o.metodo_pago,
                "fecha_pago": o.fecha_pago.isoformat() if o.fecha_pago else None,
                "status": o.status,
                "comision_obraya": o.comision_obraya,
                "monto_proveedor": o.monto_proveedor,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in ordenes
        ],
    }


# ─── Dashboard HTML ──────────────────────────────────────────────

PAGOS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Pagos - ObraYa</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e1a;
            color: #f1f5f9;
            min-height: 100vh;
        }
        a { color: #ff6b2b; text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* Header */
        .header {
            background: #1a2332;
            border-bottom: 1px solid #2a3548;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f1f5f9;
        }
        .header h1 span { color: #ff6b2b; }
        .back-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #2a3548;
            padding: 8px 16px;
            border-radius: 8px;
            color: #94a3b8;
            font-size: 0.875rem;
            transition: all 0.2s;
        }
        .back-link:hover {
            background: #374151;
            color: #f1f5f9;
            text-decoration: none;
        }

        /* Container */
        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 24px;
        }

        /* KPI Grid */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .kpi-card {
            background: #1a2332;
            border: 1px solid #2a3548;
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.2s, border-color 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: #3b82f6;
        }
        .kpi-label {
            font-size: 0.8rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 1.75rem;
            font-weight: 700;
        }
        .kpi-sub {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 4px;
        }
        .kpi-value.green { color: #22c55e; }
        .kpi-value.blue { color: #3b82f6; }
        .kpi-value.orange { color: #ff6b2b; }
        .kpi-value.yellow { color: #eab308; }
        .kpi-value.red { color: #ef4444; }

        /* Cards */
        .card {
            background: #1a2332;
            border: 1px solid #2a3548;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 16px;
            color: #f1f5f9;
        }

        /* Stripe status */
        .stripe-status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        .stripe-active {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #22c55e;
        }
        .stripe-inactive {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #ef4444;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-dot.green { background: #22c55e; }
        .status-dot.red { background: #ef4444; }

        /* Table */
        .table-wrap {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }
        thead th {
            text-align: left;
            padding: 10px 12px;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #2a3548;
            white-space: nowrap;
        }
        tbody td {
            padding: 10px 12px;
            border-bottom: 1px solid #1e293b;
            color: #94a3b8;
            white-space: nowrap;
        }
        tbody tr:hover { background: rgba(59, 130, 246, 0.05); }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-green { background: rgba(34,197,94,0.15); color: #22c55e; }
        .badge-red { background: rgba(239,68,68,0.15); color: #ef4444; }
        .badge-yellow { background: rgba(234,179,8,0.15); color: #eab308; }
        .badge-blue { background: rgba(59,130,246,0.15); color: #3b82f6; }
        .badge-gray { background: rgba(100,116,139,0.15); color: #94a3b8; }

        .check { color: #22c55e; font-weight: bold; }
        .cross { color: #ef4444; font-weight: bold; }

        /* Buttons */
        .btn {
            display: inline-block;
            padding: 5px 12px;
            border: none;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.85; }
        .btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .btn-orange { background: #ff6b2b; color: #fff; }
        .btn-blue { background: #3b82f6; color: #fff; }
        .btn-sm { padding: 4px 10px; font-size: 0.7rem; }

        /* Lookup section */
        .lookup-row {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }
        .lookup-row input {
            background: #0a0e1a;
            border: 1px solid #2a3548;
            color: #f1f5f9;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 0.9rem;
            width: 160px;
        }
        .lookup-row input:focus {
            outline: none;
            border-color: #3b82f6;
        }
        .lookup-result {
            margin-top: 16px;
            font-size: 0.85rem;
            color: #94a3b8;
        }
        .lookup-result pre {
            background: #0a0e1a;
            border: 1px solid #2a3548;
            border-radius: 8px;
            padding: 12px;
            overflow-x: auto;
            color: #f1f5f9;
            margin-top: 8px;
        }

        /* Loading */
        .loading-overlay {
            text-align: center;
            padding: 48px;
            color: #64748b;
        }
        .spinner {
            display: inline-block;
            width: 32px;
            height: 32px;
            border: 3px solid #2a3548;
            border-top-color: #ff6b2b;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Responsive */
        @media (max-width: 640px) {
            .container { padding: 16px; }
            .header { padding: 12px 16px; }
            .header h1 { font-size: 1.2rem; }
            .kpi-value { font-size: 1.3rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1><span>&#9679;</span> Sistema de Pagos</h1>
        </div>
        <a href="/hub/" class="back-link">&larr; Volver al Hub</a>
    </div>

    <div class="container" id="app">
        <div class="loading-overlay" id="loading">
            <div class="spinner"></div>
            <p style="margin-top:12px;">Cargando datos de pagos...</p>
        </div>
        <div id="content" style="display:none;">

            <!-- Stripe Status -->
            <div class="card" style="margin-bottom:20px; padding:14px 20px;">
                <div id="stripe-status"></div>
            </div>

            <!-- KPIs -->
            <div class="kpi-grid" id="kpis"></div>

            <!-- Orders Table -->
            <div class="card">
                <div class="card-title">Ordenes Recientes</div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Total</th>
                                <th>Status</th>
                                <th>Pagado</th>
                                <th>Metodo</th>
                                <th>Fecha Pago</th>
                                <th>Comision</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="orders-body"></tbody>
                    </table>
                </div>
                <p id="no-orders" style="display:none; text-align:center; padding:24px; color:#64748b;">
                    No hay ordenes registradas aun.
                </p>
            </div>

            <!-- Lookup -->
            <div class="card">
                <div class="card-title">Consultar Estado de Pago</div>
                <div class="lookup-row">
                    <input type="number" id="lookup-id" placeholder="ID de orden" min="1" />
                    <button class="btn btn-blue" onclick="lookupOrder()">Consultar</button>
                </div>
                <div class="lookup-result" id="lookup-result"></div>
            </div>
        </div>
    </div>

    <script>
        const STRIPE_CONFIGURED = STRIPE_FLAG_PLACEHOLDER;

        async function loadDashboard() {
            try {
                const res = await fetch('/pagos/api/resumen');
                if (!res.ok) throw new Error('Error ' + res.status);
                const data = await res.json();
                renderStripe();
                renderKPIs(data);
                renderOrders(data.ordenes);
            } catch (err) {
                console.error(err);
                document.getElementById('loading').innerHTML =
                    '<p style="color:#ef4444;">Error al cargar datos: ' + err.message + '</p>';
                return;
            }
            document.getElementById('loading').style.display = 'none';
            document.getElementById('content').style.display = 'block';
        }

        function renderStripe() {
            const el = document.getElementById('stripe-status');
            if (STRIPE_CONFIGURED) {
                el.innerHTML = '<div class="stripe-status stripe-active"><span class="status-dot green"></span> Stripe activo &mdash; Pagos con tarjeta habilitados</div>';
            } else {
                el.innerHTML = '<div class="stripe-status stripe-inactive"><span class="status-dot red"></span> Stripe NO configurado &mdash; Solo pagos simulados disponibles</div>';
            }
        }

        function renderKPIs(d) {
            document.getElementById('kpis').innerHTML = `
                <div class="kpi-card">
                    <div class="kpi-label">Ordenes Pagadas</div>
                    <div class="kpi-value green">${d.ordenes_pagadas} <span style="font-size:0.9rem;color:#64748b;">/ ${d.total_ordenes}</span></div>
                    <div class="kpi-sub">${d.total_ordenes ? Math.round(d.ordenes_pagadas / d.total_ordenes * 100) : 0}% completadas</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Total Cobrado</div>
                    <div class="kpi-value blue">$${Number(d.total_cobrado).toLocaleString('es-MX', {minimumFractionDigits:2})} <span style="font-size:0.8rem;color:#64748b;">MXN</span></div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Comisiones ObraYa (2%)</div>
                    <div class="kpi-value orange">$${Number(d.total_comisiones).toLocaleString('es-MX', {minimumFractionDigits:2})} <span style="font-size:0.8rem;color:#64748b;">MXN</span></div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Pendientes de Pago</div>
                    <div class="kpi-value ${d.ordenes_pendientes > 0 ? 'yellow' : 'green'}">${d.ordenes_pendientes}</div>
                    <div class="kpi-sub">${d.ordenes_pendientes > 0 ? 'Requieren atencion' : 'Todo al dia'}</div>
                </div>
            `;
        }

        function statusBadge(status) {
            const map = {
                'completada': 'badge-green',
                'pagada': 'badge-green',
                'pendiente': 'badge-yellow',
                'nueva': 'badge-blue',
                'cancelada': 'badge-red',
            };
            const cls = map[status] || 'badge-gray';
            return `<span class="badge ${cls}">${status || 'sin status'}</span>`;
        }

        function renderOrders(ordenes) {
            const tbody = document.getElementById('orders-body');
            if (!ordenes || ordenes.length === 0) {
                document.getElementById('no-orders').style.display = 'block';
                return;
            }
            tbody.innerHTML = ordenes.map(o => `
                <tr>
                    <td style="color:#f1f5f9;font-weight:600;">#${o.id}</td>
                    <td style="color:#f1f5f9;">$${o.total ? Number(o.total).toLocaleString('es-MX', {minimumFractionDigits:2}) : '0.00'}</td>
                    <td>${statusBadge(o.status)}</td>
                    <td>${o.pagado ? '<span class="check">&#10003;</span>' : '<span class="cross">&#10007;</span>'}</td>
                    <td>${o.metodo_pago || '<span style="color:#64748b;">—</span>'}</td>
                    <td>${o.fecha_pago ? new Date(o.fecha_pago).toLocaleDateString('es-MX') : '<span style="color:#64748b;">—</span>'}</td>
                    <td>${o.comision_obraya ? '$' + Number(o.comision_obraya).toFixed(2) : '—'}</td>
                    <td>
                        ${!o.pagado ? `
                            <button class="btn btn-orange btn-sm" onclick="simularPago(${o.id}, this)">Simular Pago</button>
                            <button class="btn btn-blue btn-sm" onclick="crearSesion(${o.id}, this)" style="margin-left:4px;">Stripe</button>
                        ` : '<span style="color:#64748b;font-size:0.75rem;">Completado</span>'}
                    </td>
                </tr>
            `).join('');
        }

        async function simularPago(id, btn) {
            btn.disabled = true;
            btn.textContent = '...';
            try {
                const res = await fetch('/pagos/simular/' + id, { method: 'POST' });
                const data = await res.json();
                if (data.ok) {
                    alert('Pago simulado exitosamente para orden #' + id);
                    loadDashboard();
                } else {
                    alert('Error: ' + (data.detail || 'No se pudo simular'));
                    btn.disabled = false;
                    btn.textContent = 'Simular Pago';
                }
            } catch (e) {
                alert('Error de red: ' + e.message);
                btn.disabled = false;
                btn.textContent = 'Simular Pago';
            }
        }

        async function crearSesion(id, btn) {
            btn.disabled = true;
            btn.textContent = '...';
            try {
                const res = await fetch('/pagos/crear-sesion/' + id, { method: 'POST' });
                const data = await res.json();
                if (data.ok && data.url) {
                    window.open(data.url, '_blank');
                } else {
                    alert('Error: ' + (data.detail || 'No se pudo crear sesion'));
                }
            } catch (e) {
                alert('Error de red: ' + e.message);
            }
            btn.disabled = false;
            btn.textContent = 'Stripe';
        }

        async function lookupOrder() {
            const id = document.getElementById('lookup-id').value;
            const resultEl = document.getElementById('lookup-result');
            if (!id) { resultEl.innerHTML = '<p style="color:#ef4444;">Ingresa un ID de orden.</p>'; return; }
            resultEl.innerHTML = '<p>Consultando...</p>';
            try {
                const res = await fetch('/pagos/estado/' + id);
                if (!res.ok) {
                    const err = await res.json();
                    resultEl.innerHTML = '<p style="color:#ef4444;">Error: ' + (err.detail || res.status) + '</p>';
                    return;
                }
                const data = await res.json();
                resultEl.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (e) {
                resultEl.innerHTML = '<p style="color:#ef4444;">Error de red: ' + e.message + '</p>';
            }
        }

        // Enter key in lookup input
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('lookup-id').addEventListener('keydown', e => {
                if (e.key === 'Enter') lookupOrder();
            });
            loadDashboard();
        });
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def pagos_dashboard():
    """Dashboard principal del sistema de pagos."""
    stripe_configured = bool(settings.STRIPE_SECRET_KEY)
    html = PAGOS_HTML.replace(
        "STRIPE_FLAG_PLACEHOLDER",
        "true" if stripe_configured else "false",
    )
    return HTMLResponse(content=html)
