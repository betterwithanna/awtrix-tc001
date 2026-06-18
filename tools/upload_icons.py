"""Laedt alle 8x8-Icons aus tools/icons/ auf die Uhr (AWTRIX /edit -> /ICONS/).

Muss im selben WLAN wie die Uhr laufen. IP kommt aus der .env (AWTRIX_IP).
Aufruf:  python tools/upload_icons.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config  # noqa: E402

ICONS = os.path.join(os.path.dirname(__file__), "icons")
# Nur die echten Loop-Icons hochladen (keine Test-Kandidaten).
ICON_NAMES = ["ig", "yt", "mail", "eur"]


def main():
    for name in [f"{n}.gif" for n in ICON_NAMES]:
        path = os.path.join(ICONS, name)
        if not os.path.exists(path):
            print("fehlt:", name)
            continue
        with open(path, "rb") as fh:
            resp = requests.post(
                f"http://{config.AWTRIX_IP}/edit",
                files={"file": (f"/ICONS/{name}", fh, "image/gif")},
                timeout=30,
            )
        print(f"{name} -> {resp.status_code}")


if __name__ == "__main__":
    main()
