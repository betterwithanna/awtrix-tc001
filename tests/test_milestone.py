"""Tests fuer die 100k-Feier (Supabase/notify gemockt)."""
import milestone


class Rec:
    def __init__(self):
        self.writes = {}
        self.blasts = 0


def _patch(monkeypatch, rec, stored, test_env=False):
    monkeypatch.setattr(milestone.sources, "get_metric", lambda k: stored.get(k))
    monkeypatch.setattr(milestone.sources, "set_metric",
                        lambda k, v: rec.writes.__setitem__(k, v))
    monkeypatch.setattr(milestone.awtrix, "notify",
                        lambda payload: setattr(rec, "blasts", rec.blasts + 1))
    monkeypatch.setattr(milestone, "_now", lambda: 1_000_000.0)
    monkeypatch.setenv("MILESTONE_TEST", "1") if test_env else \
        monkeypatch.delenv("MILESTONE_TEST", raising=False)


def test_below_goal_does_nothing(monkeypatch):
    rec = Rec()
    _patch(monkeypatch, rec, stored={})
    apps = {}
    milestone.handle(99_906, apps)
    assert rec.blasts == 0 and apps == {} and rec.writes == {}


def test_first_crossing_fires_blast_and_party(monkeypatch):
    rec = Rec()
    _patch(monkeypatch, rec, stored={})
    apps = {}
    milestone.handle(100_001, apps)
    assert rec.blasts == milestone.REPEAT  # Blast spielt 4x
    assert "party" in apps
    assert rec.writes[milestone._STATE] == 1_000_000.0  # Zustand gemerkt


def test_already_crossed_party_within_3h(monkeypatch):
    rec = Rec()
    # vor 1h ueberschritten -> noch Party, kein neuer Blast
    _patch(monkeypatch, rec, stored={milestone._STATE: 1_000_000.0 - 3600})
    apps = {}
    milestone.handle(100_050, apps)
    assert rec.blasts == 0 and "party" in apps and "trophy" not in apps


def test_after_3h_shows_trophy(monkeypatch):
    rec = Rec()
    # vor 4h ueberschritten -> Badge statt Party
    _patch(monkeypatch, rec, stored={milestone._STATE: 1_000_000.0 - 4 * 3600})
    apps = {}
    milestone.handle(100_050, apps)
    assert rec.blasts == 0 and "trophy" in apps and "party" not in apps


def test_crossing_fires_once(monkeypatch):
    rec = Rec()
    stored = {}
    _patch(monkeypatch, rec, stored)
    apps = {}
    milestone.handle(100_001, apps)          # erstes Mal -> Blast 4x
    stored[milestone._STATE] = rec.writes[milestone._STATE]  # Zustand persistiert
    milestone.handle(100_002, {})            # zweiter Lauf -> KEIN neuer Blast
    assert rec.blasts == milestone.REPEAT


def test_none_followers_noop(monkeypatch):
    rec = Rec()
    _patch(monkeypatch, rec, stored={})
    apps = {}
    milestone.handle(None, apps)
    assert rec.blasts == 0 and apps == {}


def test_test_env_previews_without_state(monkeypatch):
    rec = Rec()
    _patch(monkeypatch, rec, stored={}, test_env=True)
    apps = {}
    milestone.handle(50_000, apps)           # unter Ziel, aber Testmodus
    assert rec.blasts == milestone.REPEAT and "party" in apps
    assert rec.writes == {}                   # KEIN echter Zustand gesetzt
