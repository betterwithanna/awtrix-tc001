"""SmallCap-Portfolio (TROLL + Buttcoin), SEPARAT vom Haupt-Krypto-Feld.

Live-Wert in EUR via CoinGecko (kostenlos, kein Key). Gleiche Struktur wie
crypto.py (Menge + Kostenbasis pro Position), aber eigenes Feld/eigene Summe --
bewusst nicht mit BTC/SOL/PEPE vermischt (Owner-Wunsch: separates Feld).

``get_portfolio()`` liefert ein ``SmallCapPortfolio``-Tupel:
    total    -- aktueller Gesamtwert in EUR
    day_pct  -- 24h-Aenderung des Gesamtwerts in %
    day_eur  -- 24h-Aenderung des Gesamtwerts in EUR
    cost     -- insgesamt investiert (EUR)
    pl_eur   -- Gewinn/Verlust seit Kauf (EUR)
    pl_pct   -- Gewinn/Verlust seit Kauf (%)

None bei Fehler/fehlendem Preis.
"""
import logging
from collections import namedtuple

import requests

log = logging.getLogger(__name__)

# Kauf 20.08.2026 (Phantom-Wallet-Screenshot): Kostenbasis = Wert zum Kaufzeitpunkt
# (Owner: "just bought", Kostenbasis = damaliger EUR-Wert).
#   TROLL:    11,264.4069 Stk. -> 473.44 EUR
#   Buttcoin: 50,340.66934 Stk. -> 482.56 EUR
# CoinGecko-IDs per Preis-Abgleich verifiziert (Ziel ~0.049 / ~0.0109 USD/Stk.).
HOLDINGS = {
    "troll-2": {"amount": 11264.4069, "cost_eur": 473.44},
    "buttcoin-7": {"amount": 50340.66934, "cost_eur": 482.56},
}

_URL = "https://api.coingecko.com/api/v3/simple/price"

SmallCapPortfolio = namedtuple("SmallCapPortfolio", "total day_pct day_eur cost pl_eur pl_pct")


def get_portfolio():
    """``SmallCapPortfolio``-Tupel oder None bei Fehler/fehlendem Preis."""
    try:
        resp = requests.get(_URL, params={
            "ids": ",".join(HOLDINGS),
            "vs_currencies": "eur",
            "include_24hr_change": "true",
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        log.warning("SmallCap-Preise nicht abrufbar: %s", exc)
        return None

    total = prev = cost = 0.0
    for coin_id, holding in HOLDINGS.items():
        amount = holding["amount"]
        row = data.get(coin_id) or {}
        price = row.get("eur")
        if price is None:
            log.warning("Kein EUR-Preis fuer %s", coin_id)
            return None
        change = row.get("eur_24h_change") or 0.0
        total += amount * price
        prev += amount * (price / (1 + change / 100))
        cost += holding["cost_eur"]

    if prev <= 0 or cost <= 0:
        return None

    day_eur = total - prev
    day_pct = day_eur / prev * 100
    pl_eur = total - cost
    pl_pct = pl_eur / cost * 100

    return SmallCapPortfolio(total, day_pct, day_eur, cost, pl_eur, pl_pct)
