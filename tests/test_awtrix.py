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


def test_build_metric_app_scrolls_by_default():
    app = awtrix.build_metric_app("Follower 12.345", awtrix.IG_PINK)
    assert app["text"] == "Follower 12.345"
    assert app["color"] == awtrix.IG_PINK
    assert app["scrollSpeed"] == 90
    assert "center" not in app
    assert app["lifetime"] == 2400


def test_build_metric_app_centered_when_not_scrolling():
    app = awtrix.build_metric_app("99", awtrix.WHITE, scroll=False)
    assert app["center"] is True
    assert "scrollSpeed" not in app


def test_build_metric_app_adds_icon():
    app = awtrix.build_metric_app("1", awtrix.WHITE, icon="1234")
    assert app["icon"] == "1234"


def test_build_metric_app_without_icon():
    app = awtrix.build_metric_app("1", awtrix.WHITE)
    assert "icon" not in app


def test_build_combo_app_colored_fragments():
    app = awtrix.build_combo_app(
        [("78.428", awtrix.IG_PINK), (" +12", awtrix.GROWTH_GREEN)], icon="ig")
    assert app["icon"] == "ig"
    assert app["text"][0] == {"t": "78.428", "c": "E1306C"}   # ohne '#'
    assert app["text"][1] == {"t": " +12", "c": "2ECC40"}
    assert app["scrollSpeed"] == 90


def test_build_revenue_app(monkeypatch):
    monkeypatch.setattr(awtrix.config, "EUR_SIGN", "EUR")
    app = awtrix.build_revenue_app(1499.7)
    assert "1.500" in app["text"]             # gerundet + Tausenderpunkt
    assert "EUR" in app["text"]
    assert app["center"] is True
    assert app["color"] == awtrix.REVENUE_GREEN


def test_push_rejects_unknown_mode(monkeypatch):
    monkeypatch.setattr(awtrix.config, "MODE", "carrier-pigeon")
    try:
        awtrix.push({"insta": {}})
    except awtrix.AwtrixError as exc:
        assert "carrier-pigeon" in str(exc)
    else:
        raise AssertionError("AwtrixError fuer unbekannten MODE erwartet")
