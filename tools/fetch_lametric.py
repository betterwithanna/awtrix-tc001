"""Laedt LaMetric/AWTRIX-Icons per ID herunter, prueft Groesse und speichert Vorschau."""
import io
import os
import sys

import requests
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(OUT, exist_ok=True)

# name -> LaMetric Icon-ID (per Argument ueberschreibbar: name=id name=id ...)
IDS = {"yt": 5029}
for arg in sys.argv[1:]:
    if "=" in arg:
        k, v = arg.split("=", 1)
        IDS[k] = int(v)

URL = "https://developer.lametric.com/content/apps/icon_thumbs/{}_icon_thumb.png"

for name, iid in IDS.items():
    url = URL.format(iid)
    try:
        r = requests.get(url, timeout=20)
    except Exception as e:
        print(name, iid, "ERR", e)
        continue
    print(name, iid, "HTTP", r.status_code, r.headers.get("content-type"), len(r.content), "bytes")
    if r.status_code != 200 or not r.content:
        continue
    try:
        im = Image.open(io.BytesIO(r.content))
        frames = getattr(im, "n_frames", 1)
        print("   ", im.size, im.format, "frames:", frames)
        im.convert("RGB").resize((160, 160), Image.NEAREST).save(
            os.path.join(OUT, f"lam_{name}_{iid}_preview.png"))
        # 8x8-Version (erste Frame) fuer den Upload
        im.convert("RGB").resize((8, 8), Image.LANCZOS).save(
            os.path.join(OUT, f"lam_{name}_{iid}.jpg"), quality=95)
    except Exception as e:
        print("    kein Bild:", e)
