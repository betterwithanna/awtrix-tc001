"""Tests fuer den Letzter-Beitrag-Abruf + das 24h-Frischefenster."""
import datetime as dt

import instagram
import main

_MEDIA = {"data": [{
    "id": "999", "media_type": "VIDEO", "media_product_type": "REELS",
    "timestamp": "2026-06-20T08:53:17+0000", "like_count": 7, "comments_count": 5,
}]}


def test_get_last_post_parses(monkeypatch):
    monkeypatch.setattr(instagram, "_request", lambda url, params: _MEDIA)
    monkeypatch.setattr(instagram, "_media_views", lambda mid: 317)
    p = instagram.get_last_post()
    assert p["product_type"] == "REELS"
    assert p["likes"] == 7 and p["comments"] == 5 and p["views"] == 317
    assert p["timestamp"].year == 2026 and p["timestamp"].tzinfo is not None


def test_get_last_post_no_media(monkeypatch):
    monkeypatch.setattr(instagram, "_request", lambda url, params: {"data": []})
    assert instagram.get_last_post() is None


def test_media_views_reads_total_value(monkeypatch):
    monkeypatch.setattr(instagram, "_request", lambda url, params:
                        {"data": [{"values": [{"value": 248}]}]})
    assert instagram._media_views("999") == 248


def test_media_views_none_when_empty(monkeypatch):
    monkeypatch.setattr(instagram, "_request", lambda url, params: {"data": []})
    assert instagram._media_views("999") is None


def test_is_fresh_window():
    now = dt.datetime.now(dt.timezone.utc)
    assert main._is_fresh(now - dt.timedelta(hours=1)) is True
    assert main._is_fresh(now - dt.timedelta(hours=30)) is False
    assert main._is_fresh(now + dt.timedelta(hours=1)) is False  # Zukunft -> nicht frisch
