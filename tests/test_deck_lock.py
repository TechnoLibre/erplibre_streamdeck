#!/usr/bin/env python3
# © 2026 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Le verrou du Stream Deck : un programme du deck à la fois.

Les détenteurs sont de vrais processus python, chacun avec son propre
verrou dans un répertoire temporaire : flock appartient à la description de
fichier ouverte, et seul un autre processus prouve qu'il tient jusqu'à la
sortie et pas au-delà.

Ce que ces tests gardent :

- un second preneur sort en 2 et nomme le programme et le PID du premier ;
- le verrou part avec le processus qui le tient, et se reprend ensuite ;
- deux ouvertures du même fichier s'excluent, même dans un seul processus,
  d'où l'exec du point d'entrée du service ;
- holder() dit qui tient le deck sans le prendre ;
- un lien à la place du verrou, ou un dossier ouvert aux autres comptes,
  est refusé sans rien écrire ; holder() n'y lit rien non plus, ne bloque
  pas sur une FIFO et ne rend qu'un PID fait de chiffres ;
- le texte porte l'instant de départ du détenteur, troisième champ
  facultatif, et holder_running() dit si le PID nommé désigne encore son
  auteur ;
- SIGTERM devient SystemExit : les finally et atexit d'un programme du
  deck passent ;
- le tiler et le contrôleur prennent le verrou avant d'ouvrir le deck,
  remettent le deck à zéro sur SIGTERM, et le tiler sort en 3 sans deck.
- le contrôleur tient son PID dans <cache>/erplibre-home/controller.pid
  tant qu'il tourne, et l'en retire à la sortie.
"""

import ast
import fcntl
import importlib.util
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DECK_DIR = Path(__file__).resolve().parents[1]


def charger():
    """deck_lock.py par son chemin : la racine du dépôt n'est pas un
    paquet."""
    spec = importlib.util.spec_from_file_location(
        "deck_lock", DECK_DIR / "deck_lock.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def debut(pid):
    """Le champ 22 de /proc/<pid>/stat, l'instant de départ du processus,
    tel que le verrou l'écrit."""
    with open("/proc/%d/stat" % pid, encoding="utf-8") as fh:
        return fh.read().rsplit(")", 1)[1].split()[19]


# Le programme d'un preneur : argv = dossier du module, programme, chemin.
PRENDRE = (
    "import sys; sys.path.insert(0, sys.argv[1]); import deck_lock;"
    " deck_lock.{fonction}(sys.argv[2], sys.argv[3]);"
    " print('pret', flush=True); sys.stdin.read()"
)


class Verrou(unittest.TestCase):
    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.chemin = os.path.join(dossier.name, "erplibre-home", "deck.lock")
        self.deck_lock = charger()

    def detenteur(self, programme="tiler"):
        """Un processus qui prend le verrou et le garde jusqu'à ce que son
        entrée standard se ferme. Rend le Popen une fois le verrou pris."""
        proc = subprocess.Popen(
            [
                sys.executable,
                "-c",
                PRENDRE.format(fonction="acquire"),
                str(DECK_DIR),
                programme,
                self.chemin,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(proc.wait, 10)
        self.addCleanup(proc.stdin.close)
        self.addCleanup(proc.stdout.close)
        self.assertEqual("pret\n", proc.stdout.readline())
        return proc

    def second(self, programme="controller"):
        return subprocess.run(
            [
                sys.executable,
                "-c",
                PRENDRE.format(fonction="acquire_or_exit"),
                str(DECK_DIR),
                programme,
                self.chemin,
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_a_second_holder_exits_two_and_names_the_first(self):
        premier = self.detenteur("tiler")
        fini = self.second("controller")
        self.assertEqual(2, fini.returncode, fini.stderr)
        self.assertEqual("", fini.stdout)
        self.assertIn("tiler", fini.stderr)
        self.assertIn("PID %d" % premier.pid, fini.stderr)

    def test_the_lock_leaves_with_its_process(self):
        premier = self.detenteur()
        premier.stdin.close()
        premier.wait(10)
        self.assertTrue(os.path.exists(self.chemin))
        fini = self.second()
        self.assertEqual(0, fini.returncode, fini.stderr)
        self.assertEqual("pret\n", fini.stdout)

    def test_two_opens_in_one_process_exclude_each_other(self):
        tenu = self.deck_lock.acquire("tiler", self.chemin)
        self.addCleanup(tenu.close)
        with self.assertRaises(self.deck_lock.DeckBusy) as pris:
            self.deck_lock.acquire("controller", self.chemin)
        self.assertEqual(
            (str(os.getpid()), "tiler", debut(os.getpid())),
            pris.exception.holder,
        )

    def test_a_holder_leaving_during_acquire_hands_the_lock_over(self):
        """Le détenteur sort entre l'échec du flock et la lecture de son
        texte : le second essai d'acquire() prend le verrou au lieu de
        nommer un détenteur parti."""
        premier = self.detenteur("tiler")
        lire = self.deck_lock.parse_holder

        def le_detenteur_sort(texte):
            premier.stdin.close()
            premier.wait(10)
            return lire(texte)

        self.deck_lock.parse_holder = le_detenteur_sort
        tenu = self.deck_lock.acquire("controller", self.chemin)
        self.addCleanup(tenu.close)
        self.assertEqual(
            (str(os.getpid()), "controller", debut(os.getpid())),
            self.deck_lock.holder(self.chemin),
        )

    def test_holder_names_who_holds_and_takes_nothing(self):
        self.assertIsNone(self.deck_lock.holder(self.chemin))
        premier = self.detenteur("tiler")
        for _fois in range(2):
            self.assertEqual(
                (str(premier.pid), "tiler", debut(premier.pid)),
                self.deck_lock.holder(self.chemin),
            )
        premier.stdin.close()
        premier.wait(10)
        self.assertIsNone(self.deck_lock.holder(self.chemin))

    def test_holder_pids_names_the_processes_with_the_lock_open(self):
        self.assertEqual([], self.deck_lock.holder_pids(self.chemin))
        premier = self.detenteur("tiler")
        self.assertEqual(
            [premier.pid], self.deck_lock.holder_pids(self.chemin)
        )
        premier.stdin.close()
        premier.wait(10)
        self.assertEqual([], self.deck_lock.holder_pids(self.chemin))

    def test_the_directory_is_private(self):
        self.detenteur()
        mode = os.stat(os.path.dirname(self.chemin)).st_mode & 0o777
        self.assertEqual(0o700, mode)

    def test_a_symlinked_lock_is_refused_and_its_target_kept(self):
        """Un lien posé à la place du verrou n'est pas suivi : le fichier
        qu'il désigne garde son contenu."""
        dossier = os.path.dirname(self.chemin)
        os.makedirs(dossier, mode=0o700)
        cible = os.path.join(os.path.dirname(dossier), "cible")
        with open(cible, "w", encoding="utf-8") as fh:
            fh.write("exemple\n")
        os.symlink(cible, self.chemin)
        with self.assertRaises(OSError):
            self.deck_lock.acquire("tiler", self.chemin)
        with open(cible, encoding="utf-8") as fh:
            self.assertEqual("exemple\n", fh.read())

    def test_holder_does_not_follow_a_symlink(self):
        dossier = os.path.dirname(self.chemin)
        os.makedirs(dossier, mode=0o700)
        cible = os.path.join(os.path.dirname(dossier), "cible")
        with open(cible, "w", encoding="utf-8") as fh:
            fh.write("1 exemple\n")
        os.symlink(cible, self.chemin)
        tenu = open(cible, encoding="utf-8")
        self.addCleanup(tenu.close)
        fcntl.flock(tenu, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.assertIsNone(self.deck_lock.holder(self.chemin))

    def test_a_directory_open_to_others_is_refused(self):
        dossier = os.path.dirname(self.chemin)
        os.makedirs(dossier)
        os.chmod(dossier, 0o777)
        with self.assertRaises(OSError):
            self.deck_lock.acquire("tiler", self.chemin)
        self.assertFalse(os.path.exists(self.chemin))


class HolderPrudent(unittest.TestCase):
    """holder() lit un fichier que Status affiche, et dont la diagnostic tire
    un « kill <pid> » : rien n'y est repris sans contrôle."""

    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.chemin = os.path.join(dossier.name, "erplibre-home", "deck.lock")
        self.deck_lock = charger()

    def tenir(self, texte, mode=0o700):
        """Pose le verrou avec `texte` et le tient par une ouverture à part,
        dans un dossier de mode `mode`."""
        dossier = os.path.dirname(self.chemin)
        os.makedirs(dossier, exist_ok=True)
        os.chmod(dossier, mode)
        fh = open(self.chemin, "w", encoding="utf-8")
        self.addCleanup(fh.close)
        fh.write(texte)
        fh.flush()
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_only_a_numeric_pid_is_kept(self):
        self.tenir("12;reboot tiler\n")
        self.assertEqual(
            ("?", "tiler", None), self.deck_lock.holder(self.chemin)
        )

    def test_an_odd_program_name_is_not_kept(self):
        self.tenir("12 $(exemple)\n")
        self.assertEqual(("12", "?", None), self.deck_lock.holder(self.chemin))

    def test_the_start_time_is_an_optional_third_field(self):
        """Un texte écrit avant le troisième champ se lit encore ; un
        troisième champ qui n'est pas fait de chiffres vaut « ? », que
        rien ne reconnaît."""
        for texte, attendu in (
            ("12 tiler\n", ("12", "tiler", None)),
            ("12 tiler 345\n", ("12", "tiler", "345")),
            ("12 tiler 3;4\n", ("12", "tiler", "?")),
        ):
            with self.subTest(texte=texte):
                self.assertEqual(attendu, self.deck_lock.parse_holder(texte))

    def test_a_directory_open_to_others_gives_no_holder(self):
        self.tenir("12 tiler\n", mode=0o777)
        self.assertIsNone(self.deck_lock.holder(self.chemin))

    def test_a_fifo_does_not_hang(self):
        """Une FIFO sans écrivain bloquerait un open() sans O_NONBLOCK."""
        dossier = os.path.dirname(self.chemin)
        os.makedirs(dossier, mode=0o700)
        os.mkfifo(self.chemin)
        fini = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, sys.argv[1]);"
                " import deck_lock; print(deck_lock.holder(sys.argv[2]))",
                str(DECK_DIR),
                self.chemin,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(0, fini.returncode, fini.stderr)
        self.assertEqual("None\n", fini.stdout)


def ligne_stat(pid, etat, depart):
    """Une ligne de /proc/<pid>/stat : un nom à espaces et parenthèse, puis
    l'état (champ 3) et l'instant de départ (champ 22)."""
    milieu = " ".join(["0"] * 18)
    return "%d (a) b) %s %s %s 0 0\n" % (pid, etat, milieu, depart)


class LeDetenteurNomme(unittest.TestCase):
    """holder_running() : le PID que nomme le verrou désigne-t-il encore le
    processus qui l'a écrit ? Un /proc écrit à la main."""

    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.proc = dossier.name
        for pid, etat in ((123, "S"), (124, "Z")):
            os.makedirs(os.path.join(self.proc, str(pid)))
            with open(os.path.join(self.proc, str(pid), "stat"), "w") as fh:
                fh.write(ligne_stat(pid, etat, 5555))
        self.deck_lock = charger()

    def test_the_start_time_must_match(self):
        for tenu, attendu in (
            (("123", "tiler", "5555"), True),
            (("123", "tiler", "6666"), False),
            (("123", "tiler", "?"), False),
            (("123", "tiler", None), True),
            (("124", "tiler", "5555"), False),
            (("125", "tiler", None), False),
            (("?", "tiler", None), False),
        ):
            with self.subTest(tenu=tenu):
                self.assertEqual(
                    attendu, self.deck_lock.holder_running(tenu, self.proc)
                )

    def test_a_live_holder_is_running(self):
        dossier = os.path.join(self.proc, "run", "erplibre-home")
        tenu = self.deck_lock.acquire("tiler", os.path.join(dossier, "x"))
        self.addCleanup(tenu.close)
        self.assertTrue(
            self.deck_lock.holder_running(
                self.deck_lock.holder(os.path.join(dossier, "x"))
            )
        )


# Un programme du deck réduit à son nettoyage : argv = dossier du module,
# fichier où noter ce qui a tourné.
NETTOYAGE = """
import atexit, sys, time
sys.path.insert(0, sys.argv[1])
import deck_lock
deck_lock.exit_on_sigterm()
def noter(quoi):
    with open(sys.argv[2], "a") as fh:
        fh.write(quoi + "\\n")
atexit.register(noter, "atexit")
try:
    print("pret", flush=True)
    time.sleep(30)
finally:
    noter("finally")
"""


class SigtermPropre(unittest.TestCase):
    def test_sigterm_runs_finally_and_atexit(self):
        with tempfile.TemporaryDirectory() as dossier:
            notes = os.path.join(dossier, "notes")
            proc = subprocess.Popen(
                [sys.executable, "-c", NETTOYAGE, str(DECK_DIR), notes],
                stdout=subprocess.PIPE,
                text=True,
            )
            self.addCleanup(proc.kill)
            self.assertEqual("pret\n", proc.stdout.readline())
            proc.send_signal(signal.SIGTERM)
            self.assertEqual(128 + signal.SIGTERM, proc.wait(10))
            proc.stdout.close()
            with open(notes, encoding="utf-8") as fh:
                self.assertEqual(["finally", "atexit"], fh.read().split())

    def test_sigterm_raises_its_own_system_exit(self):
        """Un code qui isole les SystemExit d'un greffon reconnaît
        l'arrêt du service à sa classe."""
        deck_lock = charger()
        ancien = signal.getsignal(signal.SIGTERM)
        self.addCleanup(signal.signal, signal.SIGTERM, ancien)
        deck_lock.exit_on_sigterm()
        with self.assertRaises(deck_lock.SigtermExit) as pris:
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        self.assertIsInstance(pris.exception, SystemExit)
        self.assertEqual(128 + signal.SIGTERM, pris.exception.code)


class LeChemin(unittest.TestCase):
    def test_under_the_runtime_dir(self):
        deck_lock = charger()
        self.assertEqual(
            "/exemple/run/erplibre-home/deck.lock",
            deck_lock.lock_path({"XDG_RUNTIME_DIR": "/exemple/run"}),
        )

    def test_without_runtime_dir_a_per_user_temp_dir(self):
        deck_lock = charger()
        self.assertEqual(
            os.path.join(
                tempfile.gettempdir(),
                "erplibre-home-%d" % os.getuid(),
                "deck.lock",
            ),
            deck_lock.lock_path({}),
        )


def fonction(source, nom):
    arbre = ast.parse(source)
    return next(
        n
        for n in ast.walk(arbre)
        if isinstance(n, ast.FunctionDef) and n.name == nom
    )


def appel_du_verrou(instruction, attr="acquire_or_exit"):
    """« deck_lock.<attr>(…) » : rend le premier argument constant (None
    sans argument), ou False pour toute autre instruction."""
    if not isinstance(instruction, ast.Expr):
        return False
    appel = instruction.value
    if (
        isinstance(appel, ast.Call)
        and isinstance(appel.func, ast.Attribute)
        and isinstance(appel.func.value, ast.Name)
        and appel.func.value.id == "deck_lock"
        and appel.func.attr == attr
    ):
        if not appel.args:
            return None
        if isinstance(appel.args[0], ast.Constant):
            return appel.args[0].value
    return False


def principal(source):
    """Le dernier bloc « if __name__ == "__main__": » du module, celui qui
    lance le programme ; un bloc plus haut peut lire la ligne de commande
    avant les imports du matériel."""
    return [
        n
        for n in ast.parse(source).body
        if isinstance(n, ast.If)
        and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name)
        and n.test.left.id == "__name__"
    ][-1]


class LesProgrammesLePrennent(unittest.TestCase):
    """Le verrou se prend AVANT d'ouvrir le deck : le second programme sort
    sans avoir touché au périphérique du premier. SIGTERM se change ensuite
    en SystemExit, pour que le deck soit remis à zéro."""

    def test_the_tiler_takes_it_first_thing_in_main(self):
        source = (DECK_DIR / "erplibre_streamdeck/__main__.py").read_text(
            encoding="utf-8"
        )
        main = fonction(source, "main")
        self.assertEqual("tiler", appel_du_verrou(main.body[0]))
        self.assertIsNone(appel_du_verrou(main.body[1], "exit_on_sigterm"))
        self.assertRegex(source, r"(?m)^import deck_lock\b")

    def test_the_tiler_exits_three_without_a_visual_deck(self):
        """L'unité ne relance pas un tiler qui ne trouve aucun deck à écran
        (un autre périphérique Elgato a passé ExecCondition)."""
        self.assertEqual(3, charger().NO_DECK_EXIT)
        source = (DECK_DIR / "erplibre_streamdeck/app.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'print("No visual Stream Deck found.")\n'
            "        sys.exit(deck_lock.NO_DECK_EXIT)",
            source,
        )

    def test_the_controller_takes_it_before_its_pidfile(self):
        source = (DECK_DIR / "erplibre_controller.py").read_text(
            encoding="utf-8"
        )
        bloc = principal(source)
        self.assertEqual("controller", appel_du_verrou(bloc.body[0]))
        self.assertIsNone(appel_du_verrou(bloc.body[1], "exit_on_sigterm"))
        self.assertRegex(source, r"(?m)^import deck_lock$")

    def test_the_controller_closes_its_decks_on_the_way_out(self):
        """Ses fils d'animation tournent tant que le deck est ouvert : sans
        cette fermeture, SystemExit attendrait leur fin pour toujours."""
        source = (DECK_DIR / "erplibre_controller.py").read_text(
            encoding="utf-8"
        )
        essai = next(
            n for n in principal(source).body if isinstance(n, ast.Try)
        )
        self.assertEqual(
            "sdc.close_decks()", ast.unparse(essai.finalbody[0]).strip()
        )
        self.assertIn("self.lst_deck.append(deck)", source)

    def test_sigterm_resets_the_controller_deck_and_exits_143(self):
        """Le contrôleur tourne sur des modules factices, avec un deck qui
        note chaque appel et s'arrête en cours d'ouverture : SIGTERM le
        remet à zéro, puis le ferme, et le processus sort en 143."""
        with tempfile.TemporaryDirectory() as dossier:
            notes = os.path.join(dossier, "notes")
            factices = os.path.join(dossier, "factices")
            for nom, texte in CONTROLEUR_FACTICE.items():
                fichier = os.path.join(factices, nom)
                os.makedirs(os.path.dirname(fichier), exist_ok=True)
                with open(fichier, "w", encoding="utf-8") as fh:
                    fh.write(texte.format(notes=notes))
            proc = subprocess.Popen(
                [sys.executable, str(DECK_DIR / "erplibre_controller.py")],
                env=dict(
                    os.environ,
                    PYTHONPATH=factices,
                    XDG_RUNTIME_DIR=dossier,
                    XDG_CACHE_HOME=dossier,
                ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.addCleanup(proc.kill)
            for ligne in proc.stdout:
                if ligne == "pret\n":
                    break
            proc.send_signal(signal.SIGTERM)
            self.assertEqual(128 + signal.SIGTERM, proc.wait(10))
            proc.stdout.close()
            with open(notes, encoding="utf-8") as fh:
                self.assertEqual(
                    ["open", "reset", "reset", "close"], fh.read().split()
                )

    def test_the_controller_holds_its_pidfile_while_it_runs(self):
        """Restart deck lit le PID du contrôleur dans
        <cache>/erplibre-home/controller.pid. Il s'y écrit au lancement et
        disparaît à la sortie : un PID resté là, repris par un autre
        processus, serait tué à sa place."""
        with tempfile.TemporaryDirectory() as dossier:
            factices = os.path.join(dossier, "factices")
            for nom, texte in CONTROLEUR_FACTICE.items():
                fichier = os.path.join(factices, nom)
                os.makedirs(os.path.dirname(fichier), exist_ok=True)
                with open(fichier, "w", encoding="utf-8") as fh:
                    fh.write(texte.format(notes=os.path.join(dossier, "n")))
            pidfile = os.path.join(dossier, "erplibre-home", "controller.pid")
            proc = subprocess.Popen(
                [sys.executable, str(DECK_DIR / "erplibre_controller.py")],
                env=dict(
                    os.environ,
                    PYTHONPATH=factices,
                    XDG_RUNTIME_DIR=dossier,
                    XDG_CACHE_HOME=dossier,
                ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.addCleanup(proc.kill)
            for ligne in proc.stdout:
                if ligne == "pret\n":
                    break
            with open(pidfile, encoding="utf-8") as fh:
                self.assertEqual(str(proc.pid), fh.read().strip())
            proc.send_signal(signal.SIGTERM)
            proc.wait(10)
            proc.stdout.close()
            self.assertFalse(os.path.exists(pidfile))


# Les modules que le contrôleur importe, réduits à ce qu'il en lit avant
# d'animer : son deck note open, reset et close dans {notes}, et s'arrête
# sur deck_type(), après que init() l'a ouvert et remis à zéro.
CONTROLEUR_FACTICE = {
    "cv2.py": "",
    "requests.py": "",
    "PIL/__init__.py": "",
    "PIL/Image.py": "",
    "PIL/ImageDraw.py": "",
    "PIL/ImageFont.py": "",
    "PIL/ImageOps.py": "",
    "PIL/ImageSequence.py": "",
    "StreamDeck/__init__.py": "",
    "StreamDeck/Devices/__init__.py": "",
    "StreamDeck/Devices/StreamDeck.py": (
        "DialEventType = TouchscreenEventType = None\n"
    ),
    "StreamDeck/ImageHelpers/__init__.py": "",
    "StreamDeck/ImageHelpers/PILHelper.py": "",
    "StreamDeck/Transport/__init__.py": "",
    "StreamDeck/Transport/Transport.py": (
        "class TransportError(Exception):\n    pass\n"
    ),
    "StreamDeck/DeviceManager.py": """\
import time


class ProbeError(Exception):
    pass


class Deck:
    def note(self, quoi):
        with open({notes!r}, "a", encoding="utf-8") as fh:
            fh.write(quoi + "\\n")

    def is_visual(self):
        return True

    def open(self):
        self.note("open")

    def reset(self):
        self.note("reset")

    def close(self):
        self.note("close")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def deck_type(self):
        print("pret", flush=True)
        time.sleep(30)


class DeviceManager:
    def enumerate(self):
        return [Deck()]
""",
}


if __name__ == "__main__":
    unittest.main()
