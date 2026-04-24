from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()


class WorkOrder(BaseModel):
    id: str
    asset_id: UUID | None = None
    priority: str = "normal"
    description: str
    assigned_to: str | None = None
    due: str | None = None
    source: str = "maximo"
    status: str = "open"


@router.get("", response_model=list[WorkOrder])
async def list_wos(asset_id: UUID | None = None, status: str | None = None):
    # proxy to Maximo adapter; currently returns mock fixture
    from ...adapters.maximo_mock import list_fixture_wos
    return [w for w in list_fixture_wos() if (not asset_id or w.asset_id == asset_id)]


@router.post("", response_model=WorkOrder)
async def create_wo(wo: WorkOrder):
    from ...adapters.maximo_mock import push_fixture_wo
    return push_fixture_wo(wo)
