#!/usr/bin/env python3
# © 2026 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Dessine les images du contrôleur dans Assets/, à côté de ce script.

Released.png, Pressed.png, PressedMoved.png, Exit.png, Setting.gif et
light-bulb.gif sortent de ce script et de lui seul : ils sont sous la
licence du dépôt, AGPL-3.0 ou plus récente. Le dessin ne dépend que de
constantes, donc une nouvelle exécution redonne les mêmes octets pour une
même version de Pillow.

Les PNG sont en RGBA sur fond transparent : le contrôleur les colle avec
leur propre masque sur une touche noire. Les GIF sont sur fond noir, la
couleur des touches, et bouclent sans fin.

    python draw_assets.py
"""

import math
import os

from PIL import Image, ImageDraw

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Assets")

TAILLE = 512
JAUNE = (255, 204, 51, 255)
CONTOUR = (178, 120, 20, 255)
SOMBRE = (60, 40, 20, 255)
ROUGE = (214, 48, 49, 255)
BLANC = (255, 255, 255, 255)


def _visage():
    """Le disque jaune et son contour, commun aux trois visages."""
    image = Image.new("RGBA", (TAILLE, TAILLE), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(image)
    dessin.ellipse((32, 32, 480, 480), fill=JAUNE, outline=CONTOUR, width=14)
    return image, dessin


def relache():
    """Visage souriant : la touche au repos."""
    image, dessin = _visage()
    dessin.ellipse((160, 170, 210, 240), fill=SOMBRE)
    dessin.ellipse((302, 170, 352, 240), fill=SOMBRE)
    dessin.arc((140, 200, 372, 400), start=20, end=160, fill=SOMBRE, width=22)
    return image


def presse():
    """Visage aux yeux plissés et bouche ouverte : la touche enfoncée."""
    image, dessin = _visage()
    dessin.arc((150, 180, 220, 240), start=200, end=340, fill=SOMBRE, width=18)
    dessin.arc((292, 180, 362, 240), start=200, end=340, fill=SOMBRE, width=18)
    dessin.ellipse((196, 290, 316, 400), fill=SOMBRE)
    return image


def presse_deplace():
    """Le visage enfoncé, une baguette et ses étincelles en plus : la
    touche enfoncée pendant qu'un glisser la déplace."""
    image = presse()
    dessin = ImageDraw.Draw(image)
    dessin.line((330, 470, 470, 330), fill=SOMBRE, width=18)
    for cx, cy, r in ((470, 300, 34), (420, 250, 20), (500, 380, 16)):
        _etoile(dessin, cx, cy, r, BLANC)
    return image


def _etoile(dessin, cx, cy, r, couleur):
    """Une étoile à quatre branches centrée sur (cx, cy), de rayon r."""
    points = []
    for i in range(8):
        angle = math.pi / 4 * i
        rayon = r if i % 2 == 0 else r / 3
        points.append(
            (cx + rayon * math.cos(angle), cy + rayon * math.sin(angle))
        )
    dessin.polygon(points, fill=couleur)


def sortie():
    """Disque rouge barré d'une croix blanche : la touche de sortie."""
    image = Image.new("RGBA", (TAILLE, TAILLE), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(image)
    dessin.ellipse((32, 32, 480, 480), fill=ROUGE)
    dessin.line((168, 168, 344, 344), fill=BLANC, width=48)
    dessin.line((344, 168, 168, 344), fill=BLANC, width=48)
    return image


def engrenage(images=24, cote=256, dents=10):
    """Un engrenage gris qui tourne d'un pas de dent sur la boucle : la
    dernière image raccorde avec la première."""
    trames = []
    centre = cote / 2
    for n in range(images):
        image = Image.new("RGB", (cote, cote), "black")
        dessin = ImageDraw.Draw(image)
        decalage = 2 * math.pi / dents * n / images
        points = []
        for i in range(dents * 4):
            angle = decalage + 2 * math.pi * i / (dents * 4)
            rayon = cote * (0.44 if i % 4 in (1, 2) else 0.34)
            points.append(
                (
                    centre + rayon * math.cos(angle),
                    centre + rayon * math.sin(angle),
                )
            )
        dessin.polygon(points, fill=(170, 170, 180))
        trou = cote * 0.13
        dessin.ellipse(
            (centre - trou, centre - trou, centre + trou, centre + trou),
            fill="black",
        )
        trames.append(image)
    return trames


def ampoule(images=16, cote=256):
    """Une ampoule dont le halo grandit puis décroît sur la boucle."""
    trames = []
    c = cote / 2
    for n in range(images):
        eclat = (1 - math.cos(2 * math.pi * n / images)) / 2
        image = Image.new("RGB", (cote, cote), "black")
        dessin = ImageDraw.Draw(image)
        halo = cote * (0.30 + 0.12 * eclat)
        teinte = int(60 + 120 * eclat)
        dessin.ellipse(
            (c - halo, c * 0.80 - halo, c + halo, c * 0.80 + halo),
            fill=(teinte, teinte, 0),
        )
        verre = int(200 + 55 * eclat)
        dessin.ellipse(
            (
                c - cote * 0.22,
                c * 0.80 - cote * 0.22,
                c + cote * 0.22,
                c * 0.80 + cote * 0.22,
            ),
            fill=(verre, verre, 60),
        )
        dessin.rectangle(
            (c - cote * 0.09, c * 1.10, c + cote * 0.09, c * 1.42),
            fill=(150, 150, 160),
        )
        for k in range(3):
            y = c * 1.16 + k * cote * 0.04
            dessin.line(
                (c - cote * 0.09, y, c + cote * 0.09, y),
                fill=(90, 90, 100),
                width=3,
            )
        trames.append(image)
    return trames


def _gif(chemin, trames, duree):
    trames[0].save(
        chemin,
        save_all=True,
        append_images=trames[1:],
        duration=duree,
        loop=0,
        optimize=False,
    )


def main():
    for nom, fabrique in (
        ("Released.png", relache),
        ("Pressed.png", presse),
        ("PressedMoved.png", presse_deplace),
        ("Exit.png", sortie),
    ):
        fabrique().save(os.path.join(ASSETS, nom), optimize=True)
    _gif(os.path.join(ASSETS, "Setting.gif"), engrenage(), 80)
    _gif(os.path.join(ASSETS, "light-bulb.gif"), ampoule(), 80)


if __name__ == "__main__":
    main()
