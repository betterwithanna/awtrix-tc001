"""Tests fuer das Nacht-Dimmen (main._apply_brightness). awtrix.settings gemockt."""
import logging

import main


class _Rec:
    def __init__(self):
        self.calls = []


def _patch(monkeypatch, rec, night):
    monkeypatch.setattr(main.awtrix, "settings", lambda payload: rec.calls.append(payload))
    monkeypatch.setattr(main, "_is_night", lambda: night)


def test_night_dims_whole_display(monkeypatch):
    rec = _Rec()
    _patch(monkeypatch, rec, night=True)
    main._apply_brightness(logging.getLogger("test"))
    assert rec.calls == [{"ABRI": False, "BRI": main.NIGHT_BRI}]
    assert main.NIGHT_BRI == 1  # niedrigste Stufe (Fenster 19:00-06:00)


def test_day_restores_auto(monkeypatch):
    rec = _Rec()
    _patch(monkeypatch, rec, night=False)
    main._apply_brightness(logging.getLogger("test"))
    assert rec.calls == [{"ABRI": True}]
