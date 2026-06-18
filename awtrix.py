"""Sendet Custom-Apps an AWTRIX 3 -- per MQTT (Cloud-Broker) oder HTTP (lokale IP).

* Bauen der App-Payloads: ``build_instagram_app`` / ``build_revenue_app``
* Versand: ``push(apps)`` waehlt anhand ``config.MODE`` den Transport.

AWTRIX-API (Auszug):
* MQTT: Topic ``[PREFIX]/custom/[name]``, Payload = JSON
* HTTP: ``POST http://[IP]/api/custom?name=[name]``, Body = JSON
"""
import json
import logging

import requests

import config

log = logging.getLogger(__name__)


class AwtrixError(RuntimeError):
    """Fehler beim Senden an die Uhr (Broker/HTTP nicht erreichbar etc.)."""


def format_number(value):
    """Tausender-Trennung mit Punkt (deutsch): ``12345`` -> ``"12.345"``."""
    return f"{int(round(value)):,}".replace(",", ".")


# --- Markenfarben -----------------------------------------------------------
IG_PINK = "#E1306C"        # Instagram
YT_RED = "#FF0033"         # YouTube
SPOTIFY_GREEN = "#1DB954"  # Spotify
MAIL_BLUE = "#4AA3FF"      # Mailing/Newsletter
HOME_LIME = "#A6E22E"      # Homepage (Marken-Lime)
REVENUE_GREEN = "#39FF14"  # Einnahmen
GROWTH_GREEN = "#2ECC40"   # Tageszuwachs (z. B. Follower heute)
DROP_RED = "#FF4136"       # negativer Wert (Rueckgang)
WHITE = "#FFFFFF"


def build_metric_app(text, color=WHITE, icon=None, scroll=True, duration=7, lifetime=2400):
    """Baut eine Custom-App fuer EINE Kennzahl (= ein Feld im Loop).

    scroll=True laesst laengeren Text laufen; scroll=False zentriert kurzen Text.
    lifetime 2400 s (40 Min) ueberbrueckt locker den 15-Min-Push-Takt.
    icon = ID/Name eines auf der Uhr vorhandenen 8x8-Icons (optional).
    """
    app = {"text": str(text), "color": color, "duration": duration, "lifetime": lifetime}
    if scroll:
        app["scrollSpeed"] = 90
    else:
        app["center"] = True
    if icon:
        app["icon"] = icon
    return app


def build_revenue_app(revenue, icon=None):
    """Einnahmen-App (gruen). ``revenue`` = Betrag in EUR (z. B. Vortag)."""
    return build_metric_app(
        f"{format_number(revenue)} {config.EUR_SIGN}", REVENUE_GREEN, icon=icon, scroll=False
    )


def build_combo_app(fragments, icon=None, duration=8, lifetime=2400):
    """Ein Feld mit mehreren FARBIGEN Textsegmenten (z. B. Zahl + Zuwachs).

    fragments = Liste von (text, farbe)-Tupeln; Farbe als Hex (mit/ohne '#').
    """
    text = [{"t": t, "c": str(c).lstrip("#")} for (t, c) in fragments]
    app = {"text": text, "scrollSpeed": 90, "duration": duration, "lifetime": lifetime}
    if icon:
        app["icon"] = icon
    return app


# --- Transport --------------------------------------------------------------

def push_http(app_name, payload):
    url = f"http://{config.AWTRIX_IP}/api/custom?name={app_name}"
    try:
        # AWTRIX kann unter Last (z. B. MQTT-Reconnect) traege antworten -> grosszuegiges Timeout
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AwtrixError(f"HTTP-Push an {url} fehlgeschlagen: {exc}") from exc
    log.info("HTTP-Push '%s' an %s ok", app_name, config.AWTRIX_IP)


def _make_mqtt_client():
    import paho.mqtt.client as mqtt

    # paho-mqtt 2.x erwartet eine Callback-API-Version; 1.x kennt sie nicht.
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except (AttributeError, TypeError):
        client = mqtt.Client()

    if config.MQTT_USER:
        client.username_pw_set(config.MQTT_USER, config.MQTT_PASS)
    if config.MQTT_TLS:
        client.tls_set()
    return client


def push_mqtt(apps):
    """Oeffnet eine Verbindung zum Broker und published alle Apps (retain=True)."""
    config.require("MQTT_HOST")
    client = _make_mqtt_client()
    try:
        client.connect(config.MQTT_HOST, config.MQTT_PORT, keepalive=60)
    except Exception as exc:  # socket-/TLS-/Auth-Fehler
        raise AwtrixError(
            f"MQTT-Broker {config.MQTT_HOST}:{config.MQTT_PORT} nicht erreichbar: {exc}"
        ) from exc

    client.loop_start()
    try:
        for name, payload in apps.items():
            topic = f"{config.PREFIX}/custom/{name}"
            info = client.publish(topic, json.dumps(payload), qos=0, retain=True)
            info.wait_for_publish(timeout=10)
            if info.rc != 0:
                raise AwtrixError(f"MQTT-Publish an {topic} fehlgeschlagen (rc={info.rc})")
            log.info("MQTT-Push '%s' an %s ok", name, topic)
    finally:
        client.loop_stop()
        client.disconnect()


def push(apps):
    """Versendet die Apps ueber den konfigurierten Modus (``config.MODE``)."""
    if config.MODE == "http":
        for name, payload in apps.items():
            push_http(name, payload)
    elif config.MODE == "mqtt":
        push_mqtt(apps)
    else:
        raise AwtrixError(f"Unbekannter MODE '{config.MODE}' (erlaubt: mqtt | http)")
