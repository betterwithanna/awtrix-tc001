"""Instagram-Datenabruf ueber die Graph API.

Unterstuetzt beide offiziellen Wege ueber den Konfig-Schalter ``IG_AUTH``:

* ``facebook``  -> Base ``https://graph.facebook.com/{ver}/{IG_USER_ID}``
                   (Token gehoert zur verknuepften Facebook-Seite)
* ``instagram`` -> Base ``https://graph.instagram.com/{ver}/{IG_USER_ID}``
                   ("Instagram API with Instagram Login", keine Page-Zwischenstufe)

Liefert ``get_stats()`` -> ``{"followers": int, "reach": int}``.
"""
import logging
import time

import requests

import config

log = logging.getLogger(__name__)


class InstagramError(RuntimeError):
    """Allgemeiner Fehler beim Instagram-Abruf."""


class TokenExpiredError(InstagramError):
    """Access-Token ist abgelaufen oder ungueltig (Graph-Error-Code 190)."""


def _base_url():
    if config.IG_AUTH == "instagram":
        host = "https://graph.instagram.com"
    else:
        host = "https://graph.facebook.com"
    return f"{host}/{config.IG_API_VERSION}/{config.IG_USER_ID}"


def _request(url, params):
    """GET mit Access-Token; uebersetzt API-Fehler in sprechende Exceptions."""
    params = {**params, "access_token": config.IG_TOKEN}
    try:
        resp = requests.get(url, params=params, timeout=20)
    except requests.RequestException as exc:
        raise InstagramError(f"Netzwerkfehler beim API-Abruf: {exc}") from exc

    if resp.status_code == 200:
        return resp.json()

    # Fehlerdetails aus der Graph-API extrahieren
    error = {}
    try:
        error = resp.json().get("error", {}) or {}
    except ValueError:
        pass
    code = error.get("code")
    message = error.get("message", resp.text)

    if code == 190:
        raise TokenExpiredError(f"Access-Token ungueltig/abgelaufen: {message}")
    if code in (4, 17, 32, 613):
        raise InstagramError(f"Rate-Limit erreicht (code {code}): {message}")
    raise InstagramError(f"API-Fehler HTTP {resp.status_code} (code {code}): {message}")


def get_followers():
    """Aktuelle Follower-Zahl."""
    data = _request(_base_url(), {"fields": "followers_count,media_count"})
    return int(data.get("followers_count", 0) or 0)


def get_reach():
    """Reichweite des aktuellen Tages (Summe). 0, falls nicht abrufbar.

    Insights sind weniger stabil als die Follower-Zahl (z. B. zu wenig Aktivitaet),
    daher wird hier defensiv 0 zurueckgegeben statt einen Fehler zu werfen.
    """
    try:
        data = _request(
            f"{_base_url()}/insights",
            {"metric": "reach", "period": "day", "metric_type": "total_value"},
        )
    except InstagramError as exc:
        log.warning("Reichweite konnte nicht geladen werden: %s", exc)
        return 0

    rows = data.get("data", [])
    if not rows:
        return 0
    total = rows[0].get("total_value", {})
    if isinstance(total, dict):
        return int(total.get("value", 0) or 0)
    return 0


def get_reach_change_pct():
    """Live-Abweichung der HEUTIGEN Reichweite gegenueber GESTERN (in %).

    Vergleicht den heutigen (noch laufenden) Tageswert direkt mit gestern.
    Hinweis: morgens stark negativ, da heute erst begonnen hat -- so gewuenscht.
    None bei zu wenig Daten.
    """
    now = int(time.time())
    try:
        data = _request(f"{_base_url()}/insights", {
            "metric": "reach", "period": "day",
            "since": now - 6 * 86400, "until": now,
        })
    except InstagramError as exc:
        log.warning("Reach-Verlauf nicht abrufbar: %s", exc)
        return None

    rows = data.get("data", [])
    if not rows:
        return None
    values = [v.get("value", 0) for v in rows[0].get("values", [])]
    if len(values) < 2:
        return None
    today, yesterday = values[-1], values[-2]
    if not yesterday:
        return None
    return round((today - yesterday) / yesterday * 100, 1)


def get_stats():
    """Holt Follower + Reichweite und gibt ein dict zurueck."""
    config.require("IG_TOKEN", "IG_USER_ID")
    followers = get_followers()
    reach = get_reach()
    log.info("Instagram: followers=%s reach=%s", followers, reach)
    return {"followers": followers, "reach": reach}
