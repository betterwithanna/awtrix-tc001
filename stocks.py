"""Aktien-Portfolio (aktuell nur Moderna/MRNA), live in USD via Yahoo Finance
(kostenlos, kein Key -- inoffizieller Chart-Endpunkt).

Bestand haelt Menge + Kostenbasis in USD (Kaufwaehrung, keine FX-Umrechnung noetig).
Struktur analog zu crypto.py: Menge + Kostenbasis pro Position, bei neuem Kauf
amount += Menge, cost_usd += Menge*Kaufpreis.

``get_portfolio()`` liefert ein ``StockPortfolio``-Tupel:
    total    -- aktueller Gesamtwert in USD
    day_pct  -- Tagesveraenderung in % (regularMarketPrice vs. previousClose)
    day_usd  -- Tagesveraenderung in USD
    cost     -- insgesamt investiert (USD)
    pl_usd   -- Gewinn/Verlust seit Kauf (USD)
    pl_pct   -- Gewinn/Verlust seit Kauf (%)

None bei Fehler/fehlendem Kurs.
"""
import logging
from collections import namedtuple

import requests

log = logging.getLogger(__name__)

# Kauf 20.08.2026: 19.69439728 MRNA @ 117.80 USD = 2320.00 USD.
# Verkauf 20.08.2026 (Kapital teilweise entnommen, Rest bleibt investiert):
#   15.06852232 @ 153.97 + 0.19060317 @ 157.50 = 2350.12 USD Erloes
#   verkaufte Menge = 15.25912549 ; realisierter Gewinn = 552.60 USD
#   Kostenbasis anteilig (Durchschnittspreis 117.80/Stk.) mitverkauft:
#     1797.52 USD -> Rest-Kostenbasis = 2320.00 - 1797.52 = 522.48
# Owner-Bestaetigung (Broker-Anzeige) 20.08.2026: exakt 4.4428911388 gehalten
# (kleine Abweichung zur Berechnung 4.43527179 -- vermutlich Rundung/Gebuehr
# beim Broker). Kostenbasis unveraendert bei 522.48.
# Rest-Position komplett verkauft (20.08.2026) -> keine Aktien mehr gehalten.
# HOLDINGS leer -> get_portfolio() liefert None -> main.py entfernt das Feld.
HOLDINGS = {}

_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

StockPortfolio = namedtuple("StockPortfolio", "total day_pct day_usd cost pl_usd pl_pct")


def get_portfolio():
    """``StockPortfolio``-Tupel oder None bei Fehler/fehlendem Kurs."""
    total = prev = cost = 0.0
    for symbol, holding in HOLDINGS.items():
        try:
            resp = requests.get(_URL.format(symbol=symbol), headers=_HEADERS, timeout=15)
            resp.raise_for_status()
            meta = resp.json()["chart"]["result"][0]["meta"]
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            log.warning("Kurs fuer %s nicht abrufbar: %s", symbol, exc)
            return None

        price = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
        if price is None or not prev_close:
            log.warning("Kein Kurs/Vortagsschluss fuer %s", symbol)
            return None

        amount = holding["amount"]
        total += amount * price
        prev += amount * prev_close
        cost += holding["cost_usd"]

    if prev <= 0 or cost <= 0:
        return None

    day_usd = total - prev
    day_pct = day_usd / prev * 100
    pl_usd = total - cost
    pl_pct = pl_usd / cost * 100

    return StockPortfolio(total, day_pct, day_usd, cost, pl_usd, pl_pct)
