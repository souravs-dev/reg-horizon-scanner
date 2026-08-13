# Regulatory Horizon Scanner

A small service that watches UK financial regulator feeds (FCA, Bank of England PRA),
detects when a published item actually changes, and asks an LLM to pull out concrete
compliance obligations — always tied back to the source URL they came from.

## How it works

```
RSS feeds (FCA, PRA, BoE)
      │  httpx + feedparser
      ▼
normalize into Clause records
      │  sha256(title, content, url)  ──►  content_hash
      ▼
diff against last-seen hash in Postgres
      │  unchanged → skip
      │  new / changed →
      ▼
Claude extracts structured obligations
      │  {obligation, applies_to, deadline}
      ▼
persist Obligation rows (source_url = clause url, i.e. a citation on every row)
      │
      ▼
emit a "changed obligation" ChangeEvent (logged, optionally POSTed to a webhook)
```

Change detection is why this exists at all: regulator feeds mostly republish things
you've already seen, and LLM calls aren't free. Only a genuinely new or edited item
triggers extraction.

## Stack

- **FastAPI** — HTTP API
- **SQLAlchemy 2.0 (async)** — Postgres in prod, SQLite in tests
- **Pydantic** — the `{obligation, applies_to, deadline}` extraction schema, enforced via
  Claude tool-use so the model can't return free-form text
- **APScheduler (asyncio)** — periodic re-scan, no separate broker/worker process needed
  at this scale. (Swap for Celery + Redis if you need scanning distributed across workers.)

## Running it

```bash
docker compose up -d          # Postgres on localhost:5432
cp .env.example .env          # fill in ANTHROPIC_API_KEY
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Then:

```bash
curl -X POST http://localhost:8000/scan        # trigger a scan cycle now
curl http://localhost:8000/obligations          # extracted obligations, newest first
curl http://localhost:8000/events               # change events
curl http://localhost:8000/clauses?source="FCA News"
```

A background job also re-scans every `SCAN_INTERVAL_MINUTES` (default 60).

## Sources

Configured in `app/config.py`:

- FCA News (`fca.org.uk/news/rss.xml`)
- Bank of England — Prudential Regulation publications
- Bank of England — News

Add more by appending `{"name": ..., "url": ...}` to `SOURCES` — any RSS 2.0 feed works.

## Tests

```bash
pytest -q
```

Feed parsing and change-detection are tested against a fixture feed with `respx`-mocked
HTTP and a fake LLM extractor — no network or API key required. Run `ruff check .` for
lint.

## What's intentionally left out

This is a weekend-scope build, not a production regulatory-compliance system:

- No Alembic migrations — schema is created via `create_all` on startup.
- No auth on the API.
- No retry/backoff on feed fetch failures beyond "log and skip this source for this cycle".
- Obligation history is append-only per clause (a changed clause's old obligations aren't
  deleted), which is a reasonable default for an audit trail but means `/obligations` can
  show superseded entries for actively-changing clauses.
