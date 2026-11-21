# © 2026 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""Every path of the deck program, anchored on this file.

DECK_DIR is the root of this repository, where the package, deck_lock,
the controller and the translator live. REPO_ROOT is the ERPLibre
checkout the deck runs in, or None when it runs on its own (see
erplibre_root()). The ERPLibre files the deck uses, the settings
library, todo.py and the .venv.erplibre venv, are resolved under it.

settings.json, layouts.json (window layouts) and keymap.json (home key
layouts) live under the literal ~/.config/erplibre-home, the location
the deck has always written; the user plugin directory follows
$XDG_CONFIG_HOME, like streamdeck.conf.
The state directory is read at call time from $XDG_STATE_HOME."""

import os
from pathlib import Path

DECK_DIR = Path(__file__).resolve().parent.parent

# An absolute or relative directory: the ERPLibre checkout, whatever the
# location of the deck clone. Empty or unset, the clone's own location
# decides.
ERPLIBRE_ROOT_ENV = "ERPLIBRE_ROOT"
# Where ERPLibre clones this repository, relative to its root.
CLONE_REL = ("script", "stream_deck", "deck")


def erplibre_root(environ=None, deck_dir=DECK_DIR):
    """The ERPLibre checkout as an absolute Path, or None.

    $ERPLIBRE_ROOT wins when set and non-empty, made absolute against the
    current directory, without checking what it holds. Otherwise a clone
    whose last three directories are script/stream_deck/deck has its
    checkout three levels up. Any other location runs on its own: None.
    The directory is not required to exist; each caller checks the file
    it needs and fails as it does for a missing file."""
    environ = os.environ if environ is None else environ
    explicit = environ.get(ERPLIBRE_ROOT_ENV, "")
    if explicit:
        return Path(os.path.abspath(explicit))
    deck_dir = Path(deck_dir)
    if deck_dir.parts[-len(CLONE_REL):] == CLONE_REL:
        return deck_dir.parents[len(CLONE_REL) - 1]
    return None


REPO_ROOT = erplibre_root()
CONFIG_DIR = Path(os.path.expanduser("~/.config/erplibre-home"))
SETTINGS_FILE = CONFIG_DIR / "settings.json"
LAYOUTS_FILE = CONFIG_DIR / "layouts.json"
KEYMAP_FILE = CONFIG_DIR / "keymap.json"
# ERPLibre's settings library, which reads streamdeck.conf; None
# without an ERPLibre checkout.
SETTINGS_LIB = (
    None
    if REPO_ROOT is None
    else REPO_ROOT / "script/install/erplibre_home_settings.sh"
)


def state_dir():
    """$XDG_STATE_HOME/erplibre-home, ~/.local/state when unset."""
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return Path(base) / "erplibre-home"


def user_plugin_dir():
    """$XDG_CONFIG_HOME/erplibre-home/deck-plugins, ~/.config when
    unset or empty."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser(
        "~/.config"
    )
    return Path(base) / "erplibre-home" / "deck-plugins"
