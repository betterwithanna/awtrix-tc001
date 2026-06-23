# Privater MQTT-Broker (Mosquitto) fuer die AWTRIX-Uhr

Ersetzt den oeffentlichen `broker.emqx.io`, der Clients still rauswirft und so
das Display einfriert. Laeuft als eigener Railway-Service im BWA-Projekt
(`ravishing-curiosity`) -- isoliert neben blog/bot/platform.

## Railway-Deploy (Dashboard)

1. Im Projekt **ravishing-curiosity** → **New** → **GitHub Repo** →
   `betterwithanna/awtrix-tc001`.
2. Service **Settings → Root Directory** = `broker` (nur dieser Ordner wird
   gebaut → Dockerfile hier).
3. **Variables** setzen:
   - `MQTT_USER` = z. B. `awtrix`
   - `MQTT_PASS` = ein kurzes, starkes Passwort (z. B. 16 Zeichen, KEIN langes Token)
4. **Settings → Networking → TCP Proxy** aktivieren, **Target Port = 1883**.
   Railway vergibt eine Adresse wie `xxx.proxy.rlwy.net` + einen externen Port.
5. (Optional) **Volume** an `/mosquitto/data` mounten → Retained Messages
   ueberleben Neustarts. Ohne Volume kein Problem: der Cron pusht alle ~10 Min
   mit retain=true neu.

## Danach

- Uhr (`192.168.8.34` → Settings → MQTT): Host = Proxy-Domain, Port = externer
  Port, User/Pass wie oben, KEIN TLS. Speichern.
- Cron (`.github/workflows/awtrix-push.yml`): `MQTT_HOST`/`MQTT_PORT` auf den
  Proxy setzen, `MQTT_USER`/`MQTT_PASS` als GitHub-Secrets. `PREFIX` bleibt.

Auth: keine Secrets im Repo -- der Entrypoint baut die Passwortdatei zur
Laufzeit aus `MQTT_USER`/`MQTT_PASS`.
