"""Instagram-Datenabruf ueber die Graph API.

Unterstuetzt beide offiziellen Wege ueber den Konfig-Schalter ``IG_AUTH``:

* ``facebook``  -> Base ``https://graph.facebook.com/{ver}/{IG_USER_ID}``
                   (Token gehoert zur verknuepften Facebook-Seite)
* ``instagram`` -> Base ``https://graph.instagram.com/{ver}/{IG_USER_ID}``
                   ("Instagram API with Instagram Login", keine Page-Zwischenstufe)

Liefert ``get_stats()`` -> ``{"followers": int, "reach": int}``.
"""
import datetime as dt
import logging

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


def _reach_total(since, until):
    """Reach (total_value) fuer ein Zeitfenster [since, until] (Unix-Sek.).

    None bei Fehler/keinen Daten. WICHTIG: ohne since/until liefert die API eine
    Mehrtages-Summe, nicht 'heute'. Gleiche Methode fuer heute & gestern -> Anzeige
    und %-Abweichung sind konsistent.
    """
    try:
        data = _request(f"{_base_url()}/insights", {
            "metric": "reach", "period": "day", "metric_type": "total_value",
            "since": int(since), "until": int(until),
        })
    except InstagramError as exc:
        log.warning("Reichweite konnte nicht geladen werden: %s", exc)
        return None
    rows = data.get("data", [])
    if not rows:
        return None
    total = rows[0].get("total_value", {})
    if isinstance(total, dict):
        return int(total.get("value", 0) or 0)
    return None


def _day_bounds():
    """(heute 00:00 UTC, jetzt, gestern 00:00 UTC) als Unix-Sekunden."""
    now = dt.datetime.now(dt.timezone.utc)
    today0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return today0.timestamp(), now.timestamp(), (today0 - dt.timedelta(days=1)).timestamp()


def get_reach():
    """Reichweite HEUTE (00:00 UTC -> jetzt). 0, falls nicht abrufbar."""
    today0, now, _ = _day_bounds()
    val = _reach_total(today0, now)
    return val if val is not None else 0


def get_reach_change_pct():
    """Abweichung der heutigen Reichweite gegenueber GESTERN (in %).

    Beide Werte mit derselben Methode (total_value je Tagesfenster) -> konsistent
    zur angezeigten Reach-Zahl. Morgens negativ (heute erst angefangen) -- gewollt.
    None bei zu wenig Daten.
    """
    today0, now, yest0 = _day_bounds()
    today = _reach_total(today0, now)
    yest = _reach_total(yest0, today0)
    if today is None or not yest:
        return None
    return round((today - yest) / yest * 100, 1)


def _media_views(media_id):
    """Aufrufe eines Beitrags via Insights (``views``, sonst ``reach``). None sonst.

    ``metric_type=total_value`` -> Wert steht unter ``values[0].value`` (lifetime).
    Reels haben ``views``; aeltere Bild-Posts ggf. nur ``reach`` -> Fallback.
    """
    host = _base_url().rsplit("/", 1)[0]  # .../{version} ohne IG_USER_ID
    for metric in ("views", "reach"):
        try:
            ins = _request(f"{host}/{media_id}/insights",
                           {"metric": metric, "metric_type": "total_value"})
        except InstagramError as exc:
            log.warning("Insight '%s' fuer %s fehlgeschlagen: %s", metric, media_id, exc)
            continue
        rows = ins.get("data") or []
        if rows:
            values = rows[0].get("values") or []
            if values and values[0].get("value") is not None:
                return int(values[0]["value"])
    return None


def get_last_post():
    """Neuester Beitrag/Reel mit Kennzahlen. None bei Fehler oder keinen Medien.

    Rueckgabe-dict: ``timestamp`` (aware datetime), ``product_type`` (REELS/IMAGE/…),
    ``likes``, ``comments`` (direkt am Media-Objekt) und ``views`` (via Insights).
    """
    data = _request(_base_url() + "/media", {
        "fields": "id,media_type,media_product_type,timestamp,like_count,comments_count",
        "limit": 1,
    })
    rows = data.get("data") or []
    if not rows:
        return None
    m = rows[0]
    return {
        "id": m["id"],
        "product_type": m.get("media_product_type") or m.get("media_type") or "",
        "timestamp": dt.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z"),
        "likes": int(m.get("like_count", 0) or 0),
        "comments": int(m.get("comments_count", 0) or 0),
        "views": _media_views(m["id"]),
    }


def get_stats():
    """Holt Follower + Reichweite und gibt ein dict zurueck."""
    config.require("IG_TOKEN", "IG_USER_ID")
    followers = get_followers()
    reach = get_reach()
    log.info("Instagram: followers=%s reach=%s", followers, reach)
    return {"followers": followers, "reach": reach}
