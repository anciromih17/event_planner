from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.events import ResolutionUpdate, update_resolution
from app.database import Base
from app.models import Event


def _event(key: str, title: str, event_date: date) -> Event:
    return Event(
        canonical_key=key,
        title=title,
        event_date=event_date,
        event_time=None,
        location=None,
        source="Test",
        url="https://example.test",
    )


def test_only_conflicting_event_can_be_marked_resolved():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        conflicting = _event("one", "Dediščina", date(2026, 10, 1))
        nonconflicting = _event("three", "Penziči", date(2026, 10, 2))
        db.add_all([conflicting, _event("two", "TV Poper", date(2026, 10, 1)), nonconflicting])
        db.commit()

        response = update_resolution(conflicting.id, ResolutionUpdate(resolved=True), db)
        assert response["reseno"] is True

        with pytest.raises(HTTPException) as error:
            update_resolution(nonconflicting.id, ResolutionUpdate(resolved=True), db)
        assert error.value.status_code == 409
