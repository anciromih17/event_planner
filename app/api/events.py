from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..services.conflict_detector import conflict_map

router = APIRouter(prefix="/api/events", tags=["events"])


class ResolutionUpdate(BaseModel):
    resolved: bool


def serialize(event: Event, conflicts: dict) -> dict:
    info = conflicts[event.id]
    return {"id": event.id, "naziv_predstave": event.title,
            "datum": event.event_date.isoformat(),
            "ura": event.event_time.strftime("%H:%M") if event.event_time else None,
            "lokacija": event.location, "vir": event.source, "url": event.url,
            "zadnja_posodobitev": event.last_updated.isoformat(), "status": info.status,
            "konflikt_s": info.conflicts_with, "reseno": event.resolved}


@router.get("")
def list_events(title: Optional[str] = None, event_date: Optional[date] = None, conflicts_only: bool = False,
                search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Event)
    if title:
        query = query.filter(Event.title.ilike(f"%{title}%"))
    if event_date:
        query = query.filter(Event.event_date == event_date)
    if search:
        query = query.filter(or_(Event.title.ilike(f"%{search}%"), Event.location.ilike(f"%{search}%")))
    events = query.order_by(Event.event_date, Event.event_time, Event.title).all()
    conflicts = conflict_map(events)
    items = [serialize(event, conflicts) for event in events]
    return [item for item in items if not conflicts_only or item["status"] == "KONFLIKT"]


@router.patch("/{event_id}/resolved")
def update_resolution(event_id: int, update: ResolutionUpdate, db: Session = Depends(get_db)):
    """Store the resolution flag, but only for an event that is a conflict now."""
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "Termin ne obstaja.")

    all_events = db.query(Event).order_by(Event.event_date, Event.event_time, Event.title).all()
    conflicts = conflict_map(all_events)
    if conflicts[event.id].status != "KONFLIKT":
        raise HTTPException(409, "Samo konfliktni termini se lahko označijo kot rešeni.")

    event.resolved = update.resolved
    db.commit()
    db.refresh(event)
    return serialize(event, conflicts)
