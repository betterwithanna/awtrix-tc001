# AWTRIX Mirror — Scriptable-Widget (iPhone, **kein Mac nötig**)

Zeigt dieselben Kennzahlen wie die Uhr auf dem iPhone-Home-/Sperrbildschirm:
**Follower + Tageszuwachs**, **100k-Ziel** (fehlend + Prognose), **Einnahmen heute**
und **Krypto** (BTC+SOL). Läuft über die kostenlose App **Scriptable** — keine
Entwickler-Tools, kein Xcode, kein 99-$-Account.

```
[GitHub-Actions-Cron, alle 15 Min]
  main.py  --set_snapshot-->  Supabase (awtrix_snapshot, 1 Zeile JSON)
                                   ^
                                   |  awtrix_get_snapshot (anon-Key)
      Scriptable-Widget  ----------+   alle ~30 Min
```

---

## 1. Supabase vorbereiten (einmalig, am PC/Handy im Browser)

1. Supabase → **SQL Editor** → Inhalt von
   [`../deploy/supabase_widget.sql`](../deploy/supabase_widget.sql) ausführen
   (legt die Snapshot-Tabelle + zwei RPCs an).
2. Schreib-Token setzen — **derselbe Wert wie das GitHub-Secret `REVENUE_TOKEN`**:
   ```sql
   insert into public.awtrix_widget_secret (name, value)
     values ('write_token', '<DEIN_REVENUE_TOKEN>')
     on conflict (name) do update set value = excluded.value;
   ```
3. Ersten Snapshot erzeugen: im GitHub **Actions**-Tab den Workflow
   *AWTRIX Instagram Push* einmal manuell starten (*Run workflow*) — oder auf den
   nächsten 15-Min-Lauf warten.
4. Test (liefert dann ein JSON mit `followers`, `revenue_today`, …):
   ```bash
   curl -s -X POST \
     -H "apikey: sb_publishable_5LSC86Vn81iJG17-eYLZkQ_mab2MtVp" \
     -H "Content-Type: application/json" \
     "https://yayfjzetdpofpcoklwrr.supabase.co/rest/v1/rpc/awtrix_get_snapshot" -d '{}'
   ```

## 2. Scriptable installieren & Skript anlegen (auf dem iPhone)

1. **Scriptable** aus dem App Store laden (gratis).
2. Scriptable öffnen → **+** (oben rechts) → das neue Skript öffnet sich.
3. Den **kompletten** Inhalt von [`AwtrixMirror.js`](AwtrixMirror.js) hineinkopieren.
   - Am einfachsten: diese Datei auf dem iPhone im Browser öffnen, alles markieren,
     kopieren, in Scriptable einfügen. (Oder per iCloud/Dateien in den
     Scriptable-Ordner legen.)
4. Oben den Namen antippen und auf **AwtrixMirror** setzen.
5. Zum Testen unten auf **▶︎ Play** tippen — es sollte eine Vorschau mit deinen
   Zahlen erscheinen. „Verbindung fehlgeschlagen“ ⇒ Schritt 1 (SQL/Token) prüfen.

## 3. Widget auf den Home-Screen legen

1. Home-Screen lang drücken → **+** → **Scriptable** suchen → Größe **Klein** oder
   **Mittel** → *Widget hinzufügen*.
2. Auf das neue (noch leere) Widget tippen → **Script** = `AwtrixMirror` wählen.
   *When Interacting* kann auf *Run Script* bleiben.
3. Fertig. Das Widget aktualisiert sich selbstständig (~alle 30 Min; iOS steuert
   die genaue Häufigkeit).

---

## Anpassen

- **Andere Farben:** Objekt `COLORS` oben im Skript (Hex-Werte identisch zu `awtrix.py`).
- **Anderes Projekt/Supabase:** `SUPABASE_URL` und `SUPABASE_KEY` oben ersetzen.
- **Weitere Kennzahl:** in `main.py` ins `snapshot`-Dict aufnehmen → im Skript in
  `buildSmall`/`buildMedium` ein `metricBlock(...)` bzw. `addValue(...)` ergänzen.
- **Refresh-Intervall:** `refreshAfterDate` in `main()`.

> URL und Key sind der **publishable** Key — öffentlich-sicher (RLS aktiv, die RPC
> gibt nur das Anzeige-JSON zurück, kein Schreibrecht). Es sind dieselben Werte,
> die bereits im GitHub-Workflow stehen.

---

### Native Alternative
Wer lieber ein echtes Swift/WidgetKit-Widget möchte (braucht Mac + Xcode), findet
das fertig unter [`../ios/`](../ios/). Beide Wege nutzen denselben Supabase-Snapshot.
