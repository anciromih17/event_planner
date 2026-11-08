from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from .services.sync import refresh_events

scheduler = BackgroundScheduler(timezone="Europe/Ljubljana")


def scheduled_refresh() -> None:
    with SessionLocal() as db:
        refresh_events(db)


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(scheduled_refresh, "cron", hour=4, minute=0, id="daily_event_refresh", replace_existing=True)
        scheduler.start()
