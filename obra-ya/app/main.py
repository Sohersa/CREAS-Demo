"""
ObraYa — App principal FastAPI.
Agente de IA para cotizacion de materiales de construccion en Guadalajara.
"""
import logging
from collections import deque
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import crear_tablas
from app.routers import webhook, admin, simulador, landing, portal, portal_api, dashboard, pagos, presupuesto, aprobaciones, credito, auth, hub, precios
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


@app.on_event("startup")
async def startup():
    """Se ejecuta al iniciar el servidor."""
    logging.info("Iniciando ObraYa...")
    crear_tablas()
    logging.info("Base de datos lista.")
    sembrar_datos_demo()
    await iniciar_scheduler()


@app.get("/health")
def health():
    """Health check para monitoreo — Railway, uptime bots, etc."""
    from app.database import SessionLocal
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "error",
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
