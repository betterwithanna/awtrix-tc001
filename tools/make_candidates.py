"""Erzeugt eigene 8x8-Icon-Varianten (Instagram/YouTube), speichert je eine
cand_<label>.jpg (8x8, fuer den spaeteren Upload) und schreibt gallery.json
(64x64-Vorschau als base64) fuer das Auswahl-Widget."""
import base64
import io
import json
import os

from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "icons")
W = (255, 255, 255)
PINK = (225, 48, 108)
PURPLE = (131, 58, 180)
ORANGE = (253, 120, 52)
YTRED = (255, 0, 40)
BLACK = (0, 0, 0)

CAMERA = [  # weisse Pixel: Rahmen + Linse + Blitz-Punkt
    (2, 1), (3, 1), (4, 1), (5, 1), (2, 6), (3, 6), (4, 6), (5, 6),
    (1, 2), (1, 3), (1, 4), (1, 5), (6, 2), (6, 3), (6, 4), (6, 5),
    (3, 3), (4, 3), (3, 4), (4, 4), (5, 2),
]
PLAY = [(3, 2), (3, 3), (4, 3), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5), (3, 6)]
PLAY_BOLD = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (2, 4), (3, 4), (4, 4), (5, 4),
             (2, 5), (3, 5), (4, 5), (2, 6), (3, 6)]


def grad(x, y):
    t = (x + y) / 14.0
    if t < 0.5:
        a, b, k = PURPLE, PINK, t * 2
    else:
        a, b, k = PINK, ORANGE, (t - 0.5) * 2
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def build(bg, marks, fg=W, gradient=False):
    img = Image.new("RGB", (8, 8))
    px = img.load()
    for y in range(8):
        for x in range(8):
            px[x, y] = grad(x, y) if gradient else bg
    for p in marks:
        px[p] = fg
    return img


def save(img, label):
    img.save(os.path.join(OUT, f"cand_{label}.jpg"), quality=95)
    big = img.resize((64, 64), Image.NEAREST)
    buf = io.BytesIO()
    big.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def from_current(name):
    img = Image.open(os.path.join(OUT, name)).convert("RGB")
    big = img.resize((64, 64), Image.NEAREST)
    buf = io.BytesIO()
    big.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


cands = [
    {"grp": "Instagram", "label": "ig_current", "title": "Aktuell (LaMetric)", "current": True,
     "b64": from_current("ig.jpg")},
    {"grp": "Instagram", "label": "ig_pink", "title": "Pink Kamera",
     "b64": save(build(PINK, CAMERA), "ig_pink")},
    {"grp": "Instagram", "label": "ig_grad", "title": "Verlauf Kamera",
     "b64": save(build(None, CAMERA, gradient=True), "ig_grad")},
    {"grp": "Instagram", "label": "ig_white", "title": "Weiss / dunkel",
     "b64": save(build(BLACK, CAMERA), "ig_white")},
    {"grp": "YouTube", "label": "yt_current", "title": "Aktuell (LaMetric)", "current": True,
     "b64": from_current("yt.jpg")},
    {"grp": "YouTube", "label": "yt_play", "title": "Play schlank",
     "b64": save(build(YTRED, PLAY), "yt_play")},
    {"grp": "YouTube", "label": "yt_bold", "title": "Play kraeftig",
     "b64": save(build(YTRED, PLAY_BOLD), "yt_bold")},
]

json.dump(cands, open(os.path.join(os.path.dirname(__file__), "gallery.json"), "w"))
print("ok", len(cands), "Kandidaten; b64-Summe", sum(len(c["b64"]) for c in cands))
