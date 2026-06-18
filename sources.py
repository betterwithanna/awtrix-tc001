"""Zusatz-Datenquellen fuer das Dashboard (alles ausser Instagram).

Konvention: jede Funktion liefert eine Zahl ODER None.
None = Quelle nicht konfiguriert oder Abruf fehlgeschlagen -> das Feld wird im
Loop einfach uebersprungen, ohne den ganzen Push zu kippen.
"""
import logging

import requests

import config

log = logging.getLogger(__name__)


def get_mailing_count():
    """Anzahl E-Mail-Kontakte aus Supabase (RPC ``awtrix_contacts_count``)."""
    if not (config.SUPABASE_URL and config.SUPABASE_KEY):
        return None
    url = f"{config.SUPABASE_URL}/rest/v1/rpc/awtrix_contacts_count"
    try:
        resp = requests.post(
            url,
            headers={
                "apikey": config.SUPABASE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            json={},
            timeout=20,
        )
        resp.raise_for_status()
        return int(resp.json())
    except (requests.RequestException, ValueError, TypeError) as exc:
        log.warning("Mailing-Abruf (Supabase) fehlgeschlagen: %s", exc)
        return None
