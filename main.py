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


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    setup_logging()
    log = logging.getLogger("main")

    try:
        stats = instagram.get_stats()

        ig_icon = config.IG_ICON or None
        apps = {
            # Instagram: Follower + Reichweite als ZWEI getrennte Felder.
            "igfollow": awtrix.build_metric_app(
                f"Follower {awtrix.format_number(stats.get('followers', 0))}",
                awtrix.IG_PINK, icon=ig_icon),
            "igreach": awtrix.build_metric_app(
                f"Reach {awtrix.format_number(stats.get('reach', 0))}",
                awtrix.IG_PINK, icon=ig_icon),
        }
        # --- Weitere Kennzahlen folgen (eigene Felder) ----------------------
        # YouTube-Abos, Spotify-Follower, Mailing, Homepage, Einnahmen(Vortag).
        # Jeweils Datenquelle anbinden und z. B.:
        #   apps["revenue"] = awtrix.build_revenue_app(get_revenue_yesterday())

        awtrix.push(apps)
    except instagram.TokenExpiredError as exc:
        log.error("Token abgelaufen -- bitte erneuern (refresh_token.py): %s", exc)
        return 2
    except instagram.InstagramError as exc:
        log.error("Instagram-Abruf fehlgeschlagen: %s", exc)
        return 1
    except awtrix.AwtrixError as exc:
        log.error("Senden an die Uhr fehlgeschlagen: %s", exc)
        return 1
    except RuntimeError as exc:
        # z. B. fehlende Pflicht-Konfiguration (config.require)
        log.error("Konfigurationsfehler: %s", exc)
        return 1

    log.info("Fertig -- Apps gesendet: %s", ", ".join(apps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
