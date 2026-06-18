"""Erzeugt die Loop-Icons als VERLUSTFREIE GIFs (JPG zerstoert 8x8-Solidfarben).

ig  = volles helles Rot + weisse Kamera (eine Rot-Farbe)
eur = helles gruenes Eurozeichen auf schwarz
mail= weisser Briefumschlag auf blau
yt  = LaMetric 65661, frisch auf 8x8 -> gif
"""
import io
import os

import requests
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "icons")
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 80)
BLUE = (40, 120, 230)


def build(bg, pixels, fg, name):
    img = Image.new("RGB", (8, 8), bg)
    px = img.load()
    for p in pixels:
        px[p] = fg
    img.save(os.path.join(OUT, name + ".gif"), "GIF")
    img.resize((120, 120), Image.NEAREST).save(os.path.join(OUT, name + "_gifprev.png"))


CAMERA = [(2, 1), (3, 1), (4, 1), (5, 1), (2, 6), (3, 6), (4, 6), (5, 6),
          (1, 2), (1, 3), (1, 4), (1, 5), (6, 2), (6, 3), (6, 4), (6, 5),
          (3, 3), (4, 3), (3, 4), (4, 4), (5, 2)]
build(RED, CAMERA, WHITE, "ig")

EURO = [(2, 1), (3, 1), (4, 1), (1, 2), (5, 2), (1, 3), (2, 3), (3, 3), (4, 3),
        (1, 4), (1, 5), (2, 5), (3, 5), (4, 5), (1, 6), (5, 6), (2, 7), (3, 7), (4, 7)]
build(BLACK, EURO, GREEN, "eur")

MAIL = [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),
        (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
        (1, 3), (1, 4), (1, 5), (6, 3), (6, 4), (6, 5),
        (2, 3), (3, 4), (4, 4), (5, 3)]
build(BLUE, MAIL, WHITE, "mail")

try:
    r = requests.get("https://developer.lametric.com/content/apps/icon_thumbs/65661_icon_thumb.png", timeout=20)
    im = Image.open(io.BytesIO(r.content)).convert("RGB").resize((8, 8), Image.LANCZOS)
    im.save(os.path.join(OUT, "yt.gif"), "GIF")
    print("yt.gif ok")
except Exception as e:
    print("yt fetch err", e)

print("done")
