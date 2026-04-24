"""Copilot — RAG over docs + assets graph + last 24h telemetry, tool-calling via Claude."""
import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AskReq(BaseModel):
    question: str
    asset_context: str | None = None
    session_id: str | None = None


class Citation(BaseModel):
    kind: str  # "asset" | "wo" | "doc" | "sensor"
    ref: str


class AskResp(BaseModel):
    answer: str
    citations: list[Citation] = []


@router.post("/ask", response_model=AskResp)
async def ask(req: AskReq):
    """Uses Anthropic Claude with tool-calling: query_telemetry, get_wos, search_docs.

    Skeleton-only — requires ANTHROPIC_API_KEY and real retrievers wired to
    pgvector (docs), TimescaleDB (telemetry), Postgres AGE (asset graph).
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        return AskResp(
            answer=(
                "Copilot no configurado: define ANTHROPIC_API_KEY. "
                "En producción respondería con RAG sobre docs + telemetry + WOs."
            )
        )
    # Real implementation (outline):
    # 1. classify intent (diagnose | query | forecast | action)
    # 2. retrieve: pgvector docs + asset subgraph + last 24h of primary sensors
    # 3. call Claude with tools = [query_telemetry, get_wos, get_asset, search_docs]
    # 4. normalize response with citations
    return AskResp(answer="[scaffold]", citations=[])
