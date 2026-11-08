from datetime import date
from types import SimpleNamespace

from app.services.conflict_detector import conflict_map


def test_same_day_different_shows_are_conflicts():
    events = [SimpleNamespace(id=1, title="Dediščina", event_date=date(2026, 9, 10)), SimpleNamespace(id=2, title="TV Poper", event_date=date(2026, 9, 10))]
    result = conflict_map(events)
    assert result[1].status == "KONFLIKT"
    assert result[1].conflicts_with == ["TV Poper"]


def test_same_show_duplicate_is_not_conflict():
    events = [SimpleNamespace(id=1, title="Penziči", event_date=date(2026, 9, 10)), SimpleNamespace(id=2, title="Penziči", event_date=date(2026, 9, 10))]
    assert all(value.status == "OK" for value in conflict_map(events).values())
