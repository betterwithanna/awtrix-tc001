"""Tests fuer den Instagram-Datenabruf -- requests wird gemockt, keine echten Calls."""
import pytest

import instagram


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


def _mock_get(monkeypatch, response):
    monkeypatch.setattr(instagram.requests, "get", lambda *a, **k: response)


def test_get_followers(monkeypatch):
    _mock_get(monkeypatch, FakeResponse(200, {"followers_count": 4200, "media_count": 100}))
    assert instagram.get_followers() == 4200


def test_get_followers_missing_field_defaults_zero(monkeypatch):
    _mock_get(monkeypatch, FakeResponse(200, {"media_count": 10}))
    assert instagram.get_followers() == 0


def test_get_reach_total_value(monkeypatch):
    _mock_get(monkeypatch, FakeResponse(200, {"data": [{"total_value": {"value": 8888}}]}))
    assert instagram.get_reach() == 8888


def test_get_reach_empty_data_returns_zero(monkeypatch):
    _mock_get(monkeypatch, FakeResponse(200, {"data": []}))
    assert instagram.get_reach() == 0


def test_get_reach_swallows_errors(monkeypatch):
    # Reichweite ist optional -> Fehler darf nicht hochblubbern, sondern 0 liefern.
    _mock_get(monkeypatch, FakeResponse(500, {"error": {"code": 1, "message": "boom"}}))
    assert instagram.get_reach() == 0


def test_expired_token_raises(monkeypatch):
    _mock_get(monkeypatch, FakeResponse(400, {"error": {"code": 190, "message": "expired"}}))
    with pytest.raises(instagram.TokenExpiredError):
        instagram.get_followers()


def test_rate_limit_raises_instagram_error(monkeypatch):
    _mock_get(monkeypatch, FakeResponse(403, {"error": {"code": 4, "message": "limit"}}))
    with pytest.raises(instagram.InstagramError):
        instagram.get_followers()


def test_base_url_switch(monkeypatch):
    monkeypatch.setattr(instagram.config, "IG_USER_ID", "999")
    monkeypatch.setattr(instagram.config, "IG_API_VERSION", "v21.0")

    monkeypatch.setattr(instagram.config, "IG_AUTH", "facebook")
    assert instagram._base_url() == "https://graph.facebook.com/v21.0/999"

    monkeypatch.setattr(instagram.config, "IG_AUTH", "instagram")
    assert instagram._base_url() == "https://graph.instagram.com/v21.0/999"
