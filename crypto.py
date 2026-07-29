"""Krypto-Portfolio (BTC + SOL + PEPE): Live-Wert in EUR via CoinGecko (kostenlos, kein Key).

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

# Bestand: Menge + netto in EUR investiert (Kostenbasis = Kaeufe inkl. Gebuehren
# minus zurueckerhaltene Verkaufserloese). Die Seit-Kauf-Rendite = Wert - cost_eur
# enthaelt damit sowohl realisierte Gewinne als auch die gratis erhaltenen
# Staking-Rewards. Bei neuem Kauf: amount += Menge, cost_eur += Menge*Preis + Gebuehr.
# Quelle: Revolut Crypto Account Statement, Stand 12.07.2026.
HOLDINGS = {
    # BTC netto investiert:
    #   Kauf 30.03.: 2000.00 + 49.79 = 2049.79
    #   Kauf 03.06.: 1250.00 + 21.12 = 1271.12
    #   Verkaeufe (netto): -(183.02 + 70.02 + 28.02) = -281.06
    #   Receive 13.07.: +0.04376399 BTC = 2437.60
    #   => 5477.45
    "bitcoin": {"amount": 0.09309061, "cost_eur": 5477.45},
    # SOL netto investiert (keine Verkaeufe; Staking-Rewards kostenlos):
    #   Kauf 30.03.: 2000.00 + 46.24 = 2046.24
    #   Kauf 03.06.: 1250.00 + 31.11 = 1281.11
    #   Receive 13.07.: +35.961572 SOL = 2437.65
    #   => 5765.00 ; Menge inkl. Staking-Rewards. Seit 13.07. ist der GESAMTE
    #   SOL-Bestand gestakt (~6.24% APY) -> Menge waechst durch Rewards weiter.
    #   Kauf 29.07.: +15.010206 SOL fuer 1000.00 (inkl. 24.90 Gebuehr)
    #   => 81.524451 + 15.010206 = 96.534657 ; 5765.00 + 1000.00 = 6765.00
    "solana": {"amount": 96.534657, "cost_eur": 6765.00},
    # PEPE (Memecoin, hochspekulativ):
    #   Receive 13.07.: 405,529,868.1386 PEPE = 984.91
    "pepe": {"amount": 405529868.1386, "cost_eur": 984.91},
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
