from fastapi import APIRouter, HTTPException
from uuid import UUID
from .schema import Asset
from .service import list_assets, get_asset, upsert_asset

router = APIRouter()


@router.get("", response_model=list[Asset])
async def get_assets(cls: str | None = None, area: str | None = None, limit: int = 500):
    return await list_assets(cls=cls, area=area, limit=limit)


@router.get("/{asset_id}", response_model=Asset)
async def get_single(asset_id: UUID):
    a = await get_asset(asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    return a


@router.put("/{asset_id}", response_model=Asset)
async def put_asset(asset_id: UUID, asset: Asset):
    if asset.id != asset_id:
        raise HTTPException(400, "id mismatch")
    return await upsert_asset(asset)
