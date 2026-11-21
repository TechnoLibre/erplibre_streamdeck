#!/usr/bin/env python3
# © 2026 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Les points d'entrée du dépôt et ce qu'ils demandent au venv.

Ce que ces tests gardent :

- requirements.txt porte ce que le code importe, et plus lz4 ni polib,
  que le venv ne sert pas ;
- le programme du deck et le contrôleur répondent à -h, --help et à une
  option inconnue sans importer le matériel ni prendre le verrou du deck,
  depuis n'importe quel répertoire courant.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DECK_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS = DECK_DIR / "requirements.txt"


class TestRequirements(unittest.TestCase):
    def noms(self):
        noms = set()
        for ligne in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
            ligne = ligne.split("#", 1)[0].strip()
            if ligne:
                noms.add(
                    re.split(r"[<>=!~\[; ]", ligne, maxsplit=1)[0].lower()
                )
        return noms

    def test_what_the_deck_imports_is_required(self):
        for nom in ("requests", "keyboard", "pyudev", "streamdeck"):
            self.assertIn(nom, self.noms())

    def test_pil_and_cv2_come_from_pillow_and_opencv(self):
        """Le rendu des touches importe PIL et cv2, dont les paquets pip
        portent un autre nom que le module."""
        for nom in ("pillow", "opencv-python"):
            with self.subTest(nom=nom):
                self.assertIn(nom, self.noms())

    def test_lz4_left_the_venv(self):
        self.assertNotIn("lz4", self.noms())

    def test_polib_left_the_venv(self):
        """compile_locales.py tourne sous le python3 du système, et
        l'installateur compile par msgfmt : rien du venv n'importe polib."""
        self.assertNotIn("polib", self.noms())


# De faux paquets du matériel (StreamDeck, PIL, cv2...), placés en tête de
# PYTHONPATH : les importer écrit un témoin et tue le processus. Un
# programme du deck lancé par erreur ne touche donc jamais un vrai deck, et
# le témoin le dit.
FAUX_MATERIEL = """import os
with open(os.environ["TEMOIN_MATERIEL"], "w") as f:
    f.write(__name__)
os._exit(99)
"""


# Les paquets que les points d'entrée du deck importent pour le matériel,
# et webbrowser, qu'aucun ne doit ouvrir : son faux pose le témoin à
# l'appel de open(), pas à l'import.
PAQUETS_MATERIEL = ("StreamDeck", "PIL", "cv2", "requests", "pyudev")
FAUX_WEBBROWSER = """import builtins
import os


def open(*_args, **_kw):
    with builtins.open(os.environ["TEMOIN_MATERIEL"], "w") as f:
        f.write("webbrowser")
    os._exit(98)
"""


def executer_sans_materiel(script, *args):
    """Lance `script` sous le python des tests avec les faux paquets du
    matériel, un faux webbrowser et un XDG_RUNTIME_DIR temporaire. Rend le
    CompletedProcess, si un faux a posé son témoin, et le contenu du
    répertoire du verrou du deck. N'affirme rien."""
    with tempfile.TemporaryDirectory() as tmp:
        faux = os.path.join(tmp, "faux")
        sources = {
            "%s/__init__.py" % paquet: FAUX_MATERIEL
            for paquet in PAQUETS_MATERIEL
        }
        sources["webbrowser/__init__.py"] = FAUX_WEBBROWSER
        for relatif, source in sources.items():
            chemin = os.path.join(faux, relatif)
            os.makedirs(os.path.dirname(chemin), exist_ok=True)
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(source)
        run_dir = os.path.join(tmp, "run")
        os.makedirs(run_dir, mode=0o700)
        temoin = os.path.join(tmp, "temoin")
        env = dict(
            os.environ,
            PYTHONPATH=faux,
            XDG_RUNTIME_DIR=run_dir,
            XDG_CONFIG_HOME=os.path.join(tmp, "config"),
            XDG_CACHE_HOME=os.path.join(tmp, "cache"),
            HOME=os.path.join(tmp, "home"),
            TEMOIN_MATERIEL=temoin,
        )
        res = subprocess.run(
            [sys.executable, str(script)] + list(args),
            cwd=tmp,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return res, os.path.exists(temoin), os.listdir(run_dir)


def lancer_sans_materiel(cas, script, *args, materiel=False):
    """executer_sans_materiel(), puis échoue si le verrou du deck a été
    pris, et si un faux a posé son témoin ou non selon `materiel`. Rend le
    CompletedProcess."""
    res, importe, verrou = executer_sans_materiel(script, *args)
    cas.assertEqual(materiel, importe, res.stderr)
    cas.assertEqual([], verrou, "le verrou du deck a été pris")
    return res


class TestTilerCommandLine(unittest.TestCase):
    """La ligne de commande du programme du deck : -h et --help affichent
    l'aide et sortent en 0, toute autre option l'affiche sur la sortie
    d'erreur et sort en 2. Ni l'une ni l'autre n'importe le matériel ni ne
    prend le verrou du deck, posé ici sous un XDG_RUNTIME_DIR temporaire."""

    def lancer(self, *args):
        return lancer_sans_materiel(
            self, DECK_DIR / "erplibre_streamdeck", *args
        )

    def test_help_prints_the_usage_and_exits_0(self):
        for option in ("-h", "--help"):
            res = self.lancer(option)
            self.assertEqual(0, res.returncode, res.stderr)
            self.assertIn("usage:", res.stdout)
            self.assertIn("--list-plugins", res.stdout)
            self.assertIn("erplibre-home/streamdeck.conf", res.stdout)
            self.assertEqual("", res.stderr)

    def test_help_names_the_exit_codes(self):
        aide = self.lancer("--help").stdout
        for code in ("2", "3", "143"):
            self.assertRegex(aide, r"(?m)^\s+%s\s" % code)

    def test_an_unknown_option_exits_2_with_the_usage(self):
        for args in (
            ["--bogus"],
            ["run"],
            ["--list"],
            ["--list-plugins", "x"],
        ):
            res = self.lancer(*args)
            self.assertEqual(2, res.returncode, args)
            self.assertIn("usage:", res.stderr, args)
            self.assertEqual("", res.stdout, args)

class TestControllerCommandLine(unittest.TestCase):
    """La ligne de commande du contrôleur : -h et --help sortent en 0, une
    option inconnue en 2 avec l'usage sur la sortie d'erreur, avant les
    imports de cv2, de PIL et de StreamDeck et sans le verrou du deck."""

    SCRIPT = DECK_DIR / "erplibre_controller.py"

    def test_help_prints_the_usage_and_exits_0(self):
        for option in ("-h", "--help"):
            res = lancer_sans_materiel(self, self.SCRIPT, option)
            self.assertEqual(0, res.returncode, res.stderr)
            self.assertIn("usage:", res.stdout)
            self.assertIn("deck lock", res.stdout)
            self.assertRegex(res.stdout, r"(?m)^\s+2\s")
            self.assertRegex(res.stdout, r"(?m)^\s+143\s")
            self.assertEqual("", res.stderr)

    def test_an_unknown_option_exits_2_with_the_usage(self):
        for args in (["--bogus"], ["run"], ["--hel"], ["-x"]):
            res = lancer_sans_materiel(self, self.SCRIPT, *args)
            self.assertEqual(2, res.returncode, args)
            self.assertIn("usage:", res.stderr, args)
            self.assertEqual("", res.stdout, args)

    def test_without_an_option_it_goes_on_to_the_hardware(self):
        """Sans option, rien ne s'arrête à la ligne de commande : le
        premier import du matériel est atteint, et son faux tue le
        processus avant le verrou."""
        res = lancer_sans_materiel(self, self.SCRIPT, materiel=True)
        self.assertEqual(99, res.returncode, res.stderr)


if __name__ == "__main__":
    unittest.main()
