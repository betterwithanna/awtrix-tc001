#!/usr/bin/env python3
"""Orchestrierung: Instagram-Daten holen, App-Payload bauen, an die Uhr senden.

Aufruf:
    python main.py

Exit-Codes:
    0 = ok
    1 = allgemeiner Fehler (Abruf/Versand)
    2 = Access-Token abgelaufen (siehe refresh_token.py)
"""
import datetime as dt
import logging
import sys
from zoneinfo import ZoneInfo

import awtrix
import chime
import config
import instagram
import sources

_VIENNA = ZoneInfo("Europe/Vienna")
NIGHT_BRI = 1  # niedrigste Nacht-Helligkeit (Owner-Wunsch); ABRI=false fixiert
               # den Wert, sonst regelt der Lichtsensor staendig nach.


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _delta_fragment(delta):
    """(text, farbe) fuer einen Tageszuwachs ' +N' -- oder None, wenn unbekannt."""
    if delta is None:
        return None
    sign = "+" if delta >= 0 else ""
    color = awtrix.GROWTH_GREEN if delta >= 0 else awtrix.DROP_RED
    return (f" {sign}{awtrix.format_number(delta)}", color)


def _pct_fragment(pct):
    """(text, farbe) fuer die Live-Abweichung heute vs gestern ' +-X%' -- oder None."""
    if pct is None:
        return None
    color = awtrix.GROWTH_GREEN if pct >= 0 else awtrix.DROP_RED
    return (f" {round(pct):+d}%", color)


def _is_night():
    """True zwischen 19:00 und 06:00 Wiener Zeit (Display-Dimmfenster)."""
    hour = dt.datetime.now(_VIENNA).hour
    return hour >= 19 or hour < 6


def _is_morning():
    """True zwischen 06:00 und 09:00 Wiener Zeit (Guten-Morgen-Gruss)."""
    return 6 <= dt.datetime.now(_VIENNA).hour < 9


def _apply_brightness(log):
    """Nachts (19:00-06:00 Wien) das ganze Display fix auf BRI=1 dimmen, sonst Auto.

    Wird bei JEDEM Lauf gesetzt (selbstkorrigierend alle ~15 Min). Tagsueber
    Auto-Helligkeit (ABRI=true) = die normale Geraete-Steuerung. Fehler kippen
    den Push nicht -- awtrix.settings loggt nur.
    """
    if _is_night():
        awtrix.settings({"ABRI": False, "BRI": NIGHT_BRI})
        log.info("Helligkeit: Nacht (BRI=%d, fix)", NIGHT_BRI)
    else:
        awtrix.settings({"ABRI": True})
        log.info("Helligkeit: Tag (Auto)")


def main():
    setup_logging()
    log = logging.getLogger("main")
    _apply_brightness(log)
    apps = {}
    follower_delta = None  # fuer den +100-Follower-Ton nach dem Push

    # --- Instagram: Follower(+Zuwachs) & Reach(+Vortagsvergleich), je EIN Feld ---
    try:
        stats = instagram.get_stats()
        followers = stats.get("followers", 0)
        reach = stats.get("reach", 0)

        # Follower-Zahl (pink) + Tageszuwachs (gruen) in einem Feld
        follower_delta = sources.get_follower_delta(followers)
        frags = [(awtrix.format_number(followers), awtrix.IG_PINK)]
        frag = _delta_fragment(follower_delta)
        if frag:
            frags.append(frag)
        apps["igfollow"] = awtrix.build_combo_app(frags, icon="ig")

        # Reach (pink) + Vortagsvergleich (gruen/rot) in einem Feld
        frags = [(f"Reach {awtrix.format_number(reach)}", awtrix.IG_PINK)]
        frag = _pct_fragment(instagram.get_reach_change_pct())
        if frag:
            frags.append(frag)
        apps["igreach"] = awtrix.build_combo_app(frags, icon="ig")
    except instagram.TokenExpiredError as exc:
        log.error("Instagram-Token abgelaufen (refresh-token-Workflow erneuert ihn): %s", exc)
    except (instagram.InstagramError, RuntimeError) as exc:
        log.error("Instagram-Abruf fehlgeschlagen: %s", exc)

    # --- Mailing-Zahl (blau) + neue Kontakte heute (gruen) ------------------
    mailing = sources.get_mailing_count()
    if mailing is not None:
        frags = [(f"Mail {awtrix.format_number(mailing)}", awtrix.MAIL_BLUE)]
        frag = _delta_fragment(sources.get_mailing_delta(mailing))
        if frag:
            frags.append(frag)
        apps["mailing"] = awtrix.build_combo_app(frags, icon="mail")

    # --- YouTube voruebergehend deaktiviert (zu wenige Abos, macht aktuell
    #     wenig Sinn). sources.get_youtube_subscribers()/get_youtube_delta()
    #     bleiben da -- Block bei Bedarf einfach wieder einkommentieren.

    # --- Einnahmen heute (EUR, live aus Taplink via Supabase-Spiegel) -------
    # Bevorzugt den Live-Tageswert; faellt auf den Vortag zurueck, falls heute
    # noch kein Wert gespiegelt wurde.
    # Heutiger Live-Wert direkt -- ein 0 am Morgen ist gewollt (kein Vortag).
    rev = sources.get_revenue_today()
    if rev is not None:
        # Kein Icon -- Text "X EUR" ist eindeutig genug.
        apps["revenue"] = awtrix.build_revenue_app(rev)

    # --- Persoenliche Zeile: Herz + "I LOVE YOU" ----------------------------
    apps["love"] = awtrix.build_metric_app("I LOVE YOU FOREVER", awtrix.IG_PINK, icon="heart")

    # --- Guten-Morgen-Gruss: nur 06:00-09:00 Wien, eigenes Feld + Sonne ------
    # Ausserhalb des Fensters die App aktiv entfernen (sonst bliebe sie wegen
    # retain=True dauerhaft im Loop haengen).
    if _is_morning():
        apps["morning"] = awtrix.build_metric_app(
            "Good morning my wonderful Wifey!", "#FFC800", icon="sun"
        )
    else:
        awtrix.remove_app("morning")

    if not apps:
        log.error("Keine Kennzahlen verfuegbar -- nichts zu senden.")
        return 1

    try:
        awtrix.push(apps)
    except awtrix.AwtrixError as exc:
        log.error("Senden an die Uhr fehlgeschlagen: %s", exc)
        return 1
    except RuntimeError as exc:
        log.error("Konfigurationsfehler: %s", exc)
        return 1

    log.info("Fertig -- Apps gesendet: %s", ", ".join(apps))

    # --- Event-Toene (nach dem Push, optional; Fehler kippen den Lauf nicht) -
    # +100 Follower/Tag bzw. neuer Verkauf -> kurzer Ton, Ruhe 23-8 Uhr.
    try:
        chime.follower_milestone(follower_delta)
        chime.new_payment(sources.get_metric("revenue_eur_mtd"))
    except Exception as exc:  # noqa: BLE001 -- Ton ist Beiwerk
        log.warning("Chime fehlgeschlagen: %s", exc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
