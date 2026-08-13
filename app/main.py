from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SOURCES
from app.db import get_session, init_db
from app.models import ChangeEvent, Clause, Obligation
from app.scanner import scan_all
from app.scheduler import start_scheduler
from app.schemas import ChangeEventOut, ClauseOut, ObligationOut, ScanSummary


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield


app = FastAPI(title="Regulatory Horizon Scanner", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/sources")
async def sources() -> list[dict]:
    return SOURCES


@app.post("/scan", response_model=ScanSummary)
async def trigger_scan(session: AsyncSession = Depends(get_session)) -> ScanSummary:
    return await scan_all(session)


@app.get("/clauses", response_model=list[ClauseOut])
async def list_clauses(
    source: str | None = None, limit: int = 50, session: AsyncSession = Depends(get_session)
) -> list[Clause]:
    query = select(Clause).order_by(Clause.fetched_at.desc()).limit(limit)
    if source:
        query = query.where(Clause.source == source)
    return list(await session.scalars(query))


@app.get("/obligations", response_model=list[ObligationOut])
async def list_obligations(
    applies_to: str | None = None, limit: int = 50, session: AsyncSession = Depends(get_session)
) -> list[Obligation]:
    query = select(Obligation).order_by(Obligation.extracted_at.desc()).limit(limit)
    if applies_to:
        query = query.where(Obligation.applies_to.ilike(f"%{applies_to}%"))
    return list(await session.scalars(query))


@app.get("/events", response_model=list[ChangeEventOut])
async def list_events(limit: int = 50, session: AsyncSession = Depends(get_session)) -> list[ChangeEvent]:
    query = select(ChangeEvent).order_by(ChangeEvent.created_at.desc()).limit(limit)
    return list(await session.scalars(query))
