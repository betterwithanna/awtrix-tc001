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


def build_instagram_app(stats):
    """Baut die ``insta``-App: Follower-Zahl + Reichweite in Instagram-Pink."""
    followers = format_number(stats.get("followers", 0))
    reach = format_number(stats.get("reach", 0))
    app = {
        "text": f"{followers}  R {reach}",
        "color": "#E1306C",            # Instagram-Pink
        "scrollSpeed": 90,
        "duration": 8,
        "lifetime": 1800,              # verschwindet, wenn 30 Min kein Update kommt
    }
    if config.IG_ICON:
        app["icon"] = config.IG_ICON
    return app


def build_revenue_app(revenue):
    """Baut die ``revenue``-App (Einnahmen). Bewusst schon vorbereitet -- noch ungenutzt."""
    return {
        "text": f"{format_number(revenue)} {config.EUR_SIGN}",
        "color": "#39FF14",            # Gruen
        "center": True,
        "duration": 8,
        "lifetime": 1800,
    }


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
