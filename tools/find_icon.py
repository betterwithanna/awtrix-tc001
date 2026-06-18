"""Sucht in der AWTRIX/LaMetric icons.json nach Marken-Icons und zeigt, ob
Bilddaten (base64) eingebettet sind."""
import sys

import requests

URL = "https://raw.githubusercontent.com/JackWallnerDVC/lametric-icons/main/icons.json"
data = requests.get(URL, timeout=60).json()
byid = data.get("byId", {})

sample = next(iter(byid.values()))
print("Entry-Keys:", list(sample.keys()))
print("Beispiel:", {k: (str(v)[:40] if k != "name" else v) for k, v in sample.items()})
print("---")

terms = [t.lower() for t in sys.argv[1:]] or ["instagram", "youtube", "mailchimp", "envelope", "email", "euro"]
hits = []
for e in byid.values():
    nm = (e.get("name") or "").lower()
    if any(t in nm for t in terms):
        hits.append(e)

for e in sorted(hits, key=lambda x: x.get("name", "")):
    has_img = any(k for k in e if k not in ("id", "name", "category", "type", "version"))
    print(e.get("id"), "|", e.get("name"), "|", e.get("category"), "| extra-keys:",
          [k for k in e if k not in ("id", "name", "category", "type", "version")])
print(f"\n{len(hits)} Treffer")
