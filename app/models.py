import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class Clause(Base):
    """A single normalized item pulled from a regulator feed."""

    __tablename__ = "clauses"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_clause_source_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(Text)
    external_id: Mapped[str] = mapped_column(Text)  # feed entry guid or link
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(Text, index=True)
    published_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    obligations: Mapped[list["Obligation"]] = relationship(back_populates="clause")


class Obligation(Base):
    """A structured obligation extracted by the LLM from a clause."""

    __tablename__ = "obligations"

    id: Mapped[int] = mapped_column(primary_key=True)
    clause_id: Mapped[int] = mapped_column(ForeignKey("clauses.id"))
    obligation: Mapped[str] = mapped_column(Text)
    applies_to: Mapped[str] = mapped_column(Text)
    deadline: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    extracted_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    clause: Mapped["Clause"] = relationship(back_populates="obligations")


class ChangeEvent(Base):
    """An emitted 'changed obligation' event, one per clause content-hash change."""

    __tablename__ = "change_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    clause_id: Mapped[int] = mapped_column(ForeignKey("clauses.id"))
    event_type: Mapped[str] = mapped_column(Text)  # "new_clause" | "changed_clause"
    obligation_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
