"""Mock IBM Maximo MIF endpoints — wire to real Maximo by swapping base URL."""
from fastapi import APIRouter
from ..modules.work_orders.router import WorkOrder
from uuid import uuid4

router = APIRouter()

_WOS: list[WorkOrder] = [
    WorkOrder(id="WO-45213", priority="high",
              description="Cambio preform cavidad #5 — desgaste detectado",
              assigned_to="J. Rangel", due="hoy 22:00", source="maximo"),
    WorkOrder(id="WO-45180", priority="normal",
              description="PM mensual — lubricación rodamientos",
              assigned_to="M. Saenz", due="Vie 21/04"),
    WorkOrder(id="WO-45201", priority="high",
              description="Reemplazo filtro aceite separador",
              assigned_to="M. Saenz", due="mañana"),
]


def list_fixture_wos() -> list[WorkOrder]:
    return _WOS


def push_fixture_wo(wo: WorkOrder) -> WorkOrder:
    if wo.id.startswith("NEW"):
        wo.id = f"WO-{45300 + len(_WOS)}"
    _WOS.append(wo)
    return wo


@router.get("/mxwo")
async def mxwo_list(limit: int = 50):
    return {"member": [w.model_dump() for w in _WOS[:limit]]}


@router.get("/mxasset/{asset_id}")
async def mxasset(asset_id: str):
    return {
        "assetnum": asset_id,
        "description": f"Asset {asset_id}",
        "status": "OPERATING",
        "location": "L2-LINE-PET",
        "priority": 1,
        "wo_count": sum(1 for w in _WOS if asset_id in (w.asset_id and str(w.asset_id) or "")),
    }
