import asyncio
from dataclasses import dataclass

import feedparser
import httpx


@dataclass
class NormalizedClause:
    source: str
    external_id: str
    title: str
    url: str
    content: str
    published_at: str | None  # ISO 8601 string, or None if the feed didn't provide one


def parse_feed(source: str, raw: bytes) -> list[NormalizedClause]:
    parsed = feedparser.parse(raw)
    clauses = []
    for entry in parsed.entries:
        external_id = entry.get("id") or entry.get("link") or entry.get("title", "")
        title = entry.get("title", "").strip()
        url = entry.get("link", "")
        content = (entry.get("summary") or entry.get("description") or "").strip()
        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = _struct_time_to_iso(entry.published_parsed)
        clauses.append(
            NormalizedClause(
                source=source,
                external_id=external_id,
                title=title,
                url=url,
                content=content,
                published_at=published_at,
            )
        )
    return clauses


def _struct_time_to_iso(struct_time) -> str:
    import datetime

    return datetime.datetime(*struct_time[:6], tzinfo=datetime.UTC).isoformat()


async def fetch_feed(client: httpx.AsyncClient, name: str, url: str) -> list[NormalizedClause]:
    response = await client.get(url, timeout=20.0)
    response.raise_for_status()
    return await asyncio.to_thread(parse_feed, name, response.content)
