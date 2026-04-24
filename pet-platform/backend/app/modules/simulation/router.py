"""What-if simulation — SimPy runs in a thread/process pool, returns a scenario id + KPIs."""
import asyncio
import random
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

_SCENARIOS: dict[str, dict] = {}


class ScenarioParams(BaseModel):
    horizon_hours: int = 24
    capacity_multiplier: float = 1.0
    sku_mix: dict[str, float] | None = None
    availability_overrides: dict[str, float] | None = None


@router.post("/run")
async def run(params: ScenarioParams, bg: BackgroundTasks):
    sid = str(uuid4())
    _SCENARIOS[sid] = {"status": "queued", "params": params.model_dump()}
    bg.add_task(_execute, sid, params)
    return {"scenario_id": sid, "status": "queued"}


@router.get("/{sid}")
async def get_scenario(sid: str):
    return _SCENARIOS.get(sid, {"status": "unknown"})


async def _execute(sid: str, p: ScenarioParams):
    """Lightweight SimPy-style stub — real impl launches SimPy kernel in process pool."""
    _SCENARIOS[sid]["status"] = "running"
    await asyncio.sleep(2.0)
    baseline_oee = 81.4
    delta = (p.capacity_multiplier - 1.0) * 60.0 + random.uniform(-0.4, 0.4)
    throughput = int(24810 * p.capacity_multiplier * (1 + random.uniform(-0.01, 0.01)))
    bottleneck = "FI-F01" if p.capacity_multiplier > 1.01 else "BL-B02"
    _SCENARIOS[sid] |= {
        "status": "completed",
        "oee_projected": round(baseline_oee + delta, 2),
        "throughput_bph": throughput,
        "bottleneck": bottleneck,
        "utilization": round(min(99.8, 86 + delta * 4), 1),
    }
