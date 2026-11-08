from __future__ import annotations

from datetime import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .base import ScrapedEvent

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


CALENDAR_ID = "c_8c35c983ddc44404c000f69a3d00f20eb40700434b42bbe106d09cc4bf91c421@group.calendar.google.com"

ALLOWED_TITLE = "ŽBF 2"
DEFAULT_CREDENTIALS_PATH = "credentials.json"
DEFAULT_TOKEN_PATH = "token.json"


class GoogleCalendarScraper:

    SOURCE = "Google Calendar"

    def scrape(self, title: str, url: str = "") -> list[ScrapedEvent]:

        service = self._get_service()

        events_result = (
            service.events()
            .list(
                calendarId=CALENDAR_ID,
                maxResults=2500,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        google_events = events_result.get("items", [])

        events = []

        for event in google_events:

            summary = event.get("summary", "")

            if ALLOWED_TITLE not in summary.upper():
                continue

            start = event["start"].get("dateTime", event["start"].get("date"))

            if "T" in start:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))

                event_date = dt.date()
                event_time = dt.time()

            else:
                event_date = start
                event_time = None

            events.append(
                ScrapedEvent(
                    title=summary,
                    event_date=event_date,
                    event_time=event_time,
                    location=event.get("location", ""),
                    source=self.SOURCE,
                    url="",
                )
            )

        return events

    def _get_service(self):
        creds = None
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", DEFAULT_CREDENTIALS_PATH)
        token_path = os.getenv("GOOGLE_TOKEN_PATH", DEFAULT_TOKEN_PATH)

        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        except Exception:
            pass

        # Render does not have a browser available for the installed-app OAuth
        # flow. A stored token with a refresh token can renew itself instead.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        if not creds or not creds.valid:
            if os.getenv("RENDER") == "true":
                raise RuntimeError(
                    "Google Calendar needs valid credentials.json and token.json "
                    "Render Secret Files."
                )

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)

            creds = flow.run_local_server(port=0)

            with open(token_path, "w") as f:
                f.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)
