"""Laedt Icon-Vorschauen, base64-kodiert sie und schreibt gallery.json fuer das Auswahl-Widget."""
import base64
import io
import json
import os

import requests
from PIL import Image

URL = "https://developer.lametric.com/content/apps/icon_thumbs/{}_icon_thumb.png"

SETS = {
    "Instagram": [3741, 33712, 8649, 44238, 46949, 1643, 64045, 147],
    "YouTube": [280, 3389, 65661, 10247],
}
CURRENT = {3741, 280}

out = []
for grp, ids in SETS.items():
    for iid in ids:
        try:
            r = requests.get(URL.format(iid), timeout=20)
            if r.status_code != 200:
                print("skip", iid, r.status_code)
                continue
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()
            out.append({"grp": grp, "id": iid, "current": iid in CURRENT, "b64": b64})
        except Exception as e:
            print("err", iid, e)

path = os.path.join(os.path.dirname(__file__), "gallery.json")
json.dump(out, open(path, "w"))
print("written", len(out), "icons; total b64 chars", sum(len(o["b64"]) for o in out))
