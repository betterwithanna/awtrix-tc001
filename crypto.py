"""Krypto-Portfolio (BTC + SOL): Live-Wert in EUR via CoinGecko (kostenlos, kein Key).

Jeder Bestand haelt die Menge (``amount``) UND die insgesamt investierte Summe
in EUR (``cost_eur`` = Kostenbasis, Summe aller Kaeufe). Bei einem neuen Kauf
beide Werte erhoehen::

    amount   += gekaufte_menge
    cost_eur += gekaufte_menge * kaufpreis_eur

``get_portfolio()`` liefert ein ``Portfolio``-Tupel:

    total    -- aktueller Gesamtwert in EUR
    day_pct  -- 24h-Aenderung des Gesamtwerts in %
    day_eur  -- 24h-Aenderung des Gesamtwerts in EUR
    cost     -- insgesamt investiert (EUR) oder None, solange nicht fuer JEDEN
                Coin ein cost_eur gesetzt ist
    pl_eur   -- Gewinn/Verlust seit Kauf (EUR) oder None
    pl_pct   -- Gewinn/Verlust seit Kauf (%) oder None

Die Tagesaenderung ist die 24h-Aenderung des Gesamtwerts, gewichtet ueber die
24h-Preisaenderung beider Coins. Bei Fehler/fehlendem Preis: None.
"""
import logging
from collections import namedtuple

import requests

log = logging.getLogger(__name__)

# Bestand: Menge + insgesamt investierte EUR (Kostenbasis, Summe aller Kaeufe).
# Bei neuem Kauf: amount += Menge, cost_eur += Menge * Kaufpreis.
# cost_eur=None -> Kaufpreis noch nicht hinterlegt; die Seit-Kauf-Rendite wird
# dann ausgelassen (die Uhr zeigt weiterhin Wert + Tagesaenderung).
HOLDINGS = {
    "bitcoin": {"amount": 0.04932662, "cost_eur": None},
    "solana": {"amount": 45.46, "cost_eur": None},
}

_URL = "https://api.coingecko.com/api/v3/simple/price"

Portfolio = namedtuple("Portfolio", "total day_pct day_eur cost pl_eur pl_pct")


def get_portfolio():
    """``Portfolio``-Tupel oder None bei Fehler/fehlendem Preis."""
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

    total = prev = cost = 0.0
    cost_known = True
    for coin, holding in HOLDINGS.items():
        amount = holding["amount"]
        row = data.get(coin) or {}
        price = row.get("eur")
        if price is None:
            log.warning("Kein EUR-Preis fuer %s", coin)
            return None
        change = row.get("eur_24h_change") or 0.0
        total += amount * price
        prev += amount * (price / (1 + change / 100))  # Wert vor 24h

        coin_cost = holding.get("cost_eur")
        if coin_cost is None:
            cost_known = False
        else:
            cost += coin_cost

    if prev <= 0:
        return None
    day_pct = (total - prev) / prev * 100
    day_eur = total - prev

    if cost_known and cost > 0:
        pl_eur = total - cost
        pl_pct = pl_eur / cost * 100
    else:
        cost = pl_eur = pl_pct = None

    return Portfolio(total, day_pct, day_eur, cost, pl_eur, pl_pct)
