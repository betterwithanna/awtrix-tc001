"""Tests fuer die Zusatz-Datenquellen (requests gemockt, keine echten Calls)."""
import sources


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise sources.requests.HTTPError(str(self.status_code))

    def json(self):
        return self._payload


def test_mailing_none_without_config(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", None)
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", None)
    assert sources.get_mailing_count() is None


def test_mailing_returns_count(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.requests, "post", lambda *a, **k: FakeResponse(200, 446))
    assert sources.get_mailing_count() == 446


def test_mailing_swallows_errors(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")

    def boom(*a, **k):
        raise sources.requests.ConnectionError("down")

    monkeypatch.setattr(sources.requests, "post", boom)
    assert sources.get_mailing_count() is None


def test_youtube_none_without_config(monkeypatch):
    monkeypatch.setattr(sources.config, "YT_API_KEY", None)
    monkeypatch.setattr(sources.config, "YT_CHANNEL_ID", None)
    assert sources.get_youtube_subscribers() is None


def test_youtube_returns_subscribers(monkeypatch):
    monkeypatch.setattr(sources.config, "YT_API_KEY", "k")
    monkeypatch.setattr(sources.config, "YT_CHANNEL_ID", "UC123")
    payload = {"items": [{"statistics": {"subscriberCount": "56", "hiddenSubscriberCount": False}}]}
    monkeypatch.setattr(sources.requests, "get", lambda *a, **k: FakeResponse(200, payload))
    assert sources.get_youtube_subscribers() == 56


def test_youtube_hidden_count_returns_none(monkeypatch):
    monkeypatch.setattr(sources.config, "YT_API_KEY", "k")
    monkeypatch.setattr(sources.config, "YT_CHANNEL_ID", "UC123")
    payload = {"items": [{"statistics": {"hiddenSubscriberCount": True}}]}
    monkeypatch.setattr(sources.requests, "get", lambda *a, **k: FakeResponse(200, payload))
    assert sources.get_youtube_subscribers() is None


def test_revenue_none_without_config(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", None)
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", None)
    assert sources.get_revenue_yesterday() is None


def test_revenue_returns_value(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.requests, "post", lambda *a, **k: FakeResponse(200, 1234.5))
    assert sources.get_revenue_yesterday() == 1234.5


def test_revenue_null_returns_none(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.requests, "post", lambda *a, **k: FakeResponse(200, None))
    assert sources.get_revenue_yesterday() is None
