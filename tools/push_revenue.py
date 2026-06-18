"""Lokales Tages-Skript: Netto-Einnahmen des Vortags in EUR berechnen und in den
Supabase-Spiegel schreiben (RPC awtrix_set_metric).

Laeuft auf dem PC, wo einnahmen.json liegt -- idealerweise taeglich nach dem
'einnahmen-daily-update' (08:00). Braucht in der .env: SUPABASE_URL, SUPABASE_KEY,
REVENUE_TOKEN.

Quellen: T-Bank (net, RUB -> EUR) + PayPal (EUR direkt, RUB umgerechnet).
RUB->EUR via open.er-api.com (gratis; EZB/Frankfurter fuehren RUB nicht mehr).
"""
import json
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config  # noqa: E402

EINNAHMEN = r"D:\OneDrive\Dokumente\Claude\Projects\FinanceAgent\data_store\einnahmen\einnahmen.json"


def rub_to_eur():
    data = requests.get("https://open.er-api.com/v6/latest/RUB", timeout=20).json()
    return float(data["rates"]["EUR"])


def revenue_eur_for(data, day):
    """Summiert Netto-Einnahmen fuer ein Datum (YYYY-MM-DD) in EUR."""
    rate = rub_to_eur()
    total = 0.0
    for row in data.get("tbank", []):
        if row.get("date") == day:
            total += float(row.get("net", 0)) * rate
    for pay in data.get("paypal", []):
        if pay.get("date") == day:
            amount = float(pay.get("amount", 0))
            currency = (pay.get("currency") or "EUR").upper()
            total += amount if currency == "EUR" else amount * (rate if currency == "RUB" else 1)
    return round(total, 2)


def latest_day(data):
    """Juengstes Datum mit Einnahmen. RU-Register kommen verzoegert/gebuendelt,
    daher ist 'gestern' oft noch leer -- der letzte erfasste Tag ist aussagekraeftiger.
    """
    dates = [r["date"] for r in data.get("tbank", []) if r.get("date")]
    dates += [p["date"] for p in data.get("paypal", []) if p.get("date")]
    return max(dates) if dates else None


def main():
    with open(EINNAHMEN, encoding="utf-8") as fh:
        data = json.load(fh)
    day = latest_day(data)
    if not day:
        print("Keine Einnahmen-Daten gefunden.")
        return
    value = revenue_eur_for(data, day)
    print(f"Einnahmen {day}: {value} EUR")

    key = config.SUPABASE_KEY
    resp = requests.post(
        f"{config.SUPABASE_URL}/rest/v1/rpc/awtrix_set_metric",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"p_key": "revenue_eur_yesterday", "p_value": value, "p_token": config.REVENUE_TOKEN},
        timeout=20,
    )
    print("Supabase SET ->", resp.status_code)
    resp.raise_for_status()


if __name__ == "__main__":
    main()
