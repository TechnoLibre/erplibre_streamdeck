# Contract between the deck program and ERPLibre

**Contract version: 1.0**

The deck program runs on its own (see `README.md`). ERPLibre also clones
this repository at `script/stream_deck/deck/`, by Google Repo or by
`install_erplibre_home.sh --stream-deck`, installs `requirements.txt` in
its `.venv.streamdeck`, and runs the deck from its installer, its systemd
user unit, its make targets and its TODO menu. The GNOME extension of
ERPLibre Home, a repository of its own, runs the deck's catalog and
shares files with it. This file states what each side relies on in that
case.

`erplibre_streamdeck.CONTRACT_VERSION` carries the same version, and
ERPLibre records the one it was built against in
`script/stream_deck/deck_contract`; the tests of both sides check it. A
MINOR version adds to the contract and keeps everything it stated; a
MAJOR version changes or removes something, and lands on both sides
together.

Paths below are relative to the root of this repository unless they start
with `$`, `~` or `script/`; `script/…` paths are relative to the ERPLibre
checkout.

## Locating ERPLibre

The deck finds the ERPLibre checkout once, at import, in
`erplibre_streamdeck.paths.REPO_ROOT` (`erplibre_root()`):

1. `$ERPLIBRE_ROOT`, when set and not empty, made absolute against the
   current directory; its content is not checked.
2. Otherwise, when the repository root ends with
   `script/stream_deck/deck`, the directory three levels above it: the
   checkout that cloned it there.
3. Otherwise none (`REPO_ROOT` is `None`): the deck runs on its own.

A link to the clone does not count: the location is the one the files
resolve to. Without a checkout, the settings of `streamdeck.conf` are not
read (the defaults apply, with one journal line), the TODO key of the
deck flashes ERR, and key 0 of the controller prints a line.

## What ERPLibre and the extension rely on

1. **Layout.**
   - `erplibre_streamdeck/`: the deck program, a package run as a
     directory, `python erplibre_streamdeck` (`DECK_PROGRAM=tiler`). It
     puts the repository root first on `sys.path`, from any current
     directory.
   - `erplibre_controller.py`: the controller (`DECK_PROGRAM=controller`).
   - `erplibre_streamdeck/plugins/*.py`: the plugins of the repository.
     A plugin is named by its file without `.py`, of the pattern
     `[a-z][a-z0-9_]*`; a file starting with `_` is no plugin. The user
     plugins live in `$XDG_CONFIG_HOME/erplibre-home/deck-plugins/`
     (`~/.config` when unset or empty), named the same way, and replace a
     plugin of the repository with the same name.
   - `deck_lock.py`: the deck lock, standard library only, loaded by its
     path by ERPLibre's TODO status.
   - `requirements.txt`: the packages of the interpreter that runs every
     entry point, at least `streamdeck`, `pyudev`, `Pillow`,
     `opencv-python`, `requests` and `keyboard`.
   - `translator.py`, the speech-to-text module; `translator_doctor.py`
     (`--recommend` prints the name of one ollama model on stdout),
     `translator_test.py` and `translator_stream.py`, which ERPLibre's
     make targets run with the same interpreter.
   - `keyboard_talk.py`, `Assets/` (the controller's images and fonts)
     and `draw_assets.py`.
   - `tests/`, run by `python -m unittest discover -s tests` from the
     repository root.
2. **Deck program command line,** `python erplibre_streamdeck [option]`:
   - no option: takes the deck lock as `tiler`, then runs the deck;
   - `--list-plugins`: one line per plugin the loader finds (`active`,
     `off`, `replaced by user`, `refused` with its reason; `unreadable`
     for a plugin directory it cannot list), exit 0;
   - `--catalog`: one JSON object on stdout, exit 0: `{"format": 1,
     "actions": [<action>], "icons": [<icon>], "models": {<model>:
     {"cols": <integer>, "rows": <integer>, "keys": <integer>}}}`. The
     actions are, sorted, `plugin:<id>` of the plugins loaded with a home
     button and of the plugins `DECK_PLUGINS_OFF` turns off (never
     imported; left out when their file, read without being run, shows no
     home button), then `tiles` and `empty`; an id longer than 64
     characters is left out. The icons are the names of
     `erplibre_streamdeck.ui.icons.ICONS`. The models are every deck with
     a screen the Stream Deck library knows, by USB product id in 4
     lowercase hex digits. What a plugin prints at import goes to stderr;
   - `-h`, `--help`: the usage, the settings file and the exit codes on
     stdout, exit 0;
   - any other argument, or `--list-plugins` with `--catalog`: the usage
     on stderr, exit 2.

   `--list-plugins`, `--catalog` and `--help` neither open a deck nor
   take the deck lock; `--help` and a bad argument import neither the
   Stream Deck library nor Pillow.
3. **Controller command line,** `python erplibre_controller.py`: no
   option takes the deck lock as `controller` and drives every deck with
   a screen; `-h` and `--help` print the usage and exit 0, any other
   argument prints it on stderr and exits 2, both before importing cv2,
   Pillow or the Stream Deck library. While it runs, its pid is in
   `$XDG_CACHE_HOME/erplibre-home/controller.pid` (`~/.cache` when
   unset), assigned to the module constant `PIDFILE`; the file is removed
   at exit.
4. **Exit codes.** The systemd unit does not restart 2 and 3.

   | Code | Deck program | Controller |
   | --- | --- | --- |
   | 0 | ended, or `--help`, `--list-plugins`, `--catalog` | ended, or `--help` |
   | 1 | unexpected error, traceback on stderr | the driver cannot probe, or unexpected error |
   | 2 | deck lock held by another program (`deck_lock.BUSY_EXIT`), or bad option | same |
   | 3 | no Stream Deck with a screen (`deck_lock.NO_DECK_EXIT`) | — |
   | 143 | SIGTERM, after the deck is reset | same |

5. **Deck lock.** `deck_lock.lock_path()` is
   `$XDG_RUNTIME_DIR/erplibre-home/deck.lock`, or, without
   `XDG_RUNTIME_DIR`, `erplibre-home-<uid>/deck.lock` in the system
   temporary directory; its directory belongs to the user and is closed
   to the other accounts, or the lock is refused. The holder takes
   an exclusive `flock` on it for its whole life and writes
   `<pid> <program> <start>`, `<start>` being field 22 of
   `/proc/<pid>/stat` (a text without it still reads). `deck_lock.py`
   offers `BUSY_EXIT`, `NO_DECK_EXIT`, `lock_path(environ=None)`,
   `parse_holder(text)`, `holder(path=None)`,
   `holder_running(held, proc="/proc")`, `holder_pids(path=None)`,
   `acquire(program, path=None)` (raises `DeckBusy`),
   `acquire_or_exit(program, path=None)` and `exit_on_sigterm()` (SIGTERM
   raises `SigtermExit(143)`).
6. **Settings, `streamdeck.conf`.** At each start the deck reads, through
   ERPLibre's settings library (see What the deck relies on),
   `DECK_PLUGINS_OFF`, the comma-separated ids of the plugins not
   imported, and `DECK_SESSION_REFRESH_SEC`, the period of the session
   pages, from 0.5 to 60, 1 otherwise. `DECK_PROGRAM` and `GAMES` are
   ERPLibre's; the deck ignores them.
7. **Files.** `~` stands for the home directory, whatever the XDG
   variables say, where this list writes it literally.
   - `~/.config/erplibre-home/keymap.json`: read at each start, and when
     the deck comes back; written by the extension only. Format 1:
     `{"format": 1, "revision": <integer>, "layouts": {<model>: {"keys":
     [{"key": <integer>, "action": <action>, "icon": <icon>, "label":
     <text>}]}}}`, at most 16 models, `icon` and `label` optional, a
     label of at most 16 characters without a control character. The deck
     reads it as the extension's contract (item 10 of What ERPLibre
     relies on) writes it, and is the more lenient reader: a missing or
     unreadable file, another `format`, or a model absent gives the
     automatic layout; an invalid entry is skipped. Dials and the touch
     screen are outside format 1; the controller ignores the file.
   - `~/.config/erplibre-home/settings.json` (display style, accessibility
     and `translator_*` keys) and `layouts.json` (window layouts): the
     deck's own, each replaced atomically. Another program that writes
     `settings.json` reloads it and changes only its own keys.
   - `~/.config/erplibre-home/translator-history.json`: the translator's
     history.
   - `$XDG_STATE_HOME/erplibre-home/` (`~/.local/state` when unset):
     `todo_terminals.json`, the TODO terminals the deck opened, and
     `todo/`, their logs, both written by the deck; `claude/` and `mpv/`,
     records the deck reads, as the extension's contract states.
8. **Python modules** ERPLibre imports, with the repository root on
   `sys.path`: `erplibre_streamdeck.keymap` (`FORMAT`, `MAX_MODELS`,
   `LABEL_MAX`, `PLUGIN_ID`, `FIXED_ACTIONS`, `Entry`, `load`,
   `layout_for`, `catalog`), `erplibre_streamdeck.paths` (`state_dir`,
   `KEYMAP_FILE`, `SETTINGS_FILE`, `REPO_ROOT`, `DECK_DIR`),
   `erplibre_streamdeck.plugin.Geometry` and
   `erplibre_streamdeck.ui.icons.ICONS`. `erplibre_streamdeck` and
   `erplibre_streamdeck.paths` import only the standard library. The deck
   calls the extension only through `erplibre_streamdeck/dbus.py`
   (`dbus.call("<Method>", …)` with a literal method name) and
   `translator.py`, which ERPLibre's tests read to check those names.

## What the deck relies on

1. **From ERPLibre,** under the checkout `REPO_ROOT`:
   - `script/install/erplibre_home_settings.sh`, a bash library that
     reads `$XDG_CONFIG_HOME/erplibre-home/streamdeck.conf` (the last
     `KEY=` line of a key wins), with the functions `deck_plugins_off`
     (one plugin id per line, exit 0) and `deck_session_refresh_sec` (one
     number, exit 0). The deck sources it with `bash`, within 10 s;
     otherwise the defaults apply with one journal line.
     `tests/fixtures/erplibre_home_settings.sh` is the test double of
     these two functions;
   - `script/todo/todo.py` and `.venv.erplibre/bin/activate`, for the TODO
     terminals of the deck; `script/todo/source_todo.sh`, run from the
     checkout, for key 0 of the controller;
   - the make targets `streamdeck_translator_install_*`, which the
     translator's messages name.
2. **From the GNOME extension:** the D-Bus object `/org/gnome/Shell/
   Extensions/ERPLibreHome`, interface
   `org.gnome.Shell.Extensions.ERPLibreHome`, on `org.gnome.Shell`, and
   the methods of its contract's table. Without the extension a key that
   needs it flashes ERR; the rest of the deck works.

## Changing this contract

A change to anything above updates this file, `CONTRACT_VERSION` and
`CHANGELOG.md` in the same commit. `tests/test_contract.py` checks that
the version agrees, that the entry points and exit codes are the ones
stated, and the rules of Locating ERPLibre.
