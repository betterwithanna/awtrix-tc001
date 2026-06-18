"""Einmaliger Verbindungstest: lauscht auf [PREFIX]/# und published die insta-App.

AWTRIX funkt im Verbundzustand selbst Stats unter [PREFIX]/stats -> daran
erkennen wir eindeutig, ob die Uhr am Broker haengt.
"""
import json
import time

import paho.mqtt.client as mqtt

import awtrix
import config
import instagram

PREFIX = config.PREFIX
seen = {}


def on_connect(c, u, f, rc, *a):
    print("Broker-Connect rc =", rc)
    c.subscribe(f"{PREFIX}/#")


def on_message(c, u, msg):
    seen[msg.topic] = seen.get(msg.topic, 0) + 1


try:
    cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except (AttributeError, TypeError):
    cli = mqtt.Client()
cli.on_connect = on_connect
cli.on_message = on_message
cli.connect(config.MQTT_HOST, config.MQTT_PORT, 60)
cli.loop_start()

stats = instagram.get_stats()
app = awtrix.build_instagram_app(stats)
time.sleep(1)
cli.publish(f"{PREFIX}/custom/insta", json.dumps(app), qos=0, retain=True)
print("Insta-App published:", app["text"])

print("Lausche 12s auf Stats der Uhr ...")
time.sleep(12)
cli.loop_stop()
cli.disconnect()

stats_topics = [t for t in seen if t.startswith(f"{PREFIX}/stats")]
print("\nGesehene Topics:", seen if seen else "(keine)")
if stats_topics:
    print(">>> UHR IST VERBUNDEN (sendet Stats) <<<")
else:
    print(">>> KEINE Stats von der Uhr -> sie haengt NICHT am Broker (Port 1883 evtl. blockiert?) <<<")
