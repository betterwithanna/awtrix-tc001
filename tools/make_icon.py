"""Erzeugt 8x8-Icon-Kandidaten fuer AWTRIX aus dem BWA-Logo + ein gezeichnetes Blatt.

Ausgabe in tools/icons/. Previews sind 20x vergroessert (nearest) zum Anschauen.
"""
import os

from PIL import Image, ImageDraw

SRC = r"C:\Users\PC\Claude\bwa-ecosystem\platform\apps\homepage\public\logo-bwa.png"
OUT = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(OUT, exist_ok=True)

LIME = (164, 206, 78)   # Marken-Lime aus dem Logo
BLACK = (0, 0, 0)


def save(img8, name):
    img8.save(os.path.join(OUT, name + ".png"))
    big = img8.resize((160, 160), Image.NEAREST)
    big.save(os.path.join(OUT, name + "_preview.png"))


# 1) Emblem-Crop aus dem echten Logo (Figur + Blatt), auf Schwarz
logo = Image.open(SRC).convert("RGBA")
bg = Image.new("RGBA", logo.size, BLACK + (255,))
flat = Image.alpha_composite(bg, logo).convert("RGB")
emblem = flat.crop((380, 200, 690, 510))   # nur das Emblem, kein Schriftzug
save(emblem.resize((8, 8), Image.LANCZOS), "emblem")

# 2) Sauber gezeichnetes Blatt (lime auf schwarz)
leaf = Image.new("RGB", (8, 8), BLACK)
d = ImageDraw.Draw(leaf)
# Blatt-Form: Diagonale Linse von unten-links nach oben-rechts
leaf_pixels = [
    (5, 1), (6, 1),
    (4, 2), (5, 2), (6, 2),
    (3, 3), (4, 3), (5, 3), (6, 3),
    (3, 4), (4, 4), (5, 4), (6, 4),
    (2, 5), (3, 5), (4, 5), (5, 5),
    (2, 6), (3, 6), (4, 6),
    (2, 7),
]
for p in leaf_pixels:
    d.point(p, fill=LIME)
# Mittelrippe etwas dunkler
for p in [(4, 2), (4, 3), (3, 4), (3, 5)]:
    d.point(p, fill=(120, 150, 50))
save(leaf, "leaf")

print("fertig:", os.listdir(OUT))
