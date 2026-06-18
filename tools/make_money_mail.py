"""Erzeugt bessere 8x8-Icons fuer Euro (eur) und Mail (mail) -- handgepixelt,
hoher Kontrast. Speichert direkt eur.jpg/mail.jpg + Vorschau."""
import os

from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "icons")
WHITE = (255, 255, 255)
GREEN = (40, 220, 90)
BLACK = (0, 0, 0)
BLUE = (40, 120, 230)


def build(bg, pixels, fg, name):
    img = Image.new("RGB", (8, 8), bg)
    px = img.load()
    for p in pixels:
        px[p] = fg
    img.save(os.path.join(OUT, name + ".jpg"), quality=95)
    img.resize((120, 120), Image.NEAREST).save(os.path.join(OUT, name + "_preview.png"))


# Euro: gruenes Eurozeichen (C-Form + zwei Querstriche) auf schwarz
euro = [(2, 1), (3, 1), (4, 1),
        (1, 2), (5, 2),
        (1, 3), (2, 3), (3, 3), (4, 3),
        (1, 4),
        (1, 5), (2, 5), (3, 5), (4, 5),
        (1, 6), (5, 6),
        (2, 7), (3, 7), (4, 7)]
build(BLACK, euro, GREEN, "eur")

# Mail: weisser Briefumschlag (Rahmen + Klappe) auf blau
mail = [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),
        (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
        (1, 3), (1, 4), (1, 5), (6, 3), (6, 4), (6, 5),
        (2, 3), (3, 4), (4, 4), (5, 3)]
build(BLUE, mail, WHITE, "mail")

print("eur + mail neu erzeugt")
