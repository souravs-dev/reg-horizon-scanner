import logging

import httpx

from app.config import settings

logger = logging.getLogger("reg_scanner.events")


async def emit_change_event(event_type: str, clause_title: str, clause_url: str, obligation_count: int) -> None:
    logger.info(
        "changed_obligation event=%s title=%r url=%s obligations=%d",
        event_type,
        clause_title,
        clause_url,
        obligation_count,
    )
    if not settings.event_webhook_url:
        return
    payload = {
        "event_type": event_type,
        "title": clause_title,
        "url": clause_url,
        "obligation_count": obligation_count,
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(settings.event_webhook_url, json=payload, timeout=10.0)
    except httpx.HTTPError:
        logger.exception("Failed to deliver change event webhook")
