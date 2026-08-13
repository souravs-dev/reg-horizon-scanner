from pathlib import Path

from app.feeds import parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "sample_feed.xml"


def test_parse_feed_normalizes_entries():
    raw = FIXTURE.read_bytes()
    clauses = parse_feed("Test Regulator", raw)

    assert len(clauses) == 2
    first = clauses[0]
    assert first.source == "Test Regulator"
    assert first.external_id == "guid-consumer-duty-1"
    assert first.title == "New consumer duty guidance published"
    assert first.url == "https://example.com/news/consumer-duty-guidance"
    assert "consumer duty rules" in first.content
    assert first.published_at is not None and first.published_at.startswith("2026-01-01")
