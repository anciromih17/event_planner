from __future__ import annotations

from calendar import monthcalendar
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session

from .api.events import router as events_router, serialize
from .database import ensure_schema, get_db
from .models import Event, EventAudit
from .scheduler import start_scheduler
from .services.conflict_detector import conflict_map
from .services.sync import refresh_events

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))
app = FastAPI(title="Termini predstav", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")
app.include_router(events_router)


@app.on_event("startup")
def startup() -> None:
    ensure_schema()
    start_scheduler()


def event_items(db: Session) -> list[dict]:
    events = db.query(Event).order_by(Event.event_date, Event.event_time, Event.title).all()
    conflicts = conflict_map(events)
    return [serialize(event, conflicts) for event in events]


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "index.html", {"events": event_items(db)})


@app.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request, db: Session = Depends(get_db)):
    entries = db.query(EventAudit).order_by(EventAudit.recorded_at.desc(), EventAudit.id.desc()).all()
    return templates.TemplateResponse(request, "audit.html", {"entries": entries})


@app.post("/api/refresh")
def refresh(db: Session = Depends(get_db)):
    return refresh_events(db)


@app.get("/api/calendar/{year}/{month}")
def calendar_data(year: int, month: int, db: Session = Depends(get_db)):
    if not 1 <= month <= 12:
        raise HTTPException(400, "Mesec mora biti med 1 in 12.")
    events = [item for item in event_items(db) if item["datum"].startswith(f"{year:04d}-{month:02d}")]
    return {"year": year, "month": month, "weeks": monthcalendar(year, month), "events": events}

@app.get("/export.xlsx")
def export_xlsx(month: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
                shows: list[str] | None = Query(None), db: Session = Depends(get_db)):
    from .services.exports import select_events, excel_document
    output = excel_document(select_events(event_items(db), month, shows))
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=termini-predstav.xlsx"})


@app.get("/export.pdf")
def export_pdf(month: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
               shows: list[str] | None = Query(None), db: Session = Depends(get_db)):
    from .services.exports import select_events, pdf_document
    output = pdf_document(select_events(event_items(db), month, shows), month, shows)
    return StreamingResponse(output, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=termini-predstav.pdf"})
