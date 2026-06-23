#!/bin/sh
# Erzeugt die Passwortdatei aus den Railway-Env-Vars (MQTT_USER/MQTT_PASS),
# damit KEINE Zugangsdaten im (oeffentlichen) Repo liegen. Dann Broker starten.
set -e

PASSWD=/mosquitto/config/passwd

if [ -n "$MQTT_USER" ] && [ -n "$MQTT_PASS" ]; then
  mosquitto_passwd -b -c "$PASSWD" "$MQTT_USER" "$MQTT_PASS"
  echo "passwd fuer Benutzer '$MQTT_USER' erzeugt"
else
  echo "WARN: MQTT_USER/MQTT_PASS nicht gesetzt -- Broker startet ohne gueltige Logins" >&2
fi

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
