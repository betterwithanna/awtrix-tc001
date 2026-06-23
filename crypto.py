"""Krypto-Portfolio-Wert (BTC + SOL) live in EUR via CoinGecko (kostenlos, kein Key).

``get_portfolio()`` liefert (Gesamtwert EUR, Tagesveraenderung %, Tagesveraenderung EUR).
Die Tagesveraenderung ist die 24h-Aenderung des Gesamtwerts, gewichtet ueber die
24h-Preisaenderung beider Coins.
"""
import logging

import requests

log = logging.getLogger(__name__)

# Bestand (fix). Bei Aenderung der Mengen hier anpassen.
HOLDINGS = {"bitcoin": 0.04932662, "solana": 45.46}

_URL = "https://api.coingecko.com/api/v3/simple/price"


def get_portfolio():
    """(total_eur, change_pct, change_eur) oder None bei Fehler/fehlendem Preis."""
    try:
        resp = requests.get(_URL, params={
            "ids": ",".join(HOLDINGS),
            "vs_currencies": "eur",
            "include_24hr_change": "true",
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        log.warning("Krypto-Preise nicht abrufbar: %s", exc)
        return None

    total = prev = 0.0
    for coin, amount in HOLDINGS.items():
        row = data.get(coin) or {}
        price = row.get("eur")
        if price is None:
            log.warning("Kein EUR-Preis fuer %s", coin)
            return None
        change = row.get("eur_24h_change") or 0.0
        total += amount * price
        prev += amount * (price / (1 + change / 100))  # Wert vor 24h

    if prev <= 0:
        return None
    return total, (total - prev) / prev * 100, total - prev
