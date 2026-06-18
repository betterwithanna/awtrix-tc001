# AWTRIX TC001 — Instagram-Dashboard

Zeigt Annas Instagram-Kennzahlen (**Follower + Reichweite**) automatisch auf einer
**Ulanzi TC001** (32×8-Pixel-Display, Firmware **AWTRIX 3**) an — **ohne dauerlaufenden PC**.

AWTRIX 3 ist eine reine Anzeige-Firmware: sie ruft keine APIs selbst ab. Ein kleiner
geplanter Job holt die Zahlen von der Instagram Graph API und schickt sie als „Custom App"
an die Uhr — entweder über einen Cloud-MQTT-Broker (ohne PC) oder per HTTP direkt an die Uhr.

```
[Scheduler (GitHub Actions / Raspberry Pi)]   --push-->   [MQTT-Broker / Uhr-IP]   -->   [TC001: App "insta"]
   alle 15 Min: IG Graph API abrufen
```

---

## Projektstruktur

| Datei | Zweck |
| --- | --- |
| `config.py` | Liest alle Einstellungen aus `.env` / Umgebungsvariablen |
| `instagram.py` | Datenabruf über die Graph API (`facebook`- **oder** `instagram`-Auth) |
| `awtrix.py` | App-Payloads bauen + Versand per MQTT/HTTP |
| `main.py` | Orchestrierung (`python main.py`) |
| `refresh_token.py` | Access-Token verlängern/tauschen |
| `tests/` | Unit-Tests (gemockt, keine echten API-Calls) |
| `.github/workflows/` | GitHub-Actions-Cron (Push) + Tests |
| `deploy/` | systemd-Service + Timer und cron-Beispiel für Raspberry Pi |
| `.env.example` | Vorlage für die Konfiguration |

---

## 1. Setup (lokal / zum Testen)

```bash
# 1) Abhängigkeiten
pip install -r requirements.txt

# 2) Konfiguration
cp .env.example .env        # Windows: copy .env.example .env
#   .env öffnen und Werte eintragen (siehe unten)

# 3) Lauf
python main.py
```

Erfolg = im Loop der Uhr taucht eine App **`insta`** mit Follower-Zahl + Reichweite in
Instagram-Pink auf.

---

## 2. Konfiguration (`.env`)

| Feld | Beschreibung |
| --- | --- |
| `MODE` | `mqtt` (über Cloud-Broker, ohne PC) oder `http` (lokal an die Uhr-IP) |
| `PREFIX` | MQTT-Prefix, wie im AWTRIX-Webinterface eingestellt (z. B. `awtrix_anna`) |
| `AWTRIX_IP` | IP der Uhr — nur für `MODE=http` |
| `MQTT_HOST/PORT/USER/PASS/TLS` | Cloud-Broker-Zugang — nur für `MODE=mqtt` |
| `IG_AUTH` | `facebook` (über FB-Seite) oder `instagram` (Instagram API with Instagram Login) |
| `IG_TOKEN` | Long-Lived Access-Token |
| `IG_USER_ID` | Instagram-Business-Account-ID |
| `IG_API_VERSION` | Graph-API-Version (Default `v21.0`) |
| `EUR_SIGN`, `IG_ICON` | Anzeige-Optionen (Währungszeichen, optionale Icon-ID) |
| `FB_APP_ID`, `FB_APP_SECRET` | Nur für `refresh_token.py` |

> **Secrets niemals committen.** `.env` ist in `.gitignore`. In der Cloud werden die Werte
> als GitHub-Secrets gesetzt (siehe unten).

### Instagram-Token & Account-ID besorgen
**Empfohlen (genutzt): Instagram Login → `IG_AUTH=instagram`.**
1. IG ist **Business/Creator-Konto**.
2. Im [Meta-Developer-Portal](https://developers.facebook.com) App mit Use-Case
   *Manage messaging & content on Instagram* anlegen → **API setup with Instagram login**.
3. Permissions: `instagram_business_basic` + **`instagram_business_manage_insights`**
   (Letzteres ist Pflicht für die Reichweite!).
4. Eigenes IG-Konto unter **App roles → Roles → Instagram Testers** hinzufügen und die
   Einladung in der Instagram-App annehmen.
5. **„Generate token"** → liefert direkt einen **langlebigen** Token (~60 Tage). Die
   angezeigte **Instagram-User-ID** ist `IG_USER_ID`.

> Alternative *Facebook Login* (`IG_AUTH=facebook`): App + verknüpfte FB-Seite, Scopes
> `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`;
> Account-ID via `GET /me/accounts` → Page-ID → `GET /{page-id}?fields=instagram_business_account`.

---

## 3. Token verlängern

Long-Lived Tokens gelten ~60 Tage und müssen erneuert werden.

```bash
python refresh_token.py                 # verlängert den aktuellen IG_TOKEN
python refresh_token.py <short_token>   # tauscht einen Short-Lived -> Long-Lived
```

Das Skript loggt das neue Ablaufdatum und gibt den neuen Token auf stdout aus.
Diesen anschließend als `IG_TOKEN` in `.env` bzw. im GitHub-Secret `IG_TOKEN` eintragen.

- `IG_AUTH=instagram`: Verlängern (ohne Argument) braucht **nur den Token** — kein App-Secret.
- `IG_AUTH=facebook` **oder** Short→Long-Tausch: braucht `FB_APP_ID`/`FB_APP_SECRET`.

### Automatisch (GitHub Actions) — wartungsfrei
Der Workflow `.github/workflows/refresh-token.yml` erneuert den Token **monatlich**
selbst und schreibt ihn zurück ins Secret `IG_TOKEN`. Einmalig nötig:
1. GitHub → **Settings → Developer settings → Fine-grained personal access tokens** →
   neues Token, **Repository access** = nur `awtrix-tc001`, **Permissions →
   Secrets = Read and write**.
2. Dieses Token im Repo als Secret **`GH_PAT`** hinterlegen.

Danach läuft die Erneuerung vollautomatisch (manuell testbar via *Run workflow*).

---

## 4. Deployment

### Variante A — GitHub Actions (Cloud, ohne PC) → nur `MODE=mqtt`
1. Repo zu GitHub pushen (**öffentlich** = unbegrenzte Actions-Minuten; alle Geheimnisse
   liegen als Secrets, also nicht im Code).
2. Unter **Settings → Secrets and variables → Actions** anlegen:
   `IG_TOKEN`, `IG_USER_ID`, `MQTT_PREFIX`.
   (Nicht-geheime Defaults — Broker `broker.emqx.io`, Port `1883`, `IG_AUTH=instagram` — stehen
   direkt im Workflow `.github/workflows/awtrix-push.yml`.)
3. Der Workflow läuft alle 15 Min (Cron, UTC) und kann im **Actions**-Tab manuell gestartet
   werden (*Run workflow*).

> **Broker-Wahl (wichtig):** AWTRIX 0.98 kann **kein MQTT-over-TLS** (→ HiveMQ Cloud scheidet
> aus) und hat ein **zu kurzes Username-Feld** für lange Tokens (→ flespi scheidet aus).
> Deshalb der öffentliche Broker **`broker.emqx.io:1883`** (kein TLS, kein Login). Schutz:
> ein **nicht erratbarer `PREFIX`** (liegt als Secret), damit niemand mitliest oder auf die
> Uhr schreibt.

> GitHub-Actions-Cron läuft nur auf dem **Default-Branch**. Der HTTP-Modus erreicht die Uhr
> im Heim-WLAN nicht — in der Cloud also immer `mqtt`. Hinweis: Bei öffentlichen Repos werden
> geplante Workflows nach 60 Tagen ohne Repo-Aktivität pausiert.

### Variante B — Raspberry Pi (eigenes Always-on-Gerät) → `mqtt` *oder* `http`
```bash
git clone <repo> /home/pi/awtrix-tc001
cd /home/pi/awtrix-tc001
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # ausfüllen (im selben WLAN ist MODE=http möglich)
```

**systemd-Timer** (empfohlen):
```bash
sudo cp deploy/awtrix-push.service /etc/systemd/system/
sudo cp deploy/awtrix-push.timer   /etc/systemd/system/
# Pfade in der .service ggf. anpassen
sudo systemctl daemon-reload
sudo systemctl enable --now awtrix-push.timer
systemctl list-timers awtrix-push.timer    # Kontrolle
journalctl -u awtrix-push.service -f       # Logs
```

**oder klassischer cron** — siehe `deploy/crontab.example`.

---

## 5. Icons (8×8)
Die gebrandeten 8×8-Icons liegen unter `tools/icons/` — Logo-Blatt `bwa`, Instagram `ig`,
YouTube `yt`, Mailing `mail` — und werden in `main.py` per Dateiname referenziert
(`icon="ig"` usw.).

- **Neu generieren:** `python tools/make_icon.py` (Logo-Blatt) bzw. `python tools/make_glyphs.py`.
- **Auf die Uhr laden** (im selben WLAN): `python tools/upload_icons.py` → landet in `/ICONS/`.
- Icons sind **geräte-lokal**: nach einem Neuflash der Uhr einmal neu hochladen.
- Alternativ in der Uhr unter **Icons** ein [LaMetric-Icon](https://developer.lametric.com/icons)
  per ID laden und den Namen in `main.py` setzen.

### Native Apps ausblenden (Temperatur/Luftfeuchte/Akku/Datum)
Per Settings abschalten — **wirkt erst nach einem Reboot** der Uhr:
```bash
curl -X POST http://<IP>/api/settings -H "Content-Type: application/json" \
     -d '{"TEMP":false,"HUM":false,"BAT":false,"DAT":false,"TIM":true}'
curl -X POST http://<IP>/api/reboot
```
Es bleibt nur die native Uhrzeit (`TIM`) + die Custom-Apps. Geräte-lokal: nach
einem Neuflash erneut setzen.

---

## 6. Tests
```bash
pip install -r requirements-dev.txt
pytest -q
```
Die Tests mocken alle Netzwerk-Calls und prüfen die Formatierungs-/Build-Funktionen sowie
die Fehlerbehandlung (abgelaufener Token, Rate-Limit, Reichweite nicht abrufbar).

---

## 7. Später: Einnahmen-App
Die Architektur ist auf eine zweite App `revenue` vorbereitet:
`awtrix.build_revenue_app()` existiert bereits, und in `main.py` ist die Einbindung als
Kommentar markiert. Sobald die Einnahmen-Quelle (URL/Datei/Anbieter) feststeht, nur die
Daten holen und `apps["revenue"] = awtrix.build_revenue_app(wert)` ergänzen.
