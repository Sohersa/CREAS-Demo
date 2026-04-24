from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .modules.assets.router import router as assets_router
from .modules.telemetry.router import router as telemetry_router
from .modules.work_orders.router import router as wo_router
from .modules.simulation.router import router as sim_router
from .modules.copilot.router import router as copilot_router
from .adapters.sap_mock import router as sap_router
from .adapters.maximo_mock import router as maximo_router

app = FastAPI(title="AXIS · Digital Twin Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets_router, prefix="/api/v1/assets", tags=["assets"])
app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["telemetry"])
app.include_router(wo_router, prefix="/api/v1/work-orders", tags=["work_orders"])
app.include_router(sim_router, prefix="/api/v1/simulation", tags=["simulation"])
app.include_router(copilot_router, prefix="/api/v1/copilot", tags=["copilot"])
app.include_router(sap_router, prefix="/mocks/sap", tags=["sap_mock"])
app.include_router(maximo_router, prefix="/mocks/maximo", tags=["maximo_mock"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "axis"}
