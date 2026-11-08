from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Event, EventAudit
from app.scrapers.base import ScrapedEvent
from app.services.sync import _remove_missing_events, _upsert, _write_audit


def test_missing_event_is_deleted_and_written_to_audit_log():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        stale = ScrapedEvent("TV Poper v živo", date(2026, 9, 23), time(19), "Žalec", "Vid Valič", "https://example.test")
        current = ScrapedEvent("TV Poper v živo", date(2026, 9, 27), time(18), "Grosuplje", "Vid Valič", "https://example.test")
        assert _upsert(db, stale)
        assert _upsert(db, current)
        _write_audit(db, "ADDED", stale)
        _write_audit(db, "ADDED", current)
        assert _remove_missing_events(db, "Vid Valič", "TV Poper v živo", {current.canonical_key}) == 1
        db.commit()

        assert [event.event_date for event in db.query(Event).all()] == [date(2026, 9, 27)]
        deleted = db.query(EventAudit).filter_by(action="DELETED").one()
        assert deleted.event_date == date(2026, 9, 23)
        assert deleted.title == "TV Poper v živo"
