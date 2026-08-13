import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.db import SessionLocal
from app.scanner import scan_all

logger = logging.getLogger("reg_scanner.scheduler")

scheduler = AsyncIOScheduler()


async def run_scheduled_scan() -> None:
    async with SessionLocal() as session:
        summary = await scan_all(session)
        logger.info("Scheduled scan complete: %s", summary.model_dump())


def start_scheduler() -> None:
    scheduler.add_job(
        run_scheduled_scan,
        "interval",
        minutes=settings.scan_interval_minutes,
        id="regulatory_scan",
    )
    scheduler.start()
