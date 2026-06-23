#!/bin/sh
# Erzeugt die Passwortdatei aus den Railway-Env-Vars (MQTT_USER/MQTT_PASS),
# damit KEINE Zugangsdaten im (oeffentlichen) Repo liegen. Dann Broker starten.
set -e

PASSWD=/mosquitto/config/passwd

if [ -n "$MQTT_USER" ] && [ -n "$MQTT_PASS" ]; then
  mosquitto_passwd -b -c "$PASSWD" "$MQTT_USER" "$MQTT_PASS"
  # Mosquitto laeuft als User 'mosquitto' (drop von root). Die als root erzeugte
  # Datei muss diesem User gehoeren + lesbar sein, sonst "Unable to open pwfile".
  chown mosquitto:mosquitto "$PASSWD" 2>/dev/null || true
  chmod 0640 "$PASSWD"
  echo "passwd fuer Benutzer '$MQTT_USER' erzeugt"
else
  echo "FEHLER: MQTT_USER/MQTT_PASS nicht gesetzt -- in den Railway-Variables setzen!" >&2
  exit 1
fi

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
