#!/usr/bin/env python3
# © 2026 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Verrou du Stream Deck : un seul programme du deck à la fois.

Deux programmes qui ouvrent le même périphérique HID se disputent ses
touches et son écran sans qu'aucun ne le dise. Chaque programme du deck
prend ce verrou au démarrage ; le second sort en BUSY_EXIT (2) en nommant
le premier.

Le verrou est un fcntl.flock exclusif sur $XDG_RUNTIME_DIR/erplibre-home/
deck.lock. flock appartient à la description de fichier ouverte : il tient
tant que le fichier reste ouvert, donc jusqu'à la fin du processus, et deux
open() du même fichier, même dans un seul processus, s'excluent. Le fichier
porte « PID programme départ » du détenteur, départ étant l'instant de
départ de son processus (champ 22 de /proc/<pid>/stat), qui distingue un
PID repris de celui qui a écrit ; un texte sans ce troisième champ se lit
encore. Le fichier reste en place après le détenteur, et seul le flock dit
si le deck est pris.

Bibliothèque standard seulement : TODO la charge hors du venv du deck.
"""

import fcntl
import os
import re
import signal
import stat
import sys
import tempfile

BUSY_EXIT = 2
# Le tiler sort en NO_DECK_EXIT quand aucun Stream Deck à écran n'est
# branché (un autre périphérique Elgato passe ExecCondition) ; comme
# BUSY_EXIT, l'unité ne le relance pas.
NO_DECK_EXIT = 3
LOCK_NAME = "deck.lock"

# Les fichiers verrouillés par ce processus : les garder ouverts garde le
# verrou jusqu'à la sortie.
_held = []


class DeckBusy(Exception):
    """Le verrou est tenu ailleurs ; `holder` vaut (pid, programme, départ),
    voir parse_holder."""

    def __init__(self, holder):
        super().__init__(
            "Stream Deck in use by %s (PID %s)" % (holder[1], holder[0])
        )
        self.holder = holder


def lock_path(environ=None):
    """Le chemin du verrou : sous $XDG_RUNTIME_DIR/erplibre-home, ou, sans
    lui (une connexion sans session), sous le répertoire temporaire du
    système, dans un dossier propre à l'uid."""
    environ = os.environ if environ is None else environ
    runtime = environ.get("XDG_RUNTIME_DIR")
    if runtime:
        dossier = os.path.join(runtime, "erplibre-home")
    else:
        dossier = os.path.join(
            tempfile.gettempdir(), "erplibre-home-%d" % os.getuid()
        )
    return os.path.join(dossier, LOCK_NAME)


def parse_holder(texte):
    """(pid, programme, départ) lus dans le texte du verrou, en chaînes. Le
    PID n'est gardé que fait de chiffres, le programme que fait de lettres,
    de chiffres, de « _ » et de « - » ; « ? » sinon, et pour ce qui manque.
    Le départ, troisième champ facultatif, vaut None quand il manque (un
    texte écrit sans lui), « ? » quand il n'est pas fait de chiffres : il
    ne concorde alors avec aucun processus. Status affiche ces mots et la
    diagnostic en tire « kill <pid> » : aucun texte arbitraire n'y passe."""
    mots = texte.split()
    depart = None
    if len(mots) > 2:
        depart = mots[2] if re.fullmatch(r"[0-9]{1,20}", mots[2]) else "?"
    mots += ["?", "?"]
    pid = mots[0] if re.fullmatch(r"[0-9]{1,10}", mots[0]) else "?"
    programme = (
        mots[1] if re.fullmatch(r"[A-Za-z0-9_-]{1,32}", mots[1]) else "?"
    )
    return pid, programme, depart


def _stat_fields(pid, proc="/proc"):
    """Les champs de <proc>/<pid>/stat après la dernière « ) » (le nom de
    commande peut en porter) : l'état d'abord (champ 3), l'instant de
    départ à l'index 19 (champ 22). None quand le fichier ne se lit pas."""
    try:
        with open(
            os.path.join(proc, str(pid), "stat"),
            encoding="utf-8",
            errors="replace",
        ) as fh:
            return fh.read().rsplit(")", 1)[1].split()
    except (OSError, IndexError):
        return None


def _start_time(pid, proc="/proc"):
    """L'instant de départ de `pid` (champ 22 de /proc/<pid>/stat, en tops
    d'horloge depuis le démarrage), en chaîne, ou None. Un PID repris par un
    autre processus en a un autre."""
    champs = _stat_fields(pid, proc)
    return champs[19] if champs and len(champs) > 19 else None


def holder_running(tenu, proc="/proc"):
    """Vrai quand le PID que nomme `tenu` (parse_holder) désigne encore le
    processus qui a écrit le texte : il vit, n'est pas un zombie, et son
    instant de départ est celui du texte quand le texte en porte un. Faux
    pour un PID « ? »."""
    pid, _programme, depart = tenu
    if pid == "?":
        return False
    champs = _stat_fields(pid, proc)
    if not champs or champs[0] in ("Z", "X"):
        return False
    return depart is None or (len(champs) > 19 and champs[19] == depart)


def _check_private_dir(dossier):
    """Lève PermissionError (une OSError) si `dossier` n'est pas un
    dossier de l'uid courant fermé aux autres comptes : sous le répertoire
    temporaire commun, un autre compte pourrait l'avoir posé."""
    etat = os.lstat(dossier)
    if (
        not stat.S_ISDIR(etat.st_mode)
        or etat.st_uid != os.getuid()
        or etat.st_mode & 0o077
    ):
        raise PermissionError("%s: not a private directory" % dossier)


def _open_private(path):
    """Ouvre `path` en lecture-écriture, créé en 0600 dans un dossier créé
    en 0700. Le dossier doit être privé (_check_private_dir) et `path` ne
    doit pas être un lien symbolique, qu'une troncature suivrait jusqu'à un
    autre fichier. Lève OSError sinon."""
    dossier = os.path.dirname(path)
    os.makedirs(dossier, mode=0o700, exist_ok=True)
    _check_private_dir(dossier)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    return os.fdopen(fd, "r+", encoding="utf-8")


def _write_holder(fh, program):
    """Écrit « PID programme départ » de ce processus dans `fh`, sans le
    départ quand /proc ne le donne pas."""
    texte = "%d %s" % (os.getpid(), program)
    depart = _start_time(os.getpid())
    if depart is not None:
        texte += " " + depart
    fh.seek(0)
    fh.truncate()
    fh.write(texte + "\n")
    fh.flush()


def acquire(program, path=None):
    """Prend le verrou pour `program` et le garde jusqu'à la sortie du
    processus. Rend le fichier ouvert. Un détenteur parti entre le premier
    essai et la lecture de son texte laisse le verrou libre : un second
    essai le prend. Lève DeckBusy quand un autre processus le tient,
    OSError quand le dossier ou le fichier n'est pas privé (voir
    _open_private)."""
    path = path or lock_path()
    fh = _open_private(path)
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        tenu = parse_holder(fh.read())
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.close()
            raise DeckBusy(tenu) from None
    _write_holder(fh, program)
    _held.append(fh)
    return fh


def acquire_or_exit(program, path=None):
    """acquire(), ou une ligne sur la sortie d'erreur qui nomme le
    détenteur et une sortie en BUSY_EXIT."""
    try:
        return acquire(program, path)
    except DeckBusy as busy:
        pid, detenteur, _depart = busy.holder
        print(
            "Stream Deck in use by %s (PID %s); close it first."
            % (detenteur, pid),
            file=sys.stderr,
        )
        sys.exit(BUSY_EXIT)


def holder(path=None):
    """(pid, programme, départ) du détenteur (voir parse_holder), ou None
    quand le verrou est libre, n'a jamais été pris, ou que son dossier n'est
    pas privé. Sonde par un flock non bloquant aussitôt rendu. L'ouverture est
    non bloquante et seul un fichier ordinaire est lu : une FIFO posée à sa
    place ne fige pas Status."""
    path = path or lock_path()
    try:
        _check_private_dir(os.path.dirname(path))
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    with os.fdopen(fd, "r", encoding="utf-8", errors="replace") as fh:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        try:
            fcntl.flock(fh, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return parse_holder(fh.read())
        fcntl.flock(fh, fcntl.LOCK_UN)
    return None


def holder_pids(path=None, proc="/proc"):
    """Les PID, triés, des processus de ce compte qui ont le verrou ouvert :
    le détenteur, et tout processus qui en a hérité le descripteur. Les
    processus d'un autre compte ne se lisent pas et
    sont omis. Le lien /proc/<pid>/fd/<n> est comparé au chemin réel du
    verrou, sans ouvrir ce qu'il désigne."""
    path = os.path.realpath(path or lock_path())
    pids = []
    for nom in os.listdir(proc):
        if not nom.isdigit():
            continue
        dossier = os.path.join(proc, nom, "fd")
        try:
            fds = os.listdir(dossier)
        except OSError:
            continue
        for fd in fds:
            try:
                if os.readlink(os.path.join(dossier, fd)) == path:
                    pids.append(int(nom))
                    break
            except OSError:
                continue
    return sorted(pids)


class SigtermExit(SystemExit):
    """Le SystemExit que lève exit_on_sigterm. Un code qui isole les
    appels d'un greffon, SystemExit compris, le laisse passer : l'arrêt du
    service n'est pas une erreur du greffon, et le second SIGTERM est
    ignoré."""


def exit_on_sigterm():
    """SIGTERM (systemctl stop, kill) lève SigtermExit(128 + SIGTERM) dans
    le fil principal au lieu de tuer le processus sur place : les finally
    qui remettent le deck à zéro et les fonctions atexit passent. Un second
    SIGTERM est ignoré, pour ne pas interrompre ce nettoyage."""

    def sortir(signum, _frame):
        signal.signal(signum, signal.SIG_IGN)
        raise SigtermExit(128 + signum)

    signal.signal(signal.SIGTERM, sortir)
