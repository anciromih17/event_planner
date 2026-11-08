from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class ConflictInfo:
    status: str
    conflicts_with: list[str]


def conflict_map(events: Iterable[object]) -> dict[int, ConflictInfo]:
    """Mark dates containing two or more different performances as conflicts.

    Times deliberately do not affect the initial rule. Duplicate listings of the
    same performance (for example Eventim + organiser page) are not a conflict.
    """
    by_date: dict[date, list[object]] = defaultdict(list)
    for event in events:
        by_date[event.event_date].append(event)

    result: dict[int, ConflictInfo] = {}
    for same_day in by_date.values():
        titles = {event.title.strip().casefold(): event.title for event in same_day}
        for event in same_day:
            other_titles = sorted(
                display for key, display in titles.items() if key != event.title.strip().casefold()
            )
            result[event.id] = ConflictInfo(
                status="KONFLIKT" if other_titles else "OK", conflicts_with=other_titles
            )
    return result
