"""Zentrale Konfiguration.

Liest alle Einstellungen aus Umgebungsvariablen bzw. einer ``.env``-Datei
(per python-dotenv). So bleiben Tokens/Passwoerter aus dem Code heraus.

Importiere dieses Modul in den anderen Modulen und greife auf die Konstanten zu,
z. B. ``config.IG_TOKEN``.
"""
import os

from dotenv import load_dotenv

# .env laden, falls vorhanden. Bereits gesetzte echte Umgebungsvariablen
# (z. B. GitHub-Actions-Secrets oder systemd EnvironmentFile) werden NICHT
# ueberschrieben (override=False ist der Default).
load_dotenv()


def _get(name, default=None):
    val = os.getenv(name, default)
    if isinstance(val, str):
        val = val.strip()
    return val


def _get_int(name, default):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _get_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# --- Modus & AWTRIX ---------------------------------------------------------
MODE = (_get("MODE", "mqtt") or "mqtt").lower()      # "mqtt" | "http"
PREFIX = _get("PREFIX", "awtrix_anna")               # MQTT-Topic-Prefix der Uhr

# HTTP-Modus: lokale IP der Uhr
AWTRIX_IP = _get("AWTRIX_IP", "192.168.1.50")

# MQTT-Modus: Cloud-Broker
MQTT_HOST = _get("MQTT_HOST")
MQTT_PORT = _get_int("MQTT_PORT", 8883)
MQTT_USER = _get("MQTT_USER")
MQTT_PASS = _get("MQTT_PASS")
MQTT_TLS = _get_bool("MQTT_TLS", True)

# --- Instagram Graph API ----------------------------------------------------
# "facebook"  -> Base https://graph.facebook.com  (ueber verknuepfte FB-Seite)
# "instagram" -> Base https://graph.instagram.com (Instagram API with Instagram Login)
IG_AUTH = (_get("IG_AUTH", "facebook") or "facebook").lower()
IG_TOKEN = _get("IG_TOKEN")
IG_USER_ID = _get("IG_USER_ID")
IG_API_VERSION = _get("IG_API_VERSION", "v21.0")

# Optional, nur fuer die Token-Verlaengerung (refresh_token.py)
FB_APP_ID = _get("FB_APP_ID")
FB_APP_SECRET = _get("FB_APP_SECRET")

# --- Anzeige ----------------------------------------------------------------
EUR_SIGN = _get("EUR_SIGN", "EUR")     # Waehrungszeichen fuer die Einnahmen-App
IG_ICON = _get("IG_ICON", "")          # ID/Name eines hochgeladenen 8x8-Icons (optional)

# --- Weitere Datenquellen ---------------------------------------------------
# Supabase (Mailing-Kontaktzahl via RPC awtrix_contacts_count). Publishable Key
# ist oeffentlich-sicher (RLS aktiv, RPC liefert nur eine Zahl).
SUPABASE_URL = _get("SUPABASE_URL")
SUPABASE_KEY = _get("SUPABASE_KEY")


def require(*names):
    """Stellt sicher, dass die genannten Pflichtfelder gesetzt sind.

    Wirft RuntimeError mit einer klaren Meldung, wenn etwas fehlt.
    Wird zur Laufzeit (nicht beim Import) aufgerufen, damit Tests das Modul
    ohne vollstaendige .env importieren koennen.
    """
    missing = [n for n in names if not globals().get(n)]
    if missing:
        raise RuntimeError(
            "Fehlende Konfiguration: "
            + ", ".join(missing)
            + " -- bitte in der .env-Datei setzen (siehe .env.example)."
        )
