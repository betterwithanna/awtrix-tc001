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
        ig_icon = config.IG_ICON or None
        apps["igfollow"] = awtrix.build_metric_app(
            f"Follower {awtrix.format_number(stats.get('followers', 0))}",
            awtrix.IG_PINK, icon=ig_icon)
        apps["igreach"] = awtrix.build_metric_app(
            f"Reach {awtrix.format_number(stats.get('reach', 0))}",
            awtrix.IG_PINK, icon=ig_icon)
    except instagram.TokenExpiredError as exc:
        log.error("Instagram-Token abgelaufen (refresh-token-Workflow erneuert ihn): %s", exc)
    except (instagram.InstagramError, RuntimeError) as exc:
        log.error("Instagram-Abruf fehlgeschlagen: %s", exc)

    # --- Mailing (Supabase Kontaktzahl) -------------------------------------
    mailing = sources.get_mailing_count()
    if mailing is not None:
        apps["mailing"] = awtrix.build_metric_app(
            f"Mailing {awtrix.format_number(mailing)}", awtrix.MAIL_BLUE)

    # --- YouTube / Spotify / Einnahmen(Vortag) folgen hier (eigene Felder) --

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
