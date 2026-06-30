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


def test_follower_delta_none_without_token(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.config, "REVENUE_TOKEN", None)
    assert sources.get_follower_delta(100) is None


def test_follower_delta_returns_value(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.config, "REVENUE_TOKEN", "t")
    monkeypatch.setattr(sources.requests, "post", lambda *a, **k: FakeResponse(200, 12))
    assert sources.get_follower_delta(100) == 12


def test_mailing_delta_returns_value(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.config, "REVENUE_TOKEN", "t")
    monkeypatch.setattr(sources.requests, "post", lambda *a, **k: FakeResponse(200, 1))
    assert sources.get_mailing_delta(447) == 1


def test_youtube_delta_returns_value(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.config, "REVENUE_TOKEN", "t")
    monkeypatch.setattr(sources.requests, "post", lambda *a, **k: FakeResponse(200, 2))
    assert sources.get_youtube_delta(58) == 2


def test_set_snapshot_skips_without_token(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.config, "REVENUE_TOKEN", None)

    def boom(*a, **k):
        raise AssertionError("set_snapshot darf ohne Token nicht senden")

    monkeypatch.setattr(sources.requests, "post", boom)
    assert sources.set_snapshot({"followers": 1}) is None


def test_set_snapshot_posts_payload_with_token(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.config, "REVENUE_TOKEN", "t")
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return FakeResponse(200, None)

    monkeypatch.setattr(sources.requests, "post", fake_post)
    sources.set_snapshot({"followers": 42})
    assert captured["url"].endswith("/rpc/awtrix_set_snapshot")
    assert captured["json"] == {"p_data": {"followers": 42}, "p_token": "t"}


def test_set_snapshot_swallows_errors(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    monkeypatch.setattr(sources.config, "REVENUE_TOKEN", "t")

    def boom(*a, **k):
        raise sources.requests.ConnectionError("down")

    monkeypatch.setattr(sources.requests, "post", boom)
    assert sources.set_snapshot({"x": 1}) is None  # kein Crash


def test_get_snapshot_none_without_config(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", None)
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", None)
    assert sources.get_snapshot() is None


def test_get_snapshot_returns_dict(monkeypatch):
    monkeypatch.setattr(sources.config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(sources.config, "SUPABASE_KEY", "k")
    payload = {"followers": 42, "revenue_today": 12.5}
    monkeypatch.setattr(sources.requests, "post", lambda *a, **k: FakeResponse(200, payload))
    assert sources.get_snapshot() == payload
