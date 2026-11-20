
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
needs a udev rule to open without root. On Debian and Ubuntu:


```bash
sudo apt install -y libudev-dev libusb-1.0-0-dev libhidapi-libusb0 python3-venv
sudo tee /etc/udev/rules.d/70-streamdeck.rules << 'RULES'
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="0fd9", TAG+="uaccess"
RULES
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Then clone the repository and install its packages in a venv; every
command below runs from the repository root, under that venv:


```bash
git clone https://github.com/TechnoLibre/erplibre-streamdeck.git
cd erplibre-streamdeck
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python erplibre_streamdeck
```


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


```bash
python erplibre_controller.py
python erplibre_controller.py --help
```


### keyboard_talk.py

Keyboard automation script, key 3 of the controller. Uses `wmctrl` to target a terminal window, then sends an automated key sequence via the `keyboard` library, under `sudo`.


## Deck program

`erplibre_streamdeck/` is the deck program of ERPLibre Home (`DECK_PROGRAM=tiler`, `make streamdeck_erplibre` inside ERPLibre). It is a package run as a directory: a small kernel owns the deck, the lock, the flash, the home screen and the key dispatch, and every feature is a plugin.


```bash
python erplibre_streamdeck
python erplibre_streamdeck --list-plugins
python erplibre_streamdeck --catalog
python erplibre_streamdeck --help
```


`--list-plugins` prints what the loader finds (one line per plugin: `active`, `off`, `replaced by user` or `refused` with its reason; `unreadable` for a plugin directory it cannot list) without opening the deck or taking its lock. `-h` and `--help` print the usage, the settings file and the exit codes (2: deck lock held or bad option, 3: no Stream Deck with a screen, 143: SIGTERM), then exit 0; any other argument prints the usage on stderr and exits 2. Neither takes the lock nor needs the Stream Deck library. `--catalog` prints, as JSON, what a `keymap.json` layout may name (see below); it reads the deck models from the Stream Deck library without opening any deck, and takes no lock. Layout of the package:


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


### Turning plugins off

The setting `DECK_PLUGINS_OFF` in `$XDG_CONFIG_HOME/erplibre-home/streamdeck.conf` is a comma-separated list of plugin ids that are not imported. Inside ERPLibre, set it from TODO › ERPLibre Home › Plugins on/off, or by hand; the deck reads it through ERPLibre's settings library (see [Inside ERPLibre](#inside-erplibre)), so on its own it imports every plugin. A plugin that raises on import, has no `PLUGIN`, declares another `api` than `PLUGIN_API`, takes a page id already taken, or fails in `setup` is refused and the others keep running; the journal names the plugin and the reason.


```
DECK_PLUGINS_OFF=bluetooth,translate
```


### Home key layout (`keymap.json`)

Without a layout, the home buttons take row 0 in their order (and row 1 on a deck of three rows or more), and the dashboard every other key from row 1 on. `~/.config/erplibre-home/keymap.json` replaces that for the deck models it names. The GNOME extension writes it, from a layout Odoo offers and the employee applies; the deck program reads it each time it starts, or its deck comes back. Format 1:


```json
{"format": 1, "revision": 7,
 "layouts": {"0084": {"keys": [
   {"key": 0, "action": "plugin:timers", "icon": "timer", "label": "Timers"},
   {"key": 1, "action": "tiles"},
   {"key": 2, "action": "empty"}]}}}
```


- `layouts`: by USB product id, 4 lowercase hex digits, at most 16 models.
- `keys`: at most the model's key count. `key` is an integer from 0 to the key count minus one, used once. `action` is `plugin:<id>` (that plugin's home button), `tiles` (a dashboard key) or `empty` (a black key). `icon` is a name of `ui/icons.py` `ICONS`, or absent. `label` has at most 16 characters and no control character, or is absent.
- With a layout, it is the home screen: a plugin's home button goes to the key that names it, and a plugin with a home button the layout does not name gets no key. Fixtures (the mic, the layout shortcuts) only take keys the layout does not name. The dashboard takes the `tiles` keys, then every key left. `icon` and `label` replace the icon and the text of the home button; its colour and state stay the plugin's.
- A missing or unreadable file, another `format`, more than 16 models, a model absent, a layout without a `keys` list or with more entries than keys: the automatic layout. An invalid entry is skipped; a `plugin:<id>` of a plugin turned off or absent leaves its key black. Each case is one journal line, ten at most per start, then one line counting the rest.
- Dials and the touch screen of the Stream Deck + are outside format 1; the controller (`DECK_PROGRAM=controller`) ignores the file.

`--catalog` gives what a layout may name on this checkout: `{"format": 1, "actions": [...], "icons": [...], "models": {"0084": {"cols": 4, "rows": 2, "keys": 8}, ...}}`. The actions are, sorted, the loaded plugins with a home button and the plugins turned off by `DECK_PLUGINS_OFF` (listed from their file name without being imported, and left out when their file, read without being run, shows they have no home button: a `PLUGIN = Plugin(...)` with no `home_button`, or `home_button=None`), then `tiles` and `empty`; an id of more than 64 characters, which a layout cannot name, is left out; the models are every deck with a screen the Stream Deck library knows.


### Writing a plugin

A plugin is one `.py` file. Its id is its file stem (`[a-z][a-z0-9_]*`; files starting with `_` are skipped) and it exposes `PLUGIN = Plugin(api=PLUGIN_API, ...)`. Every callable receives a `Context` (`ctx`) and runs with the kernel lock held. This plugin adds a home button and one page with a back key:


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


A `Plugin` also takes `fixtures` (keys placed on the home screen), `tiles` (dashboard tiles), `home_tick`, `setup(ctx)` and `shutdown(ctx)`; `plugin.py` documents each. `shutdown` runs with the lock held (without it when a key press still holds it after 5 s): it must not take `ctx.locked()` nor wait for a thread that does. A thread a plugin starts takes the lock with `with ctx.locked():`.

A plugin of the user goes in `$XDG_CONFIG_HOME/erplibre-home/deck-plugins/` (`~/.config/erplibre-home/deck-plugins/` when unset), and replaces a plugin of the repository with the same id. **Trust:** user plugins run inside the deck service with the user's rights, like a shell profile; put there only code you wrote or read.


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


## Tests

The tests replace the Stream Deck library, Pillow and every outside
command, and need no deck. The pages are checked against the goldens of
`tests/fixtures/erplibre_streamdeck/`;
`STREAMDECK_GOLDEN=update-from-package` writes them from the run instead.
A few tests run the real program, with the interpreter of
`STREAMDECK_PYTHON` or the one running the tests, and are skipped when it
lacks the Stream Deck library. Outside ERPLibre, the settings library is
replaced by `tests/fixtures/erplibre_home_settings.sh`.


```bash
.venv/bin/python -m unittest discover -s tests
```


## Files


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


## License

AGPL-3.0 — [TechnoLibre](http://www.technolibre.ca), see `LICENSE`.

Third-party files in `Assets/` keep their own license, compatible with
AGPL-3.0: `Assets/ATTRIBUTION.txt` gives each file its license and source.
