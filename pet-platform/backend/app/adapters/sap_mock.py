"""Mock SAP S/4HANA endpoints mirroring OData structure — swap URL to real SAP to go live."""
from fastapi import APIRouter

router = APIRouter()

_COSTS = {
    "MX-50023": {"asset": "BL-B02-SIDEL-SBO24", "ytd_usd": 128_400, "plan_usd": 185_000},
    "MX-50024": {"asset": "FI-F01-KRONES",     "ytd_usd": 84_900,  "plan_usd": 140_000},
    "MX-50025": {"asset": "AC-HP01-ATLAS",     "ytd_usd": 36_200,  "plan_usd": 55_000},
}


@router.get("/CostCenter('{cc}')")
async def cost_center(cc: str):
    data = _COSTS.get(cc)
    if not data:
        return {"error": "not_found"}
    return {"CostCenter": cc, **data, "Currency": "USD", "Source": "SAP CO · mock"}


@router.get("/PurchaseOrder")
async def purchase_orders(asset: str | None = None, limit: int = 20):
    return {"PurchaseOrders": [
        {"id": f"PO-{4000 + i}", "asset": asset or "BL-B02", "amount_usd": 1200 + i * 87,
         "vendor": "Sidel México", "status": ["released", "invoiced"][i % 2]}
        for i in range(limit)
    ]}
