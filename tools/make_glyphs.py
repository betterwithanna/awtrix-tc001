"""Erzeugt 8x8-Marken-Glyphen (Instagram, YouTube, Mailing) fuer AWTRIX."""
import os

from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(OUT, exist_ok=True)

W = (255, 255, 255)


def make(name, bg, white_pixels, accent=None, accent_pixels=()):
    img = Image.new("RGB", (8, 8), bg)
    px = img.load()
    for (x, y) in white_pixels:
        px[x, y] = W
    for (x, y) in accent_pixels:
        px[x, y] = accent
    img.save(os.path.join(OUT, name + ".jpg"), quality=95)
    img.resize((160, 160), Image.NEAREST).save(os.path.join(OUT, name + "_preview.png"))


# Instagram: pink, weisser Kamera-"Lens"-Ring + Punkt oben rechts
make("ig", (225, 48, 108),
     white_pixels=[(3, 2), (4, 2), (2, 3), (5, 3), (2, 4), (5, 4), (3, 5), (4, 5), (6, 1)])

# YouTube: rot, weisses Play-Dreieck
make("yt", (255, 0, 51),
     white_pixels=[(3, 2), (3, 3), (3, 4), (3, 5), (4, 3), (4, 4), (5, 4)])

# Mailing: blau, weisser Briefumschlag (Rahmen + Klappe)
make("mail", (74, 163, 255),
     white_pixels=[(1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),
                   (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
                   (1, 3), (1, 4), (1, 5), (6, 3), (6, 4), (6, 5),
                   (2, 3), (3, 4), (4, 4), (5, 3)])

print("fertig:", [f for f in os.listdir(OUT) if f.endswith(".jpg")])
