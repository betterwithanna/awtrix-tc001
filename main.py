#!/usr/bin/env python3
"""Orchestrierung: Instagram-Daten holen, App-Payload bauen, an die Uhr senden.

Aufruf:
    python main.py

Exit-Codes:
    0 = ok
    1 = allgemeiner Fehler (Abruf/Versand)
    2 = Access-Token abgelaufen (siehe refresh_token.py)
"""
import logging
import sys

import awtrix
import config
import instagram
import sources


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


def main():
    setup_logging()
    log = logging.getLogger("main")
    apps = {}

    # --- Instagram: Follower(+Zuwachs) & Reach(+Vortagsvergleich), je EIN Feld ---
    try:
        stats = instagram.get_stats()
        followers = stats.get("followers", 0)
        reach = stats.get("reach", 0)

        # Follower-Zahl (pink) + Tageszuwachs (gruen) in einem Feld
        frags = [(awtrix.format_number(followers), awtrix.IG_PINK)]
        frag = _delta_fragment(sources.get_follower_delta(followers))
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

    # --- YouTube-Abos (rot) + neue Abos heute (gruen) -----------------------
    yt = sources.get_youtube_subscribers()
    if yt is not None:
        frags = [(f"YouTube {awtrix.format_number(yt)}", awtrix.YT_RED)]
        frag = _delta_fragment(sources.get_youtube_delta(yt))
        if frag:
            frags.append(frag)
        apps["youtube"] = awtrix.build_combo_app(frags, icon="yt")

    # --- Einnahmen Vortag (EUR, aus dem Supabase-Spiegel) -------------------
    rev = sources.get_revenue_yesterday()
    if rev is not None:
        apps["revenue"] = awtrix.build_revenue_app(rev, icon="eur")

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
