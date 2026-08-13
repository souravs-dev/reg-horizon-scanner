import datetime

from pydantic import BaseModel, Field


class ExtractedObligation(BaseModel):
    obligation: str = Field(description="The specific obligation or requirement being imposed")
    applies_to: str = Field(description="Who the obligation applies to, e.g. 'UK-authorised payment firms'")
    deadline: str | None = Field(default=None, description="Compliance deadline if stated, else null")


class ExtractionResult(BaseModel):
    obligations: list[ExtractedObligation]


class ObligationOut(BaseModel):
    id: int
    obligation: str
    applies_to: str
    deadline: str | None
    source_url: str
    extracted_at: datetime.datetime

    model_config = {"from_attributes": True}


class ClauseOut(BaseModel):
    id: int
    source: str
    title: str
    url: str
    content_hash: str
    published_at: datetime.datetime | None
    fetched_at: datetime.datetime

    model_config = {"from_attributes": True}


class ChangeEventOut(BaseModel):
    id: int
    clause_id: int
    event_type: str
    obligation_count: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ScanSummary(BaseModel):
    sources_scanned: int
    clauses_seen: int
    new_clauses: int
    changed_clauses: int
    obligations_extracted: int
