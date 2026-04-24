"""Telemetry module — TimescaleDB hypertable + WebSocket live stream."""
import asyncio
import json
import random
from datetime import datetime, UTC
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Demo tags emulating PET plant sensors
DEMO_TAGS = [
    ("BL-B02.PT-201", "pressure_hp", "bar", 39.0, 0.6),
    ("BL-B02.TI-115", "heater_temp", "degC", 112.0, 3.0),
    ("FI-F01.FQI-01", "speed", "bph", 26100.0, 180.0),
    ("AC-HP01.VT-01", "vibration", "mm/s", 2.8, 0.4),
    ("CH-01.TI-SUP", "supply_temp", "degC", 7.2, 0.2),
]


@router.get("/tags")
async def list_tags():
    return [{"tag": t, "kind": k, "unit": u} for t, k, u, *_ in DEMO_TAGS]


@router.get("/query")
async def query(tag: str, minutes: int = 60):
    """Return downsampled history for the last N minutes (demo = synthetic)."""
    now = datetime.now(UTC)
    base = next((d for d in DEMO_TAGS if d[0] == tag), None)
    if not base:
        return {"tag": tag, "points": []}
    _, _, unit, v0, sigma = base
    pts = [
        {"t": (now.timestamp() - 60 * (minutes - i)) * 1000, "v": v0 + random.gauss(0, sigma)}
        for i in range(minutes)
    ]
    return {"tag": tag, "unit": unit, "points": pts}


@router.websocket("/stream")
async def stream(ws: WebSocket):
    """Multiplexed live telemetry stream — consumer sends {subscribe:[tags]} first."""
    await ws.accept()
    subs: set[str] = {t[0] for t in DEMO_TAGS}
    try:
        while True:
            for tag, kind, unit, v, sigma in DEMO_TAGS:
                if tag not in subs:
                    continue
                await ws.send_text(json.dumps({
                    "tag": tag, "kind": kind, "unit": unit,
                    "t": datetime.now(UTC).isoformat(),
                    "v": round(v + random.gauss(0, sigma), 3),
                }))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return
