"""Laedt alle 8x8-Icons aus tools/icons/ auf die Uhr (AWTRIX /edit -> /ICONS/).

Muss im selben WLAN wie die Uhr laufen. IP kommt aus der .env (AWTRIX_IP).
Aufruf:  python tools/upload_icons.py
"""
import glob
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config  # noqa: E402

ICONS = os.path.join(os.path.dirname(__file__), "icons")


def main():
    files = sorted(glob.glob(os.path.join(ICONS, "*.jpg")))
    if not files:
        print("Keine Icons in", ICONS)
        return
    for path in files:
        name = os.path.basename(path)
        with open(path, "rb") as fh:
            resp = requests.post(
                f"http://{config.AWTRIX_IP}/edit",
                files={"file": (f"/ICONS/{name}", fh, "image/jpeg")},
                timeout=30,
            )
        print(f"{name} -> {resp.status_code}")


if __name__ == "__main__":
    main()
