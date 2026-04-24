"""
ObraYa — App principal FastAPI.
Agente de IA para cotizacion de materiales de construccion en Guadalajara.
"""
import logging
from collections import deque
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import crear_tablas
from app.routers import webhook, admin, simulador, landing, portal, portal_api, dashboard, pagos, presupuesto, aprobaciones, credito, auth, hub, precios, dashboard_v2, demo
from app.services.scheduler import iniciar_scheduler
from app.services.seed_demo import sembrar_datos_demo

# Rate limiter global
limiter = Limiter(key_func=get_remote_address)

# Buffer de logs en memoria (ultimos 200 mensajes)
log_buffer = deque(maxlen=200)


class BufferHandler(logging.Handler):
    def emit(self, record):
        log_buffer.append(self.format(record))


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
buffer_handler = BufferHandler()
buffer_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.getLogger().addHandler(buffer_handler)

# Crear app
app = FastAPI(
    title="ObraYa",
    description="Agente de IA para cotizacion de materiales de construccion",
    version="0.1.0",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (para el panel admin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir el design bundle de Claude Design (Landing + Playground + componentes)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Mount adicional: Landing.html usa paths relativos como "design/tokens.css"
# que desde / se resuelven a "/design/tokens.css". Servimos esa ruta.
_design_inner = _static_dir / "design" / "design"
if _design_inner.exists():
    app.mount("/design", StaticFiles(directory=str(_design_inner)), name="design_assets")


@app.get("/landing")
def serve_landing():
    """Landing principal — design system de Claude Design."""
    f = _static_dir / "design" / "Landing.html"
    if f.exists():
        return FileResponse(str(f))
    return JSONResponse({"error": "Landing not found"}, status_code=404)


@app.get("/playground")
@app.get("/Playground.html")
def serve_playground():
    """Playground interactivo — visualiza el flujo end-to-end."""
    f = _static_dir / "design" / "Playground.html"
    if f.exists():
        return FileResponse(str(f))
    return JSONResponse({"error": "Playground not found"}, status_code=404)


@app.get("/Landing.html")
def serve_landing_explicit():
    """El iframe puede pedir Landing.html explicitamente."""
    f = _static_dir / "design" / "Landing.html"
    if f.exists():
        return FileResponse(str(f))
    return JSONResponse({"error": "Landing not found"}, status_code=404)


@app.get("/probar")
@app.get("/Probar.html")
def serve_probar():
    """Pagina interactiva que simula el flujo completo de cotizacion."""
    f = _static_dir / "design" / "Probar.html"
    if f.exists():
        return FileResponse(str(f))
    return RedirectResponse(url="/", status_code=307)


# Rutas mock del Landing — redirigen a las paginas reales del portal
from fastapi.responses import RedirectResponse


@app.get("/residente")
@app.get("/residente/{path:path}")
def ir_portal_residente(path: str = ""):
    """URLs del Landing mockup que van al portal real de residente."""
    return RedirectResponse(url="/portal", status_code=307)


@app.get("/proveedor")
@app.get("/proveedor/{path:path}")
def ir_portal_proveedor(path: str = ""):
    """URLs del Landing mockup que van al portal real de proveedor."""
    return RedirectResponse(url="/portal", status_code=307)


@app.get("/ops")
@app.get("/ops/{path:path}")
def ir_admin_ops(path: str = ""):
    """URLs del Landing mockup que van al admin/dashboard."""
    return RedirectResponse(url="/dashboard", status_code=307)


@app.get("/demo")
def ir_demo():
    """Atajo a la demo interactiva."""
    return RedirectResponse(url="/playground", status_code=307)


@app.get("/app")
@app.get("/app/{path:path}")
def ir_app(path: str = ""):
    """Atajo: app.obraya.mx -> portal."""
    return RedirectResponse(url="/portal", status_code=307)


# 404 handler — en vez de JSON feo, redirige al Landing
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Cualquier 404 redirige al Landing (excepto rutas API)."""
    path = request.url.path
    if path.startswith("/api/") or path.startswith("/admin/api/") or path.startswith("/webhook/"):
        # APIs sí devuelven JSON 404
        return JSONResponse({"detail": "Not Found", "path": path}, status_code=404)
    # Rutas web → Landing
    return RedirectResponse(url="/", status_code=307)

# Registrar routers — landing va al final para que "/" no sobreescriba otros
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(admin.router)
app.include_router(simulador.router)
app.include_router(portal.router)
app.include_router(portal_api.router)
app.include_router(dashboard.router)
app.include_router(pagos.router)
app.include_router(presupuesto.router)
app.include_router(aprobaciones.router)
app.include_router(landing.router)
app.include_router(credito.router)
app.include_router(precios.router)
app.include_router(hub.router)
app.include_router(dashboard_v2.router)
app.include_router(demo.router)


@app.on_event("startup")
async def startup():
    """Se ejecuta al iniciar el servidor."""
    logging.info("Iniciando ObraYa...")
    crear_tablas()
    logging.info("Base de datos lista.")
    sembrar_datos_demo()
    await iniciar_scheduler()

    # Validar WhatsApp en background (no bloquea startup)
    async def _validar_whatsapp_bg():
        try:
            from app.services.whatsapp_health import verificar_whatsapp
            wa = await verificar_whatsapp()
            if wa["ok"]:
                det = wa.get("detalles", {})
                logging.info(
                    f"WhatsApp OK — {det.get('phone_number', '?')} "
                    f"({det.get('verified_name', '?')}) quality={det.get('quality_rating', '?')}"
                )
            else:
                logging.warning(f"WhatsApp status: {wa['status']} — {wa.get('mensaje', '')}")
        except Exception as e:
            logging.warning(f"No se pudo validar estado de WhatsApp: {e}")

    import asyncio
    asyncio.create_task(_validar_whatsapp_bg())


@app.get("/health")
def health():
    """
    Health check rapido para Railway — SOLO verifica que el proceso este up.
    No hace llamadas externas. El healthcheck completo esta en /health/full.
    """
    return {"status": "ok", "version": "0.3.0"}


@app.get("/health/full")
async def health_full():
    """
    Health check completo — BD + WhatsApp.
    NO usar para healthchecks de Railway (hace llamadas externas con latency).
    """
    from app.database import SessionLocal
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False

    # WhatsApp health (valida token contra Meta en vivo)
    whatsapp_status = "not_checked"
    try:
        from app.services.whatsapp_health import verificar_whatsapp
        wa = await verificar_whatsapp()
        whatsapp_status = wa["status"]
    except Exception:
        whatsapp_status = "check_failed"

    overall = "ok"
    if not db_ok:
        overall = "degraded"
    elif whatsapp_status not in ("healthy", "not_checked"):
        overall = "degraded"

    return {
        "status": overall,
        "db": "connected" if db_ok else "error",
        "whatsapp": whatsapp_status,
        "version": "0.2.0",
    }


@app.get("/admin/api/logs")
def get_logs(n: int = 50):
    """Ultimos N logs del servidor (en memoria)."""
    entries = list(log_buffer)
    return {"total": len(entries), "logs": entries[-n:]}


@app.get("/privacy")
def privacy():
    """Politica de privacidad requerida por Meta."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>ObraYa - Politica de Privacidad</title></head>
<body style="font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px">
<h1>Politica de Privacidad - ObraYa</h1>
<p>Ultima actualizacion: Abril 2026</p>
<h2>Datos que recopilamos</h2>
<p>ObraYa recopila tu numero de telefono y mensajes de WhatsApp unicamente para procesar
tus solicitudes de cotizacion de materiales de construccion.</p>
<h2>Uso de datos</h2>
<p>Tus datos se usan exclusivamente para: generar cotizaciones, contactar proveedores
en tu nombre, y enviarte comparativas de precios.</p>
<h2>Almacenamiento</h2>
<p>Los datos se almacenan de forma segura y no se comparten con terceros
mas alla de los proveedores necesarios para tu cotizacion.</p>
<h2>Contacto</h2>
<p>Para dudas sobre privacidad: gerencia@gruposohersa.com</p>
</body>
</html>""")
