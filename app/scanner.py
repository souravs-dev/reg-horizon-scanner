import datetime
import logging
from collections.abc import Awaitable, Callable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SOURCES
from app.events import emit_change_event
from app.feeds import NormalizedClause, fetch_feed
from app.hashing import content_hash
from app.llm import extract_obligations
from app.models import ChangeEvent, Clause, Obligation
from app.schemas import ExtractionResult, ScanSummary

logger = logging.getLogger("reg_scanner.scanner")

ExtractFn = Callable[[str, str], Awaitable[ExtractionResult]]


async def _process_clause(
    session: AsyncSession, normalized: NormalizedClause, extract_fn: ExtractFn
) -> tuple[str | None, int]:
    """Diff one normalized clause against the DB. Returns (event_type, obligations_extracted)."""
    new_hash = content_hash(normalized.title, normalized.content, normalized.url)

    existing = await session.scalar(
        select(Clause).where(
            Clause.source == normalized.source, Clause.external_id == normalized.external_id
        )
    )

    published_at = (
        datetime.datetime.fromisoformat(normalized.published_at) if normalized.published_at else None
    )

    if existing is None:
        event_type = "new_clause"
        clause = Clause(
            source=normalized.source,
            external_id=normalized.external_id,
            title=normalized.title,
            url=normalized.url,
            content=normalized.content,
            content_hash=new_hash,
            published_at=published_at,
        )
        session.add(clause)
        await session.flush()
    elif existing.content_hash != new_hash:
        event_type = "changed_clause"
        existing.title = normalized.title
        existing.content = normalized.content
        existing.content_hash = new_hash
        existing.published_at = published_at
        clause = existing
    else:
        return None, 0

    result = await extract_fn(clause.title, clause.content)
    for item in result.obligations:
        session.add(
            Obligation(
                clause_id=clause.id,
                obligation=item.obligation,
                applies_to=item.applies_to,
                deadline=item.deadline,
                source_url=clause.url,
            )
        )
    session.add(
        ChangeEvent(clause_id=clause.id, event_type=event_type, obligation_count=len(result.obligations))
    )
    await emit_change_event(event_type, clause.title, clause.url, len(result.obligations))
    return event_type, len(result.obligations)


async def scan_all(session: AsyncSession, extract_fn: ExtractFn = extract_obligations) -> ScanSummary:
    summary = ScanSummary(
        sources_scanned=0, clauses_seen=0, new_clauses=0, changed_clauses=0, obligations_extracted=0
    )
    async with httpx.AsyncClient() as client:
        for source in SOURCES:
            try:
                clauses = await fetch_feed(client, source["name"], source["url"])
            except httpx.HTTPError:
                logger.exception("Failed to fetch feed %s", source["name"])
                continue
            summary.sources_scanned += 1
            for normalized in clauses:
                summary.clauses_seen += 1
                event_type, obligation_count = await _process_clause(session, normalized, extract_fn)
                if event_type == "new_clause":
                    summary.new_clauses += 1
                elif event_type == "changed_clause":
                    summary.changed_clauses += 1
                summary.obligations_extracted += obligation_count
    await session.commit()
    return summary
