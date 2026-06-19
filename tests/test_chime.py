"""Tests fuer die Event-Toene (chime). Supabase/notify werden gemockt."""
import chime


class Recorder:
    """Faengt set_metric-Schreibvorgaenge und notify-Aufrufe ab."""

    def __init__(self):
        self.writes = {}
        self.notifies = []


def _patch(monkeypatch, rec, stored, active=True):
    monkeypatch.setattr(chime.sources, "get_metric", lambda key: stored.get(key))
    monkeypatch.setattr(chime.sources, "set_metric",
                        lambda key, value: rec.writes.__setitem__(key, value))
    monkeypatch.setattr(chime.awtrix, "notify", lambda payload: rec.notifies.append(payload))
    monkeypatch.setattr(chime, "_active_now", lambda: active)


# --- Follower-Meilenstein ---------------------------------------------------

def test_follower_first_run_seeds_no_tone(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={})  # noch kein Stand
    chime.follower_milestone(250)
    assert rec.notifies == []
    assert rec.writes["chime_ig_hundreds"] == 2  # Stand gemerkt, kein Ton


def test_follower_new_hundred_rings(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_ig_hundreds": 1})
    chime.follower_milestone(205)  # 2 > 1
    assert len(rec.notifies) == 1
    assert rec.notifies[0]["rtttl"] == chime.LVLUP
    assert "+200" in rec.notifies[0]["text"]
    assert rec.writes["chime_ig_hundreds"] == 2


def test_follower_same_hundred_silent(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_ig_hundreds": 2})
    chime.follower_milestone(250)  # 2 == 2
    assert rec.notifies == []


def test_follower_reset_on_new_day(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_ig_hundreds": 3})
    chime.follower_milestone(10)  # 0 < 3 -> Reset
    assert rec.notifies == []
    assert rec.writes["chime_ig_hundreds"] == 0


def test_follower_quiet_hours_seeds_but_silent(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_ig_hundreds": 0}, active=False)
    chime.follower_milestone(150)  # 1 > 0, aber Ruhezeit
    assert rec.notifies == []
    assert rec.writes["chime_ig_hundreds"] == 1  # Stand trotzdem nachziehen


def test_follower_none_noop(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_ig_hundreds": 0})
    chime.follower_milestone(None)
    assert rec.notifies == [] and rec.writes == {}


# --- Neue Zahlung -----------------------------------------------------------

def test_payment_first_run_seeds_no_tone(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={})
    chime.new_payment(120.0)
    assert rec.notifies == []
    assert rec.writes["chime_revenue_mtd"] == 120.0


def test_payment_increase_rings(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_revenue_mtd": 100.0})
    chime.new_payment(119.0)
    assert len(rec.notifies) == 1
    assert rec.notifies[0]["rtttl"] == chime.COIN
    assert rec.writes["chime_revenue_mtd"] == 119.0


def test_payment_no_change_silent(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_revenue_mtd": 100.0})
    chime.new_payment(100.0)
    assert rec.notifies == []


def test_payment_month_reset_silent(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_revenue_mtd": 500.0})
    chime.new_payment(12.0)  # Monatswechsel -> faellt
    assert rec.notifies == []
    assert rec.writes["chime_revenue_mtd"] == 12.0


def test_payment_quiet_hours_silent(monkeypatch):
    rec = Recorder()
    _patch(monkeypatch, rec, stored={"chime_revenue_mtd": 100.0}, active=False)
    chime.new_payment(150.0)
    assert rec.notifies == []
    assert rec.writes["chime_revenue_mtd"] == 150.0
