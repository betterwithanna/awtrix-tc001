"""100k-Follower-Feier auf der Uhr.

Ablauf beim Ueberschreiten von 100.000 Followern (Owner-Wahl):
* EINMALIGER Fanfaren-Blast: Regenbogen + Fanfare + Konfetti-Icon + Lauftext
  (feuert sofort, zu JEDER Uhrzeit -- once in a lifetime).
* danach 3 Stunden PARTY-MODUS: goldenes Feier-Feld im Loop (nur visuell,
  KEIN wiederholter Ton).
* danach dauerhaftes STERN-BADGE "100.000" im Loop.

Zustand in Supabase (ADD-only Key ``milestone_100k_ts`` = Unix-Sekunden des
Ueberschreitens) -> loest genau EINMAL aus. Vorschau/Test: Env ``MILESTONE_TEST=1``
feuert Blast + Party OHNE den echten Zustand zu setzen (wartet weiter auf 100k).

Text bewusst in LATEIN (auch das RU "SPASIBO" transliteriert), weil der
AWTRIX-Font kein Kyrillisch rendert.
"""
import datetime as dt
import logging
import os

import awtrix
import sources

log = logging.getLogger(__name__)

GOAL = 100_000
PARTY_SECS = 3 * 3600          # Party-Modus-Dauer nach dem Ueberschreiten
REPEAT = 4                     # der Blast (Fanfare+Text) spielt 4x hintereinander
_STATE = "milestone_100k_ts"   # Supabase-Key (Unix-Sek. des Ueberschreitens)

# Triumphale Fanfare (RTTTL, Piezo): aufsteigender Sieges-Ruf + Schluss-Akzent.
FANFARE = ("100k:d=8,o=5,b=140:g,c6,e6,g6,e6,g6,4c7,"
           "g6,c7,e7,4g7,16p,c7,c7,c7,2c7")

GOLD = "#FFD700"

# RU translit + EN + DE (Font kann kein Kyrillisch).
_BLAST_TEXT = "100.000 !  SPASIBO - THANK YOU - DANKE  -  ANNA, WE DID IT TOGETHER"
_PARTY_TEXT = "100.000 - SPASIBO - THANK YOU - DANKE - WE DID IT"


def _now():
    return dt.datetime.now(dt.timezone.utc).timestamp()


def _fire_blast():
    """Grosser Feier-Notify: Fanfare + Regenbogen + Konfetti-Icon + Lauftext.

    Spielt ``REPEAT`` mal hintereinander: mit ``stack=True`` reihen sich die
    Notifications in die AWTRIX-Warteschlange und laufen nacheinander ab.
    """
    for _ in range(REPEAT):
        awtrix.notify({
            "text": _BLAST_TEXT,
            "rtttl": FANFARE,
            "rainbow": True,
            "icon": "party",
            "duration": 12,
            "wakeup": True,
            "hold": False,
            "stack": True,
        })
    log.info("100k-Blast %dx gefeuert", REPEAT)


def _party_app():
    return awtrix.build_combo_app([(_PARTY_TEXT, GOLD)], icon="party", duration=10)


def _trophy_app():
    return awtrix.build_metric_app("100.000", GOLD, icon="trophy", scroll=False)


def handle(followers, apps):
    """Feier-Logik. Fuegt ggf. Party-/Badge-Feld zu ``apps`` hinzu, feuert den Blast.

    ``MILESTONE_TEST=1`` -> Vorschau: Blast + Party, OHNE Zustand zu setzen.
    """
    if os.getenv("MILESTONE_TEST"):
        _fire_blast()
        apps["party"] = _party_app()
        log.info("MILESTONE_TEST: Vorschau gefeuert (kein echter Zustand gesetzt)")
        return

    ts = sources.get_metric(_STATE)

    if ts is None:
        # Noch nie ueberschritten. Erst beim tatsaechlichen Erreichen feiern.
        if followers is not None and followers >= GOAL:
            sources.set_metric(_STATE, _now())
            _fire_blast()
            apps["party"] = _party_app()
        return

    # Schon ueberschritten: 3h Party, danach dauerhaftes Badge.
    if _now() - ts < PARTY_SECS:
        apps["party"] = _party_app()
    else:
        apps["trophy"] = _trophy_app()
