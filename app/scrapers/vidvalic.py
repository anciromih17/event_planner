from __future__ import annotations

from collections.abc import Iterable

import requests
from bs4 import BeautifulSoup

from .base import ScrapedEvent, parse_slovenian_date, parse_time


class VidValicScraper:
    """Parser for Vid Valič's WordPress + Tickera `tc_filter_events` endpoint."""

    SOURCE = "Vid Valič"
    HEADERS = {"User-Agent": "EventPlanner/1.0 (+internal public schedule monitor)"}

    def scrape(self, title: str, url: str) -> list[ScrapedEvent]:
        page = requests.get(url, headers=self.HEADERS, timeout=30)
        page.raise_for_status()
        page_soup = BeautifulSoup(page.text, "html.parser")
        category = page_soup.select_one("#tc_event_categories")
        if not category or not category.get("value"):
            return []
        payload = {
            "action": "tc_filter_events", "tc_categories": category["value"],
            "tc_start_date": "", "tc_end_date": "", "tc_column_number": "1",
            "tc_show_excerpt": "false", "tc_show_number_of_posts": "100",
            "tc_pagination_number": "1", "tc_show_default_featured_image": "false",
            "tc_selected_category_values": "", "tc_show_past_events": "false",
            "tc_order_events_by": "asc", "className": "",
        }
        response = requests.post("https://vidvalic.si/wp-admin/admin-ajax.php", data=payload, headers=self.HEADERS, timeout=30)
        response.raise_for_status()
        return self.parse_ajax_html(response.text, title, url)

    def parse_ajax_html(self, html: str, title: str, url: str) -> list[ScrapedEvent]:
        soup = BeautifulSoup(html, "html.parser")
        events: list[ScrapedEvent] = []
        for card in soup.select(".tc-single-event"):
            card_text = card.get_text(" ", strip=True)
            event_date = parse_slovenian_date(card_text)
            if not event_date:
                continue
            location_node = card.select_one(".tc-event-location, .tc-location, .event-location")
            location = location_node.get_text(" ", strip=True) if location_node else None
            events.append(ScrapedEvent(title, event_date, parse_time(card_text), location, self.SOURCE, url))
        # Tickera templates can change class names; retain an accessible fallback.
        if not events:
            for node in soup.select("article, li, div"):
                event_date = parse_slovenian_date(node.get_text(" ", strip=True))
                if event_date:
                    events.append(ScrapedEvent(title, event_date, parse_time(node.get_text(" ", strip=True)), None, self.SOURCE, url))
        return _unique(events)


def _unique(events: Iterable[ScrapedEvent]) -> list[ScrapedEvent]:
    return list({event.canonical_key: event for event in events}.values())
