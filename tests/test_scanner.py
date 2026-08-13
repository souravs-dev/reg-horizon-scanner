from pathlib import Path

import httpx
import respx

from app.config import SOURCES
from app.scanner import scan_all
from app.schemas import ExtractedObligation, ExtractionResult

FIXTURE = Path(__file__).parent / "fixtures" / "sample_feed.xml"
FEED_XML = FIXTURE.read_bytes()
FEED_XML_CHANGED = FEED_XML.replace(
    b"Firms must implement the new consumer duty rules by 31 December 2026.",
    b"Firms must implement the new consumer duty rules by 30 June 2027 (deadline extended).",
)


async def fake_extract(title: str, content: str) -> ExtractionResult:
    if "consumer duty" not in title.lower():
        return ExtractionResult(obligations=[])
    return ExtractionResult(
        obligations=[
            ExtractedObligation(
                obligation="Implement the new consumer duty rules",
                applies_to="UK-authorised firms",
                deadline="2026-12-31",
            )
        ]
    )


def _mock_all_sources(content: bytes) -> None:
    for source in SOURCES:
        respx.get(source["url"]).mock(return_value=httpx.Response(200, content=content))


@respx.mock
async def test_scan_detects_new_clauses(session):
    _mock_all_sources(FEED_XML)

    summary = await scan_all(session, extract_fn=fake_extract)

    assert summary.sources_scanned == len(SOURCES)
    assert summary.new_clauses == 2 * len(SOURCES)  # 2 items per feed
    assert summary.changed_clauses == 0
    assert summary.obligations_extracted == len(SOURCES)  # only 1 of 2 items yields an obligation


@respx.mock
async def test_rescan_with_unchanged_feed_is_a_noop(session):
    _mock_all_sources(FEED_XML)
    await scan_all(session, extract_fn=fake_extract)

    _mock_all_sources(FEED_XML)
    summary = await scan_all(session, extract_fn=fake_extract)

    assert summary.new_clauses == 0
    assert summary.changed_clauses == 0
    assert summary.obligations_extracted == 0


@respx.mock
async def test_rescan_with_edited_clause_is_detected_as_changed(session):
    _mock_all_sources(FEED_XML)
    await scan_all(session, extract_fn=fake_extract)

    _mock_all_sources(FEED_XML_CHANGED)
    summary = await scan_all(session, extract_fn=fake_extract)

    assert summary.new_clauses == 0
    assert summary.changed_clauses == len(SOURCES)
    assert summary.obligations_extracted == len(SOURCES)
