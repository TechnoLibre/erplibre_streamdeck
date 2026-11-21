<!---------------------------->
<!-- multilingual suffix: en, fr -->
<!-- no suffix: en -->
<!---------------------------->

<!-- [en] -->
# ERPLibre Stream Deck

The deck program of ERPLibre Home for the Elgato Stream Deck: a small
kernel that runs plugin pages (accessibility, Bluetooth, sound, window
layouts, tiling, timers, Claude and mpv sessions, TODO terminals,
speech-to-text translator), the classic controller, the deck lock that
lets one program at a time open the deck, and the translator. Every
program adapts to the model plugged in (Mini, Original, MK.2, XL, Plus,
Neo) through `deck.key_layout()`.

It runs on its own, and ERPLibre clones it at `script/stream_deck/deck/`
(see [Inside ERPLibre](#inside-erplibre)). `CONTRACT.md` states what
ERPLibre and the GNOME extension rely on.

## Install

The Stream Deck library talks to the deck through hidapi, and the deck
needs a udev rule to open without root; `wmctrl` serves key 3 of the
controller. Inside ERPLibre, skip this block: `install_erplibre_home.sh
--stream-deck` installs the same packages and manages its own rule,
`70-streamdeck.rules`, which also starts the deck service when a deck is
plugged in. On its own, on Debian and Ubuntu, the rule goes in a file of
its own name, which ERPLibre's installer neither overwrites nor removes:

<!-- [fr] -->
# ERPLibre Stream Deck

Le programme du deck d'ERPLibre Home pour l'Elgato Stream Deck : un petit
noyau qui fait tourner des pages de plugins (accessibilité, Bluetooth,
son, dispositions de fenêtres, tuilage, minuteurs, sessions Claude et
mpv, terminaux TODO, traducteur vocal), le contrôleur classique, le
verrou du deck qui ne laisse qu'un programme à la fois ouvrir le deck, et
le traducteur. Chaque programme s'adapte au modèle branché (Mini,
Original, MK.2, XL, Plus, Neo) par `deck.key_layout()`.

Il tourne seul, et ERPLibre le clone dans `script/stream_deck/deck/`
(voir [Dans ERPLibre](#dans-erplibre)). `CONTRACT.md` dit ce dont ERPLibre
et l'extension GNOME dépendent.

## Installer

La bibliothèque Stream Deck parle au deck par hidapi, et le deck demande
une règle udev pour s'ouvrir sans root ; `wmctrl` sert la touche 3 du
contrôleur. Dans ERPLibre, sauter ce bloc : `install_erplibre_home.sh
--stream-deck` installe les mêmes paquets et gère sa propre règle,
`70-streamdeck.rules`, qui démarre aussi le service du deck quand un deck
est branché. Seul, sur Debian et Ubuntu, la règle va dans un fichier à
son propre nom, que l'installateur d'ERPLibre n'écrase ni ne retire :

<!-- [end] -->
<!-- [common] -->

```bash
sudo apt install -y libudev-dev libusb-1.0-0-dev libhidapi-libusb0 python3-venv wmctrl
sudo tee /etc/udev/rules.d/70-streamdeck-standalone.rules << 'RULES'
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="0fd9", TAG+="uaccess"
RULES
sudo udevadm control --reload-rules && sudo udevadm trigger
```

<!-- [end] -->
<!-- [en] -->
Then clone the repository and install its packages in a venv; every
command below runs from the repository root, under that venv:

<!-- [fr] -->
Puis cloner le dépôt et installer ses paquets dans un venv ; chaque
commande plus bas se lance depuis la racine du dépôt, sous ce venv :

<!-- [end] -->
<!-- [common] -->

```bash
git clone https://github.com/TechnoLibre/erplibre-streamdeck.git
cd erplibre-streamdeck
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python erplibre_streamdeck
```

<!-- [end] -->

<!-- [en] -->

## Controller

### erplibre_controller.py

Main Stream Deck controller for ERPLibre. Handles physical buttons with assigned actions:

| Button | Action |
|--------|--------|
| 0 | Launch ERPLibre's `todo.py` (interactive CLI), inside ERPLibre |
| 1 | Brightness + |
| 2 | Brightness - |
| 3 | Launch `keyboard_talk.py` (keyboard automation) |
| 4 | Reset Stream Deck |
| 5 | Cycle display mode: Animation -> Big image -> Webcam |

Supports the Stream Deck Plus (touchscreen, dials), USB hotplug detection (pyudev), and GIF animations. `-h` and `--help` print the usage and the exit codes (1: driver cannot probe, 2: deck lock held or bad option, 143: SIGTERM), then exit 0; any other argument prints the usage on stderr and exits 2. Neither takes the deck lock nor needs cv2, PIL or the Stream Deck library.

<!-- [fr] -->

## Contrôleur

### erplibre_controller.py

Contrôleur principal du Stream Deck pour ERPLibre. Gère les boutons physiques avec des actions assignées :

| Bouton | Action |
|--------|--------|
| 0 | Lance le `todo.py` d'ERPLibre (CLI interactif), dans ERPLibre |
| 1 | Luminosité + |
| 2 | Luminosité - |
| 3 | Lance `keyboard_talk.py` (automatisation clavier) |
| 4 | Reset du Stream Deck |
| 5 | Cycle mode d'affichage : Animation → Big image → Webcam |

Supporte le Stream Deck Plus (touchscreen, dials), la détection USB hotplug (pyudev), et les animations GIF. `-h` et `--help` affichent l'usage et les codes de sortie (1 : le pilote ne peut sonder, 2 : verrou du deck tenu ou option invalide, 143 : SIGTERM), puis sortent en 0 ; tout autre argument affiche l'usage sur la sortie d'erreur et sort en 2. Ni l'un ni l'autre ne prend le verrou du deck ni n'a besoin de cv2, de PIL ou de la bibliothèque Stream Deck.

<!-- [common] -->

```bash
python erplibre_controller.py
python erplibre_controller.py --help
```

<!-- [en] -->

### keyboard_talk.py

Keyboard automation script, key 3 of the controller. Uses `wmctrl` to target a terminal window, then sends an automated key sequence via the `keyboard` library, under `sudo`.

<!-- [fr] -->

### keyboard_talk.py

Script d'automatisation clavier, touche 3 du contrôleur. Utilise `wmctrl` pour cibler une fenêtre terminal, puis envoie une séquence de touches automatisée via la librairie `keyboard`, sous `sudo`.

<!-- [en] -->

## Deck program

`erplibre_streamdeck/` is the deck program of ERPLibre Home (`DECK_PROGRAM=tiler`, `make streamdeck_erplibre` inside ERPLibre). It is a package run as a directory: a small kernel owns the deck, the lock, the flash, the home screen and the key dispatch, and every feature is a plugin.

<!-- [fr] -->

## Programme du deck

`erplibre_streamdeck/` est le programme du deck d'ERPLibre Home (`DECK_PROGRAM=tiler`, `make streamdeck_erplibre` dans ERPLibre). C'est un paquet lancé comme un répertoire : un petit noyau possède le deck, le verrou, le flash, l'écran d'accueil et la distribution des touches, et chaque fonction est un plugin.

<!-- [common] -->

```bash
python erplibre_streamdeck
python erplibre_streamdeck --list-plugins
python erplibre_streamdeck --catalog
python erplibre_streamdeck --help
```

<!-- [en] -->

`--list-plugins` prints what the loader finds (one line per plugin: `active`, `off`, `replaced by user` or `refused` with its reason; `unreadable` for a plugin directory it cannot list) without opening the deck or taking its lock. `-h` and `--help` print the usage, the settings file and the exit codes (2: deck lock held or bad option, 3: no Stream Deck with a screen, 143: SIGTERM), then exit 0; any other argument prints the usage on stderr and exits 2. Neither takes the lock nor needs the Stream Deck library. `--catalog` prints, as JSON, what a `keymap.json` layout may name (see below); it reads the deck models from the Stream Deck library without opening any deck, and takes no lock. Layout of the package:

<!-- [fr] -->

`--list-plugins` affiche ce que le chargeur trouve (une ligne par plugin : `active`, `off`, `replaced by user` ou `refused` avec sa raison ; `unreadable` pour un répertoire de plugins illisible) sans ouvrir le deck ni prendre son verrou. `-h` et `--help` affichent l'usage, le fichier de réglages et les codes de sortie (2 : verrou du deck tenu ou option invalide, 3 : aucun Stream Deck à écran, 143 : SIGTERM), puis sortent en 0 ; tout autre argument affiche l'usage sur la sortie d'erreur et sort en 2. Ni l'un ni l'autre ne prend le verrou ni n'a besoin de la bibliothèque Stream Deck. `--catalog` affiche en JSON ce qu'une disposition de `keymap.json` peut nommer (voir plus bas) ; il lit les modèles de deck dans la bibliothèque Stream Deck sans ouvrir aucun deck, et ne prend pas de verrou. Disposition du paquet :

<!-- [common] -->

```
erplibre_streamdeck/
├── __main__.py   # entry point, --help, --list-plugins / point d'entrée
├── app.py        # build(): settings, plugins, kernel / assemblage
├── kernel.py     # deck, lock, flash, loop, dispatch / noyau
├── home.py       # home screen: buttons, fixtures, tiles / accueil
├── keymap.py     # keymap.json, --catalog / disposition des touches
├── loader.py     # discovery of the plugins / découverte
├── plugin.py     # Plugin, Page, HomeButton, Fixture, TileProvider
├── context.py    # Context, the one object a plugin receives
├── paths.py, settings.py, dbus.py
├── ui/           # rendering, colours, i18n / rendu, couleurs, i18n
└── plugins/      # a11y, bluetooth, claude_sessions, dev_reload,
                  # layouts, mpv_sessions, sound, tiling, timers,
                  # todo_terminals, translate
```

<!-- [en] -->

### Turning plugins off

The setting `DECK_PLUGINS_OFF` in `$XDG_CONFIG_HOME/erplibre-home/streamdeck.conf` is a comma-separated list of plugin ids that are not imported. Inside ERPLibre, set it from TODO › ERPLibre Home › Plugins on/off, or by hand; the deck reads it through ERPLibre's settings library (see [Inside ERPLibre](#inside-erplibre)), so on its own it imports every plugin. A plugin that raises on import, has no `PLUGIN`, declares another `api` than `PLUGIN_API`, takes a page id already taken, or fails in `setup` is refused and the others keep running; the journal names the plugin and the reason.

<!-- [fr] -->

### Couper des plugins

Le réglage `DECK_PLUGINS_OFF` de `$XDG_CONFIG_HOME/erplibre-home/streamdeck.conf` est une liste d'identifiants de plugins, séparés par des virgules, qui ne sont pas importés. Dans ERPLibre, le régler depuis TODO › ERPLibre Home › Plugins on/off, ou à la main ; le deck le lit par la bibliothèque de réglages d'ERPLibre (voir [Dans ERPLibre](#dans-erplibre)), si bien que seul, il importe tous les plugins. Un plugin qui lève à l'import, n'a pas de `PLUGIN`, déclare un autre `api` que `PLUGIN_API`, prend un identifiant de page déjà pris ou échoue dans `setup` est refusé et les autres continuent ; le journal nomme le plugin et la raison.

<!-- [common] -->

```
DECK_PLUGINS_OFF=bluetooth,translate
```

<!-- [en] -->

### Home key layout (`keymap.json`)

Without a layout, the home buttons take row 0 in their order (and row 1 on a deck of three rows or more), and the dashboard every other key from row 1 on. `~/.config/erplibre-home/keymap.json` replaces that for the deck models it names. The GNOME extension writes it, from a layout Odoo offers and the employee applies; the deck program reads it each time it starts, or its deck comes back. Format 1:

<!-- [fr] -->

### Disposition des touches d'accueil (`keymap.json`)

Sans disposition, les boutons d'accueil prennent la rangée 0 dans leur ordre (et la rangée 1 sur un deck de trois rangées ou plus), et le tableau de bord toutes les autres touches à partir de la rangée 1. `~/.config/erplibre-home/keymap.json` remplace cela pour les modèles de deck qu'il nomme. L'extension GNOME l'écrit, à partir d'une disposition qu'Odoo propose et que l'employé applique ; le programme du deck le lit à chaque démarrage, ou au retour de son deck. Format 1 :

<!-- [common] -->

```json
{"format": 1, "revision": 7,
 "layouts": {"0084": {"keys": [
   {"key": 0, "action": "plugin:timers", "icon": "timer", "label": "Timers"},
   {"key": 1, "action": "tiles"},
   {"key": 2, "action": "empty"}]}}}
```

<!-- [en] -->

- `layouts`: by USB product id, 4 lowercase hex digits, at most 16 models.
- `keys`: at most the model's key count. `key` is an integer from 0 to the key count minus one, used once. `action` is `plugin:<id>` (that plugin's home button), `tiles` (a dashboard key) or `empty` (a black key). `icon` is a name of `ui/icons.py` `ICONS`, or absent. `label` has at most 16 characters and no control character, or is absent.
- With a layout, it is the home screen: a plugin's home button goes to the key that names it, and a plugin with a home button the layout does not name gets no key. Fixtures (the mic, the layout shortcuts) only take keys the layout does not name. The dashboard takes the `tiles` keys, then every key left. `icon` and `label` replace the icon and the text of the home button; its colour and state stay the plugin's.
- A missing or unreadable file, another `format`, more than 16 models, a model absent, a layout without a `keys` list or with more entries than keys: the automatic layout. An invalid entry is skipped; a `plugin:<id>` of a plugin turned off or absent leaves its key black. Each case is one journal line, ten at most per start, then one line counting the rest.
- Dials and the touch screen of the Stream Deck + are outside format 1; the controller (`DECK_PROGRAM=controller`) ignores the file.

`--catalog` gives what a layout may name on this checkout: `{"format": 1, "actions": [...], "icons": [...], "models": {"0084": {"cols": 4, "rows": 2, "keys": 8}, ...}}`. The actions are, sorted, the loaded plugins with a home button and the plugins turned off by `DECK_PLUGINS_OFF` (listed from their file name without being imported, and left out when their file, read without being run, shows they have no home button: a `PLUGIN = Plugin(...)` with no `home_button`, or `home_button=None`), then `tiles` and `empty`; an id of more than 64 characters, which a layout cannot name, is left out; the models are every deck with a screen the Stream Deck library knows.

<!-- [fr] -->

- `layouts` : par identifiant de produit USB, 4 chiffres hexadécimaux minuscules, au plus 16 modèles.
- `keys` : au plus le nombre de touches du modèle. `key` est un entier de 0 au nombre de touches moins un, employé une fois. `action` vaut `plugin:<id>` (le bouton d'accueil de ce plugin), `tiles` (une touche du tableau de bord) ou `empty` (une touche noire). `icon` est un nom de `ui/icons.py` `ICONS`, ou absent. `label` a au plus 16 caractères et aucun caractère de contrôle, ou est absent.
- Avec une disposition, elle fait l'écran d'accueil : le bouton d'accueil d'un plugin va à la touche qui le nomme, et un plugin à bouton d'accueil que la disposition ne nomme pas n'a pas de touche. Les fixtures (le micro, les raccourcis de dispositions de fenêtres) ne prennent que des touches que la disposition ne nomme pas. Le tableau de bord prend les touches `tiles`, puis toutes les touches restantes. `icon` et `label` remplacent l'icône et le texte du bouton d'accueil ; sa couleur et son état restent ceux du plugin.
- Fichier absent ou illisible, autre `format`, plus de 16 modèles, modèle absent, disposition sans liste `keys` ou avec plus d'entrées que de touches : la disposition automatique. Une entrée invalide est sautée ; un `plugin:<id>` d'un plugin coupé ou absent laisse sa touche noire. Chaque cas fait une ligne de journal, dix au plus par démarrage, puis une ligne qui compte le reste.
- Les molettes et l'écran tactile du Stream Deck + sont hors du format 1 ; le contrôleur (`DECK_PROGRAM=controller`) ignore le fichier.

`--catalog` donne ce qu'une disposition peut nommer sur ce checkout : `{"format": 1, "actions": [...], "icons": [...], "models": {"0084": {"cols": 4, "rows": 2, "keys": 8}, ...}}`. Les actions sont, triés, les plugins chargés à bouton d'accueil et les plugins coupés par `DECK_PLUGINS_OFF` (listés d'après leur nom de fichier sans être importés, et laissés de côté quand leur fichier, lu sans être exécuté, montre qu'ils n'ont pas de bouton d'accueil : un `PLUGIN = Plugin(...)` sans `home_button`, ou avec `home_button=None`), puis `tiles` et `empty` ; un identifiant de plus de 64 caractères, qu'une disposition ne peut nommer, est laissé de côté ; les modèles sont tous les decks à écran que connaît la bibliothèque Stream Deck.

<!-- [en] -->

### Writing a plugin

A plugin is one `.py` file. Its id is its file stem (`[a-z][a-z0-9_]*`; files starting with `_` are skipped) and it exposes `PLUGIN = Plugin(api=PLUGIN_API, ...)`. Every callable receives a `Context` (`ctx`) and runs with the kernel lock held. This plugin adds a home button and one page with a back key:

<!-- [fr] -->

### Écrire un plugin

Un plugin est un fichier `.py`. Son identifiant est le nom du fichier sans extension (`[a-z][a-z0-9_]*` ; les fichiers qui commencent par `_` sont ignorés) et il expose `PLUGIN = Plugin(api=PLUGIN_API, ...)`. Chaque fonction reçoit un `Context` (`ctx`) et s'exécute avec le verrou du noyau tenu. Ce plugin ajoute un bouton d'accueil et une page avec une touche retour :

<!-- [common] -->

```python
from erplibre_streamdeck.plugin import (
    PLUGIN_API, HomeButton, KeyFace, Page, Plugin,
)


def _keys(geo):
    return {"back": 0} if geo.cols >= 2 else None


def _render(ctx):
    for key in range(ctx.geo.total_keys):
        ctx.set_key(key, (20, 20, 30))
    ctx.set_key(0, (60, 60, 60), ctx.t("BACK"))


def _handle(ctx, key):
    if key == 0:
        ctx.home()


PLUGIN = Plugin(
    api=PLUGIN_API,
    pages=[Page("hello", _keys, _render, _handle)],
    home_button=HomeButton(
        90,
        face=lambda ctx: KeyFace((30, 90, 60), "HELLO"),
        press=lambda ctx: ctx.goto("hello"),
    ),
)
```

<!-- [en] -->

A `Plugin` also takes `fixtures` (keys placed on the home screen), `tiles` (dashboard tiles), `home_tick`, `setup(ctx)` and `shutdown(ctx)`; `plugin.py` documents each. `shutdown` runs with the lock held (without it when a key press still holds it after 5 s): it must not take `ctx.locked()` nor wait for a thread that does. A thread a plugin starts takes the lock with `with ctx.locked():`.

A plugin of the user goes in `$XDG_CONFIG_HOME/erplibre-home/deck-plugins/` (`~/.config/erplibre-home/deck-plugins/` when unset), and replaces a plugin of the repository with the same id. **Trust:** user plugins run inside the deck service with the user's rights, like a shell profile; put there only code you wrote or read.

<!-- [fr] -->

Un `Plugin` prend aussi `fixtures` (touches placées sur l'accueil), `tiles` (tuiles du tableau de bord), `home_tick`, `setup(ctx)` et `shutdown(ctx)` ; `plugin.py` documente chacun. `shutdown` s'exécute verrou tenu (sans lui quand une touche le tient encore après 5 s) : il ne doit ni prendre `ctx.locked()` ni attendre un fil qui le prend. Un fil lancé par un plugin prend le verrou par `with ctx.locked():`.

Un plugin de l'utilisateur va dans `$XDG_CONFIG_HOME/erplibre-home/deck-plugins/` (`~/.config/erplibre-home/deck-plugins/` si la variable est absente) et remplace le plugin du dépôt de même identifiant. **Confiance :** les plugins de l'utilisateur s'exécutent dans le service du deck avec les droits de l'utilisateur, comme un profil de shell ; n'y mettre que du code écrit ou relu par soi.

<!-- [en] -->

#### Slow actions, polls and settings

A callable runs with the lock held, so it must not wait on a process. `ctx.run_blocking(work, then=None)` runs `work()` in a thread, without the lock, and returns `True`:

- `work` takes no argument and touches only what it captured before the call, plus `ctx.dbus` and `ctx.log`; never `ctx` itself.
- The pressed key shows "…" while the job runs and the rest of the deck stays usable.
- On the next loop pass, under the lock, the kernel calls `then(ctx, result, error)` (`error` is the exception `work` raised, or `None`). `then` renders itself, like a handler. Without `then`, the kernel flashes OK when `error` is `None` and the result is truthy, ERR otherwise, and renders.
- A plugin has one job at a time: `run_blocking` while one runs returns `False` and flashes ERR. A press that would reach a busy plugin flashes ERR without calling it; key 0 of its page (BACK on most pages) goes home instead. Its polls and ticks wait.
- A job that raises is journaled once, with its traceback, before `then` runs.

`Plugin.polls` is a list of `Poll(period, active, read, store)`. A render reads `ctx.state()` and starts no process; a poll fills that state:

- `active(ctx)` (lock held) says whether the data is needed now, for example because the plugin's page shows.
- `read()` (no lock) runs the processes and returns the data. It never touches `ctx`; a failing `read` keeps the previous data.
- A `read` that writes its own failures wraps its pass in `with repeat_log.watch() as log:`, where `repeat_log = RepeatLog(write, what)` is created once with the module: `log(msg)` records a failure, written once while it repeats on every pass, again when it changes, and `what: recovered` is written on the first pass without failure. A pass that comes more than `RepeatLog.FORGET_SEC` (10 s) after the last one, the poll having been inactive, starts afresh: its failures are written again.
- `store(ctx, data)` (lock held) keeps the data in `ctx.state()` and returns `True` to ask for one render.

`ctx.setting(name, default=None)` reads a deck setting given to the kernel at start (`session_refresh_sec`, from `DECK_SESSION_REFRESH_SEC`), or `default`. A render may run before the first poll ends: set the state in `setup(ctx)`. This plugin runs a job on a key press and shows a counter that a poll refreshes:

<!-- [fr] -->

#### Actions lentes, sondages et réglages

Une fonction s'exécute verrou tenu : elle ne doit pas attendre un processus. `ctx.run_blocking(work, then=None)` exécute `work()` dans un fil, sans le verrou, et rend `True` :

- `work` ne prend aucun argument et ne touche que ce qu'elle a capturé avant l'appel, plus `ctx.dbus` et `ctx.log` ; jamais `ctx`.
- La touche pressée affiche « … » pendant la tâche et le reste du deck reste utilisable.
- Au prochain passage de la boucle, verrou tenu, le noyau appelle `then(ctx, result, error)` (`error` est l'exception levée par `work`, ou `None`). `then` fait son propre rendu, comme un gestionnaire. Sans `then`, le noyau fait clignoter OK quand `error` vaut `None` et que le résultat est vrai, ERR sinon, et rend.
- Un plugin n'a qu'une tâche à la fois : `run_blocking` pendant qu'une tâche tourne rend `False` et fait clignoter ERR. Une touche qui atteindrait un plugin occupé clignote en ERR sans l'appeler ; la touche 0 de sa page (RETOUR sur la plupart des pages) ramène à l'accueil. Ses sondages et ses ticks attendent.
- Une tâche qui lève est inscrite une fois au journal, avec sa trace, avant l'appel de `then`.

`Plugin.polls` est une liste de `Poll(period, active, read, store)`. Un rendu lit `ctx.state()` et ne lance aucun processus ; un sondage remplit cet état :

- `active(ctx)` (verrou tenu) dit si la donnée est utile maintenant, par exemple parce que la page du plugin est affichée.
- `read()` (sans verrou) lance les processus et rend la donnée. Il ne touche jamais `ctx` ; un `read` qui échoue garde la donnée précédente.
- Un `read` qui inscrit ses propres échecs enveloppe son passage dans `with repeat_log.watch() as log:`, où `repeat_log = RepeatLog(write, what)` est créé une fois avec le module : `log(msg)` consigne un échec, inscrit une fois tant qu'il se répète à chaque passage, de nouveau quand il change, et `what: recovered` est inscrit au premier passage sans échec. Un passage qui vient plus de `RepeatLog.FORGET_SEC` (10 s) après le précédent, le sondage ayant été inactif, repart de zéro : ses échecs sont inscrits de nouveau.
- `store(ctx, data)` (verrou tenu) garde la donnée dans `ctx.state()` et rend `True` pour demander un rendu.

`ctx.setting(name, default=None)` lit un réglage du deck donné au noyau au démarrage (`session_refresh_sec`, issu de `DECK_SESSION_REFRESH_SEC`), ou `default`. Un rendu peut avoir lieu avant la fin du premier sondage : poser l'état dans `setup(ctx)`. Ce plugin lance une tâche à l'appui d'une touche et affiche un compteur qu'un sondage rafraîchit :

<!-- [common] -->

```python
import subprocess

from erplibre_streamdeck.plugin import (
    PLUGIN_API, HomeButton, KeyFace, Page, Plugin, Poll,
)


def _setup(ctx):
    ctx.state().lines = 0


def _keys(geo):
    return {"back": 0, "run": 1} if geo.total_keys > 1 else None


def _render(ctx):
    for key in range(ctx.geo.total_keys):
        ctx.set_key(key, (20, 20, 30))
    ctx.set_key(0, (60, 60, 60), ctx.t("BACK"))
    ctx.set_key(1, (30, 90, 60), f"RUN\n{ctx.state().lines}")


def _work():
    # no ctx, no lock / ni ctx, ni verrou
    done = subprocess.run(["uptime"], capture_output=True, timeout=5)
    return done.returncode == 0


def _then(ctx, result, error):
    ctx.flash(error is None and result)
    ctx.render()


def _handle(ctx, key):
    if key == 0:
        ctx.home()
    elif key == 1:
        ctx.run_blocking(_work, _then)


def _read():
    done = subprocess.run(["uptime"], capture_output=True, timeout=5)
    return len(done.stdout.splitlines())


def _store(ctx, lines):
    changed = ctx.state().lines != lines
    ctx.state().lines = lines
    return changed


PLUGIN = Plugin(
    api=PLUGIN_API,
    pages=[Page("hello", _keys, _render, _handle)],
    home_button=HomeButton(
        90,
        face=lambda ctx: KeyFace((30, 90, 60), "HELLO"),
        press=lambda ctx: ctx.goto("hello"),
    ),
    polls=[Poll(2.0, lambda ctx: ctx.page == "hello", _read, _store)],
    setup=_setup,
)
```

<!-- [en] -->

## Translator

The speech-to-text translator (`translator.py`, its page in the
`translate` plugin, `translator_doctor.py`, `translator_test.py`,
`translator_stream.py`) is described in [TRANSLATOR.md](TRANSLATOR.md).

## Inside ERPLibre

ERPLibre clones this repository at `script/stream_deck/deck/`, installs
`requirements.txt` in its `.venv.streamdeck`, and runs the deck program
as its `erplibre-home-streamdeck` user service. The deck then finds the
ERPLibre checkout three levels up from the clone, or in the variable
`ERPLIBRE_ROOT` when it is set and not empty, and uses these files of
it:

- `script/install/erplibre_home_settings.sh`, which reads
  `DECK_PLUGINS_OFF` and `DECK_SESSION_REFRESH_SEC` in `streamdeck.conf`;
- `script/todo/todo.py` and `.venv.erplibre`, for the TODO terminals;
- `script/todo/source_todo.sh`, for key 0 of the controller.

Without a checkout, the deck runs with the default settings, and the TODO
keys flash ERR. The GNOME extension, a repository of its own
([erplibre-home-gnome-extension](https://github.com/TechnoLibre/erplibre-home-gnome-extension)),
gives the deck the D-Bus methods of window tiling, layouts, timers and
sessions; without it, those keys flash ERR.

<!-- [fr] -->

## Traducteur

Le traducteur vocal (`translator.py`, sa page dans le plugin `translate`,
`translator_doctor.py`, `translator_test.py`, `translator_stream.py`) est
décrit dans [TRANSLATOR.fr.md](TRANSLATOR.fr.md).

## Dans ERPLibre

ERPLibre clone ce dépôt dans `script/stream_deck/deck/`, installe
`requirements.txt` dans son `.venv.streamdeck`, et lance le programme du
deck comme son service utilisateur `erplibre-home-streamdeck`. Le deck
trouve alors le checkout d'ERPLibre trois niveaux au-dessus du clone, ou
dans la variable `ERPLIBRE_ROOT` quand elle est posée et non vide, et se
sert de ces fichiers :

- `script/install/erplibre_home_settings.sh`, qui lit `DECK_PLUGINS_OFF`
  et `DECK_SESSION_REFRESH_SEC` dans `streamdeck.conf` ;
- `script/todo/todo.py` et `.venv.erplibre`, pour les terminaux TODO ;
- `script/todo/source_todo.sh`, pour la touche 0 du contrôleur.

Sans checkout, le deck tourne avec les réglages par défaut, et les
touches TODO clignotent en ERR. L'extension GNOME, un dépôt à part
([erplibre-home-gnome-extension](https://github.com/TechnoLibre/erplibre-home-gnome-extension)),
donne au deck les méthodes D-Bus du tuilage, des dispositions, des
minuteurs et des sessions ; sans elle, ces touches clignotent en ERR.

<!-- [en] -->

## Tests

The tests replace the Stream Deck library, Pillow and every outside
command, and need no deck. The pages are checked against the goldens of
`tests/fixtures/erplibre_streamdeck/`;
`STREAMDECK_GOLDEN=update-from-package` writes them from the run instead.
A few tests run the real program, with the interpreter of
`STREAMDECK_PYTHON` or the one running the tests, and are skipped when it
lacks the Stream Deck library. Outside ERPLibre, the settings library is
replaced by `tests/fixtures/erplibre_home_settings.sh`.

<!-- [fr] -->

## Tests

Les tests remplacent la bibliothèque Stream Deck, Pillow et toute commande
extérieure, et ne demandent aucun deck. Les pages se comparent aux golden
de `tests/fixtures/erplibre_streamdeck/` ;
`STREAMDECK_GOLDEN=update-from-package` les écrit plutôt depuis la passe.
Quelques tests lancent le vrai programme, sous l'interpréteur de
`STREAMDECK_PYTHON` ou celui des tests, et sont sautés quand il n'a pas la
bibliothèque Stream Deck. Hors d'ERPLibre, la bibliothèque de réglages est
remplacée par `tests/fixtures/erplibre_home_settings.sh`.

<!-- [end] -->
<!-- [common] -->

```bash
.venv/bin/python -m unittest discover -s tests
```

<!-- [en] -->

## Files

<!-- [fr] -->

## Fichiers

<!-- [common] -->

```
├── CONTRACT.md                # What ERPLibre relies on / Ce dont ERPLibre dépend
├── CHANGELOG.md               # Changes / Changements
├── requirements.txt           # Python dependencies / Dépendances Python
├── deck_lock.py               # One deck program at a time / Un programme à la fois
├── erplibre_streamdeck/       # Deck program package (plugins) / Paquet du deck
├── erplibre_controller.py     # Controller / Contrôleur
├── keyboard_talk.py           # Keyboard automation / Automatisation clavier
├── translator*.py             # Speech-to-text / Traducteur vocal
├── Assets/                    # Controller images and fonts / Images et polices
├── draw_assets.py             # Draws the controller images / Dessine les images
└── tests/                     # Unit tests and goldens / Tests et golden
```

<!-- [en] -->

## License

AGPL-3.0 — [TechnoLibre](http://www.technolibre.ca), see `LICENSE`.

Third-party files in `Assets/` keep their own license, compatible with
AGPL-3.0: `Assets/ATTRIBUTION.txt` gives each file its license and source.

<!-- [fr] -->

## Licence

AGPL-3.0 — [TechnoLibre](http://www.technolibre.ca), voir `LICENSE`.

Les fichiers tiers de `Assets/` gardent leur propre licence, compatible avec
l'AGPL-3.0 : `Assets/ATTRIBUTION.txt` donne pour chacun sa licence et sa
source.
