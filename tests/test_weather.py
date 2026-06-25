"""Tests fuer die Aussentemperatur (Open-Meteo gemockt)."""
import weather


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


def test_temperature_parsed(monkeypatch):
    monkeypatch.setattr(weather.requests, "get",
                        lambda *a, **k: _Resp({"current": {"temperature_2m": 12.7}}))
    assert weather.get_temperature() == 12.7


def test_temperature_none_when_missing(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda *a, **k: _Resp({"current": {}}))
    assert weather.get_temperature() is None


def test_temperature_none_on_error(monkeypatch):
    def boom(*a, **k):
        raise weather.requests.RequestException("net")
    monkeypatch.setattr(weather.requests, "get", boom)
    assert weather.get_temperature() is None
