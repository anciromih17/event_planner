from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Event(Base):
    """One logical public performance. Same performance from two sources is merged."""

    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("canonical_key", name="uq_event_canonical_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_key: Mapped[str] = mapped_column(String(500), index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    event_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(1500))
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # A technician can only mark a currently conflicting appointment as resolved.
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EventAudit(Base):
    """Immutable record of event additions and source-confirmed removals."""

    __tablename__ = "event_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(10), index=True)  # ADDED or DELETED
    title: Mapped[str] = mapped_column(String(300), index=True)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    event_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    source: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(1500))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
