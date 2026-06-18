"""Tests fuer Formatierungs- und App-Build-Funktionen (ohne echte Netzwerk-Calls)."""
import awtrix


def test_format_number_thousands():
    assert awtrix.format_number(1234) == "1.234"
    assert awtrix.format_number(0) == "0"
    assert awtrix.format_number(999) == "999"
    assert awtrix.format_number(1234567) == "1.234.567"


def test_format_number_rounds_floats():
    assert awtrix.format_number(1499.7) == "1.500"
    assert awtrix.format_number(42.2) == "42"


def test_build_instagram_app():
    app = awtrix.build_instagram_app({"followers": 12345, "reach": 6789})
    assert app["color"] == "#E1306C"          # Instagram-Pink
    assert "12.345" in app["text"]            # Follower, mit Tausenderpunkt
    assert "6.789" in app["text"]             # Reichweite
    assert app["duration"] == 8
    assert app["lifetime"] == 1800


def test_build_instagram_app_handles_missing_keys():
    app = awtrix.build_instagram_app({})
    assert "0" in app["text"]


def test_build_instagram_app_adds_icon(monkeypatch):
    monkeypatch.setattr(awtrix.config, "IG_ICON", "1234")
    app = awtrix.build_instagram_app({"followers": 1, "reach": 2})
    assert app["icon"] == "1234"


def test_build_instagram_app_without_icon(monkeypatch):
    monkeypatch.setattr(awtrix.config, "IG_ICON", "")
    app = awtrix.build_instagram_app({"followers": 1, "reach": 2})
    assert "icon" not in app


def test_build_revenue_app(monkeypatch):
    monkeypatch.setattr(awtrix.config, "EUR_SIGN", "EUR")
    app = awtrix.build_revenue_app(1499.7)
    assert "1.500" in app["text"]             # gerundet + Tausenderpunkt
    assert "EUR" in app["text"]
    assert app["center"] is True
    assert app["color"] == "#39FF14"


def test_push_rejects_unknown_mode(monkeypatch):
    monkeypatch.setattr(awtrix.config, "MODE", "carrier-pigeon")
    try:
        awtrix.push({"insta": {}})
    except awtrix.AwtrixError as exc:
        assert "carrier-pigeon" in str(exc)
    else:
        raise AssertionError("AwtrixError fuer unbekannten MODE erwartet")
