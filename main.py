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


def main():
    setup_logging()
    log = logging.getLogger("main")
    apps = {}

    # --- Instagram: Follower + Reichweite als ZWEI getrennte Felder ---------
    try:
        stats = instagram.get_stats()
        apps["igfollow"] = awtrix.build_metric_app(
            f"Follower {awtrix.format_number(stats.get('followers', 0))}",
            awtrix.IG_PINK, icon="ig")
        # Tageszuwachs der Follower seit 0:01 Uhr (gruen; bei Rueckgang rot)
        delta = sources.get_follower_delta(stats.get("followers", 0))
        if delta is not None:
            sign = "+" if delta >= 0 else ""
            apps["igtoday"] = awtrix.build_metric_app(
                f"{sign}{awtrix.format_number(delta)} heute",
                awtrix.GROWTH_GREEN if delta >= 0 else awtrix.DROP_RED)
        apps["igreach"] = awtrix.build_metric_app(
            f"Reach {awtrix.format_number(stats.get('reach', 0))}",
            awtrix.IG_PINK, icon="ig")
        # Reach letzter kompletter Tag vs Vortag in % (gruen/rot)
        reach_pct = instagram.get_reach_change_pct()
        if reach_pct is not None:
            apps["igreachpd"] = awtrix.build_metric_app(
                f"gestern {reach_pct:+.1f}%".replace(".", ","),
                awtrix.GROWTH_GREEN if reach_pct >= 0 else awtrix.DROP_RED)
    except instagram.TokenExpiredError as exc:
        log.error("Instagram-Token abgelaufen (refresh-token-Workflow erneuert ihn): %s", exc)
    except (instagram.InstagramError, RuntimeError) as exc:
        log.error("Instagram-Abruf fehlgeschlagen: %s", exc)

    # --- Mailing (Supabase Kontaktzahl) -------------------------------------
    mailing = sources.get_mailing_count()
    if mailing is not None:
        apps["mailing"] = awtrix.build_metric_app(
            f"Mailing {awtrix.format_number(mailing)}", awtrix.MAIL_BLUE, icon="mail")

    # --- YouTube (Abonnenten) -----------------------------------------------
    yt = sources.get_youtube_subscribers()
    if yt is not None:
        apps["youtube"] = awtrix.build_metric_app(
            f"YouTube {awtrix.format_number(yt)}", awtrix.YT_RED, icon="yt")

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
