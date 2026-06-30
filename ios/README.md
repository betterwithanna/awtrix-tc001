# AWTRIX Mirror — iOS-Widget

Spiegelt die wichtigsten Kennzahlen der TC001-Uhr als **natives WidgetKit-Widget**
auf den iPhone-Home- und Sperrbildschirm:

- **Follower** + Tageszuwachs (Instagram-Pink, grün/rot)
- **100k-Ziel** — fehlende Follower + Prognosedatum
- **Einnahmen heute** + **Krypto-Portfolio** (BTC+SOL) mit Tages-%

```
[GitHub-Actions-Cron, alle 15 Min]
  main.py  --set_snapshot-->  Supabase (awtrix_snapshot, 1 Zeile JSON)
                                   ^
                                   | awtrix_get_snapshot (anon-Key)
            iPhone-Widget  --------+   alle ~30 Min
```

Die Uhr und das Widget lesen aus derselben Quelle, daher zeigen sie immer dasselbe.

---

## Voraussetzungen (wichtig — native Route)

Ein natives Widget lässt sich **nur auf einem Mac mit Xcode bauen**:

- **macOS + Xcode 15+** (kostenlos im App Store); Ziel-iPhone mit **iOS 17+**
- Eine **Apple-ID** zum Signieren. Mit einer kostenlosen Apple-ID läuft die App
  **7 Tage**, danach muss sie neu auf das iPhone geschoben werden. Mit einem
  **Apple-Developer-Account (99 $/Jahr)** läuft sie dauerhaft.
- Ein **iPhone** (Widgets laufen nicht zuverlässig im Simulator) per Kabel.
- **XcodeGen** (`brew install xcodegen`) — erzeugt das Xcode-Projekt aus `project.yml`.

> Kein Mac? Dann ist dieses Verzeichnis für dich nicht nutzbar — der Code ist
> fertig, aber das Bauen/Installieren geht nur über Xcode. Eine Mac-freie
> Alternative wäre die App **Scriptable** gewesen (sag Bescheid, dann baue ich die).

---

## 1. Supabase vorbereiten (einmalig, ohne Mac)

Die Daten kommen aus deinem bestehenden Supabase-Projekt.

1. Supabase → **SQL Editor** → Inhalt von [`../deploy/supabase_widget.sql`](../deploy/supabase_widget.sql)
   ausführen. Das legt die Snapshot-Tabelle und die zwei RPCs an.
2. Im selben Editor den Schreib-Token setzen (**denselben Wert wie das
   GitHub-Secret `REVENUE_TOKEN`**):
   ```sql
   insert into public.awtrix_widget_secret (name, value)
     values ('write_token', '<DEIN_REVENUE_TOKEN>')
     on conflict (name) do update set value = excluded.value;
   ```
3. Fertig — beim nächsten Cron-Lauf (oder *Run workflow* im Actions-Tab) schreibt
   `main.py` den ersten Snapshot. Test:
   ```bash
   curl -s -X POST \
     -H "apikey: sb_publishable_5LSC86Vn81iJG17-eYLZkQ_mab2MtVp" \
     -H "Content-Type: application/json" \
     "https://yayfjzetdpofpcoklwrr.supabase.co/rest/v1/rpc/awtrix_get_snapshot" -d '{}'
   ```
   Erwartet: ein JSON mit `followers`, `goal_missing`, `revenue_today`, … .

> URL und `apikey` sind der **publishable** Key — öffentlich-sicher (RLS aktiv,
> die RPC gibt nur das Anzeige-JSON zurück). Sie stehen bereits im
> GitHub-Workflow. Bei einem anderen Projekt beide Werte in
> `Sources/Shared/Config.swift` anpassen.

## 2. Xcode-Projekt erzeugen & bauen (am Mac)

```bash
cd ios
xcodegen generate           # erzeugt AwtrixMirror.xcodeproj
open AwtrixMirror.xcodeproj
```

In Xcode:

1. Target **AwtrixMirror** → *Signing & Capabilities* → dein **Team** wählen
   (Apple-ID genügt). Dasselbe für das Target **AwtrixWidgetExtension**.
   - Falls der Bundle-Identifier kollidiert: in `project.yml` `bundleIdPrefix`
     bzw. die `PRODUCT_BUNDLE_IDENTIFIER` auf etwas Eindeutiges ändern und
     `xcodegen generate` erneut laufen lassen.
2. iPhone per Kabel anschließen, oben als Ziel auswählen, **Run** (⌘R).
3. Beim ersten Start am iPhone unter *Einstellungen → Allgemein → VPN & Geräte­
   verwaltung* dem Entwickler vertrauen.

## 3. Widget aufs Home-Screen legen

Home-Screen lang drücken → **+** → „AWTRIX Mirror“ suchen → Größe **Klein** oder
**Mittel** wählen → hinzufügen. Das Widget aktualisiert sich selbstständig
(~alle 30 Min; iOS budgetiert die Häufigkeit).

---

## Struktur

| Pfad | Zweck |
| --- | --- |
| `project.yml` | XcodeGen-Spec (zwei Targets: App + Widget-Extension) |
| `Sources/Shared/` | Geteilt: Datenmodell, Supabase-Abruf, Farben, Formatierung |
| `Sources/App/` | Begleit-App (zeigt dieselben Werte, Verbindungstest) |
| `Sources/Widget/` | WidgetKit-Extension (klein + mittel) |

Geteilte Quellen liegen bewusst in **beiden** Targets (`Sources/Shared`), damit
App und Widget denselben Code nutzen.

## Anpassen

- **Andere Kennzahlen anzeigen:** Feld in `main.py` zum `snapshot`-Dict
  hinzufügen → in `Snapshot.swift` ergänzen → in der View darstellen.
- **Farben:** `Sources/Shared/Theme.swift` (identisch zu `awtrix.py`).
- **Refresh-Intervall:** `getTimeline(...)` in `AwtrixWidget.swift`.
