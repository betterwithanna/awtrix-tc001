"""Aussentemperatur fuer Kirchstetterngasse 7, 1160 Wien via Open-Meteo (kostenlos, kein Key)."""
import logging

import requests

log = logging.getLogger(__name__)

# Fixe Koordinaten der Adresse (einmal via Nominatim geocodet).
LAT, LON = 48.2052537, 16.3314745

_URL = "https://api.open-meteo.com/v1/forecast"


def get_temperature():
    """Aktuelle Aussentemperatur in °C (float) oder None bei Fehler."""
    try:
        resp = requests.get(_URL, params={
            "latitude": LAT, "longitude": LON,
            "current": "temperature_2m", "timezone": "Europe/Vienna",
        }, timeout=15)
        resp.raise_for_status()
        current = resp.json().get("current") or {}
    except (requests.RequestException, ValueError) as exc:
        log.warning("Temperatur nicht abrufbar: %s", exc)
        return None
    temp = current.get("temperature_2m")
    return float(temp) if temp is not None else None
