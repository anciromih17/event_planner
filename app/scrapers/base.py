from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
import re
import unicodedata
from typing import Optional


@dataclass(frozen=True)
class ScrapedEvent:
    title: str
    event_date: date
    event_time: Optional[time]
    location: Optional[str]
    source: str
    url: str

    @property
    def canonical_key(self) -> str:
        # Sources are intentionally excluded: the same public performance is merged.
        parts = (self.title, self.event_date.isoformat(), self.event_time.isoformat() if self.event_time else "", self.location or "")
        return "|".join(normalize(part) for part in parts)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", value).strip().casefold()


MONTHS = {
    "jan": 1, "januar": 1, "januarja": 1, "feb": 2, "februar": 2, "februarja": 2,
    "mar": 3, "marec": 3, "marca": 3, "apr": 4, "april": 4, "aprila": 4,
    "maj": 5, "maja": 5, "jun": 6, "junij": 6, "junija": 6, "jul": 7, "julij": 7,
    "julija": 7, "avg": 8, "avgust": 8, "avgusta": 8, "sep": 9, "september": 9,
    "septembra": 9, "okt": 10, "oktober": 10, "oktobra": 10, "nov": 11,
    "november": 11, "novembra": 11, "dec": 12, "december": 12, "decembra": 12,
}


def parse_slovenian_date(value: str) -> Optional[date]:
    value = " ".join(value.replace("─", " ").replace("–", " ").split())
    numeric = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
    if numeric:
        return date(int(numeric.group(3)), int(numeric.group(2)), int(numeric.group(1)))
    textual = re.search(r"(\d{1,2})\.?\s+([A-Za-zčšžČŠŽ]+)\.?\s*,?\s+(\d{4})", value)
    if not textual:
        return None
    month = MONTHS.get(normalize(textual.group(2)))
    return date(int(textual.group(3)), month, int(textual.group(1))) if month else None


def parse_time(value: str) -> Optional[time]:
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", value)
    return time(int(match.group(1)), int(match.group(2))) if match else None
