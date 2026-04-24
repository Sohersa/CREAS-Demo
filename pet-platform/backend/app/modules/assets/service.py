"""Asset service — backed by Postgres via SQLAlchemy (scaffold)."""
from datetime import datetime, UTC
from uuid import UUID, uuid4
from .schema import Asset, Position, Geometry, MaintenanceAttrs

# In-memory demo store. Replace with real SQLAlchemy session + asset_repo.
_STORE: dict[UUID, Asset] = {}


async def list_assets(cls: str | None = None, area: str | None = None, limit: int = 500) -> list[Asset]:
    out = list(_STORE.values())
    if cls:
        out = [a for a in out if a.cls == cls]
    return out[:limit]


async def get_asset(asset_id: UUID) -> Asset | None:
    return _STORE.get(asset_id)


async def upsert_asset(a: Asset) -> Asset:
    a.updated_at = datetime.now(UTC)
    _STORE[a.id] = a
    return a


def seed_demo():
    """Idempotent seed with 3 demo assets so the scaffold runs out-of-the-box."""
    if _STORE:
        return
    for tag, cls, x, z in [
        ("BL-B02-SIDEL-SBO24", "Blower", -8.0, -6.0),
        ("FI-F01-KRONES", "Filler", 8.0, -10.0),
        ("AC-HP01-ATLAS", "Compressor", -8.0, -24.0),
    ]:
        a = Asset(
            id=uuid4(), tag=tag, name=tag, cls=cls,
            geometry=Geometry(mesh_uri=f"s3://axis/models/{tag}.glb", bbox=(0, 0, 0, 4, 4, 4)),
            position=Position(x=x, y=0, z=z),
            maintenance=MaintenanceAttrs(criticality="A"),
            updated_at=datetime.now(UTC),
        )
        _STORE[a.id] = a


seed_demo()
