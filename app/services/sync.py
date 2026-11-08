from __future__ import annotations

from datetime import datetime
import logging
from typing import Dict, List, Union

from sqlalchemy.orm import Session

from ..models import Event, EventAudit
from ..scrapers import VidValicScraper, GoogleCalendarScraper
from ..scrapers.base import ScrapedEvent

LOGGER = logging.getLogger(__name__)

SOURCES = [
    ("Google Calendar", "ŽBF 2", ""),
    ("Vid Valič", "Dediščina", "https://vidvalic.si/vstopnice-dediscina/"),
    ("Vid Valič", "Penziči", "https://vidvalic.si/vstopnice-penzici/"),
    ("Vid Valič", "TV Poper v živo", "https://vidvalic.si/vstopnice-tvpoper/"),
]


def refresh_events(db: Session) -> Dict[str, Union[int, List[str]]]:
    """Reconcile each successfully fetched source with the local event list."""
    added = updated = deleted = 0
    errors: list[str] = []
    scrapers = {"Google Calendar": GoogleCalendarScraper(), "Vid Valič": VidValicScraper()}
    for source, title, url in SOURCES:
        try:
            scraped_events = scrapers[source].scrape(title, url)
            found_keys = set()
            for scraped in scraped_events:
                was_new = _upsert(db, scraped)
                found_keys.add(scraped.canonical_key)
                added += was_new
                updated += not was_new
                if was_new:
                    _write_audit(db, "ADDED", scraped)
            # This runs only after a scraper completed successfully. A network or
            # parsing error therefore cannot silently remove valid local events.
            deleted += _remove_missing_events(db, source, title, found_keys)
            db.commit()
        except Exception as exc:
            db.rollback()
            message = f"{title} ({source}): {exc}"
            LOGGER.warning("Refresh failed: %s", message)
            errors.append(message)
    return {"added": added, "updated": updated, "deleted": deleted, "errors": errors}


def _upsert(db: Session, item: ScrapedEvent) -> bool:
    event = db.query(Event).filter_by(canonical_key=item.canonical_key).one_or_none()
    if event is None:
        db.add(Event(canonical_key=item.canonical_key, title=item.title, event_date=item.event_date,
                     event_time=item.event_time, location=item.location, source=item.source,
                     url=item.url, last_updated=datetime.utcnow()))
        return True
    event.title, event.event_date, event.event_time, event.location = item.title, item.event_date, item.event_time, item.location
    event.source = _combine(event.source, item.source)
    event.url = _combine(event.url, item.url)
    event.last_updated = datetime.utcnow()
    return False


def _remove_missing_events(db: Session, source: str, title: str, found_keys: set[str]) -> int:
    """Remove local entries absent from one successful source refresh."""
    query = db.query(Event).filter(Event.source == source)
    # Google Calendar event names include additional description after ŽBF 2.
    query = query.filter(Event.title.ilike(f"{title}%") if source == "Google Calendar" else Event.title == title)
    stale_events = [event for event in query.all() if event.canonical_key not in found_keys]
    for event in stale_events:
        _write_audit(db, "DELETED", event)
        db.delete(event)
    return len(stale_events)


def _write_audit(db: Session, action: str, item: ScrapedEvent | Event) -> None:
    db.add(EventAudit(action=action, title=item.title, event_date=item.event_date,
                      event_time=item.event_time, location=item.location,
                      source=item.source, url=item.url, recorded_at=datetime.utcnow()))


def _combine(old: str, new: str) -> str:
    return old if new in old.split(" | ") else f"{old} | {new}"
