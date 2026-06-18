"""Ersetzt auf der Uhr die alten .jpg-Icons durch die verlustfreien .gif:
loescht /ICONS/<name>.jpg und laedt <name>.gif hoch. LAN noetig."""
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config  # noqa: E402

IP = config.AWTRIX_IP
ICONS = os.path.join(os.path.dirname(__file__), "icons")
NAMES = ["ig", "yt", "mail", "eur"]

for n in NAMES:
    try:
        r = requests.delete(f"http://{IP}/edit", params={"path": f"/ICONS/{n}.jpg"}, timeout=20)
        print("DELETE", n + ".jpg", "->", r.status_code)
    except Exception as e:
        print("DELETE err", n, e)

for n in NAMES:
    path = os.path.join(ICONS, n + ".gif")
    with open(path, "rb") as fh:
        r = requests.post(f"http://{IP}/edit", files={"file": (f"/ICONS/{n}.gif", fh, "image/gif")}, timeout=30)
    print("UPLOAD", n + ".gif", "->", r.status_code)

r = requests.get(f"http://{IP}/list?dir=/ICONS", timeout=20)
print("ICONS auf der Uhr:", r.text)
