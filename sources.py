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


def get_youtube_subscribers():
    """Abonnentenzahl des YouTube-Kanals (Data API v3, oeffentliche Statistik)."""
    if not (config.YT_API_KEY and config.YT_CHANNEL_ID):
        return None
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "statistics", "id": config.YT_CHANNEL_ID, "key": config.YT_API_KEY},
            timeout=20,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None
        stats = items[0].get("statistics", {})
        if stats.get("hiddenSubscriberCount"):
            return None
        return int(stats.get("subscriberCount", 0))
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        log.warning("YouTube-Abruf fehlgeschlagen: %s", exc)
        return None


def get_revenue_yesterday():
    """Einnahmen des Vortags (EUR) aus dem Supabase-Spiegel (RPC awtrix_get_metric).

    Wird lokal von tools/push_revenue.py befuellt. None = noch kein Wert da.
    """
    if not (config.SUPABASE_URL and config.SUPABASE_KEY):
        return None
    url = f"{config.SUPABASE_URL}/rest/v1/rpc/awtrix_get_metric"
    try:
        resp = requests.post(
            url,
            headers={
                "apikey": config.SUPABASE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            json={"p_key": "revenue_eur_yesterday"},
            timeout=20,
        )
        resp.raise_for_status()
        value = resp.json()
        return float(value) if value is not None else None
    except (requests.RequestException, ValueError, TypeError) as exc:
        log.warning("Einnahmen-Abruf (Supabase) fehlgeschlagen: %s", exc)
        return None


def _daily_delta(key, current):
    """Tageszuwachs einer Kennzahl seit Tagesbeginn (Wiener Zeit) via Supabase-RPC.

    Der Server merkt sich den Startwert des Tages unter '<key>_daystart' und
    liefert (aktuell - Start). Braucht den Schreib-Token (REVENUE_TOKEN).
    None, wenn nicht konfiguriert oder bei Fehler.
    """
    if not (config.SUPABASE_URL and config.SUPABASE_KEY and config.REVENUE_TOKEN):
        return None
    url = f"{config.SUPABASE_URL}/rest/v1/rpc/awtrix_daily_delta"
    try:
        resp = requests.post(
            url,
            headers={
                "apikey": config.SUPABASE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            json={"p_key": key, "p_current": int(current), "p_token": config.REVENUE_TOKEN},
            timeout=20,
        )
        resp.raise_for_status()
        value = resp.json()
        return int(value) if value is not None else None
    except (requests.RequestException, ValueError, TypeError) as exc:
        log.warning("Tageszuwachs '%s' (Supabase) fehlgeschlagen: %s", key, exc)
        return None


def get_follower_delta(current):
    """Follower-Zuwachs seit Tagesbeginn."""
    return _daily_delta("ig_followers", current)


def get_mailing_delta(current):
    """Neue Mailing-Kontakte seit Tagesbeginn."""
    return _daily_delta("mailing", current)
