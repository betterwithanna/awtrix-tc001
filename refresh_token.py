#!/usr/bin/env python3
"""Erneuert/verlaengert den Instagram-Access-Token und protokolliert das Ablaufdatum.

Aufruf:
    python refresh_token.py                 # verlaengert den aktuellen IG_TOKEN
    python refresh_token.py <short_token>   # tauscht einen Short-Lived -> Long-Lived

Funktioniert fuer beide Auth-Wege (IG_AUTH=facebook|instagram):

* facebook  : fb_exchange_token (braucht FB_APP_ID + FB_APP_SECRET)
* instagram : ig_exchange_token (Short->Long, braucht FB_APP_SECRET)
              bzw. ig_refresh_token (verlaengert einen Long-Lived Token)

Der neue Token wird auf stdout ausgegeben -- danach in .env / GitHub-Secrets
als IG_TOKEN eintragen.
"""
import logging
import sys
from datetime import datetime, timedelta, timezone

import requests

import config

log = logging.getLogger("refresh_token")


def exchange_facebook(token):
    """Short- oder Long-Lived (Facebook) -> Long-Lived Token (~60 Tage)."""
    config.require("FB_APP_ID", "FB_APP_SECRET")
    url = f"https://graph.facebook.com/{config.IG_API_VERSION}/oauth/access_token"
    resp = requests.get(url, params={
        "grant_type": "fb_exchange_token",
        "client_id": config.FB_APP_ID,
        "client_secret": config.FB_APP_SECRET,
        "fb_exchange_token": token,
    }, timeout=20)
    resp.raise_for_status()
    return resp.json()


def exchange_instagram(short_token):
    """Short-Lived (Instagram Login) -> Long-Lived Token (~60 Tage)."""
    config.require("FB_APP_SECRET")
    resp = requests.get("https://graph.instagram.com/access_token", params={
        "grant_type": "ig_exchange_token",
        "client_secret": config.FB_APP_SECRET,
        "access_token": short_token,
    }, timeout=20)
    resp.raise_for_status()
    return resp.json()


def refresh_instagram(long_token):
    """Verlaengert einen bestehenden Long-Lived Instagram-Token um weitere ~60 Tage."""
    resp = requests.get("https://graph.instagram.com/refresh_access_token", params={
        "grant_type": "ig_refresh_token",
        "access_token": long_token,
    }, timeout=20)
    resp.raise_for_status()
    return resp.json()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    short = sys.argv[1] if len(sys.argv) > 1 else None

    if config.IG_AUTH == "instagram":
        data = exchange_instagram(short) if short else refresh_instagram(config.IG_TOKEN)
    else:
        # facebook: derselbe Endpoint nimmt Short- wie Long-Lived Tokens entgegen
        data = exchange_facebook(short or config.IG_TOKEN)

    token = data.get("access_token")
    expires_in = data.get("expires_in")
    if not token:
        raise RuntimeError(f"Kein Token erhalten. Antwort der API: {data}")

    log.info("Neuer Access-Token: %s...%s", token[:6], token[-4:])
    if expires_in:
        valid_until = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        log.info(
            "Gueltig fuer ca. %s Tage (bis %s UTC)",
            round(int(expires_in) / 86400, 1),
            valid_until.strftime("%Y-%m-%d %H:%M"),
        )
    log.info("-> Diesen Token als IG_TOKEN in .env / GitHub-Secrets eintragen.")

    # Reiner Token auf stdout, damit man ihn einfach weiterverarbeiten kann.
    print(token)


if __name__ == "__main__":
    main()
