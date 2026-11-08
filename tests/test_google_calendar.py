from unittest.mock import patch

from app.scrapers.google_calendar import GoogleCalendarScraper


class ExpiredCredentials:
    valid = False
    expired = True
    refresh_token = "refresh-token"

    def __init__(self):
        self.refresh_called = False

    def refresh(self, request):
        self.refresh_called = True
        self.valid = True


def test_expired_google_token_is_refreshed_without_browser_login(monkeypatch):
    credentials = ExpiredCredentials()
    service = object()
    monkeypatch.setenv("GOOGLE_TOKEN_PATH", "/tmp/token.json")

    with patch(
        "app.scrapers.google_calendar.Credentials.from_authorized_user_file",
        return_value=credentials,
    ), patch("app.scrapers.google_calendar.build", return_value=service) as build:
        assert GoogleCalendarScraper()._get_service() is service

    assert credentials.refresh_called
    build.assert_called_once()
