"""Tests fuer den 15-Tage-Schnitt (Prognose 100k)."""
import instagram


def _vals(seq):
    return {"data": [{"values": [{"value": v} for v in seq]}]}


def test_avg_strips_trailing_zeros(monkeypatch):
    # letzte ~Tage nicht finalisiert (0) -> abschneiden, Rest mitteln
    monkeypatch.setattr(instagram, "_request", lambda u, p: _vals([100, 200, 300, 0, 0]))
    assert instagram.get_follower_avg_per_day(3) == 200.0  # (100+200+300)/3


def test_avg_uses_last_n_window(monkeypatch):
    monkeypatch.setattr(instagram, "_request", lambda u, p: _vals([10, 20, 30, 40, 0]))
    # trailing 0 weg -> [10,20,30,40]; letzte 2 -> (30+40)/2
    assert instagram.get_follower_avg_per_day(2) == 35.0


def test_avg_none_when_all_zero(monkeypatch):
    monkeypatch.setattr(instagram, "_request", lambda u, p: _vals([0, 0, 0]))
    assert instagram.get_follower_avg_per_day(15) is None


def test_avg_none_when_no_rows(monkeypatch):
    monkeypatch.setattr(instagram, "_request", lambda u, p: {"data": []})
    assert instagram.get_follower_avg_per_day(15) is None
