"""Event-Toene fuer die Uhr: +100 Follower/Tag und neue Zahlung.

Der Cloud-Job ruft nach jedem Push ``follower_milestone`` und ``new_payment``
auf. Zustand liegt in Supabase (``chime_ig_hundreds`` / ``chime_revenue_mtd``),
damit jede 100er-Marke bzw. jeder Verkauf nur EINMAL klingelt.

Ruhezeiten 23:00-08:00 (Wiener Zeit): in dieser Zeit wird der Zustand zwar
aktualisiert (kein Nachklingeln spaeter), aber KEIN Ton gespielt.

Da der Job nur alle ~10 Min laeuft, kommt der Ton bis zu ~10 Min (Follower)
bzw. ~20 Min (Zahlung: Plattform-Cron + unser Cron) nach dem Ereignis.
"""
import datetime as dt
import logging
from zoneinfo import ZoneInfo

import awtrix
import sources

log = logging.getLogger(__name__)

# RTTTL-Melodien (kurz, ohne #): Aufstieg fuer Follower, Muenz-Sound fuer Sale.
LVLUP = "lvlup:d=16,o=6,b=160:c,e,g,c7"
COIN = "coin:d=4,o=5,b=900:16b6,32f7"

_VIENNA = ZoneInfo("Europe/Vienna")
_QUIET_START = 23  # ab 23:00 still
_QUIET_END = 8     # bis 08:00 still


def _active_now():
    """True, wenn ausserhalb der Ruhezeit (08:00-23:00 Wiener Zeit)."""
    hour = dt.datetime.now(_VIENNA).hour
    return _QUIET_END <= hour < _QUIET_START


def follower_milestone(delta):
    """Ton, sobald der heutige Follower-Zuwachs eine neue 100er-Marke erreicht."""
    if delta is None or delta < 0:
        return
    hundreds = int(delta) // 100
    last = sources.get_metric("chime_ig_hundreds")
    if last is None:
        # Erstlauf: Stand merken, NICHT rueckwirkend klingeln.
        sources.set_metric("chime_ig_hundreds", hundreds)
        return
    last = int(last)
    if hundreds > last:
        sources.set_metric("chime_ig_hundreds", hundreds)
        if _active_now():
            awtrix.notify({"text": f"+{hundreds * 100} heute!", "rtttl": LVLUP,
                           "color": awtrix.GROWTH_GREEN, "duration": 6})
            log.info("Chime: +%d Follower heute", hundreds * 100)
    elif hundreds < last:
        # Neuer Tag -> Zaehler ist zurueckgesetzt: Stand nachziehen, kein Ton.
        sources.set_metric("chime_ig_hundreds", hundreds)


def new_payment(revenue_mtd):
    """Ton (Cha-Ching), sobald die Monats-Einnahmen steigen (= neuer Verkauf).

    Nutzt ``revenue_eur_mtd`` (zaehlt im Monat nur hoch) statt des Tageswerts,
    damit der naechtliche Tages-Reset keinen Fehlalarm ausloest.
    """
    if revenue_mtd is None:
        return
    last = sources.get_metric("chime_revenue_mtd")
    if last is None:
        # Erstlauf: Stand merken, NICHT rueckwirkend klingeln.
        sources.set_metric("chime_revenue_mtd", revenue_mtd)
        return
    if revenue_mtd > last + 0.001:
        sources.set_metric("chime_revenue_mtd", revenue_mtd)
        if _active_now():
            awtrix.notify({"text": "Sale!", "rtttl": COIN,
                           "color": awtrix.REVENUE_GREEN, "duration": 6})
            log.info("Chime: neue Zahlung (mtd %.2f)", revenue_mtd)
    elif revenue_mtd < last - 0.001:
        # Monatswechsel -> mtd faellt: Stand nachziehen, kein Ton.
        sources.set_metric("chime_revenue_mtd", revenue_mtd)
