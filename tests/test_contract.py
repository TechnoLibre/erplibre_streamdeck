#!/usr/bin/env python3
# © 2026 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""CONTRACT.md against the code: its version, the entry points and exit
codes it states, and the rules that locate the ERPLibre checkout.

The rules are checked twice: on erplibre_root() with an explicit
environment and directory, and in a subprocess on a copy of the package
placed at <checkout>/script/stream_deck/deck/, where the module computes
REPO_ROOT and SETTINGS_LIB at import as it does in ERPLibre."""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamdeck_stubs as S  # noqa: E402

DECK_DIR = Path(__file__).resolve().parents[1]
CONTRACT = DECK_DIR / "CONTRACT.md"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract_text():
    return CONTRACT.read_text(encoding="utf-8")


paths = load(
    "deck_paths_under_test", DECK_DIR / "erplibre_streamdeck/paths.py"
)


class VersionTest(unittest.TestCase):
    def test_the_package_and_the_contract_state_one_version(self):
        package = load(
            "deck_package_under_test",
            DECK_DIR / "erplibre_streamdeck/__init__.py",
        )
        self.assertRegex(package.CONTRACT_VERSION, r"^\d+\.\d+$")
        found = re.findall(
            r"^\*\*Contract version: (\d+\.\d+)\*\*$",
            contract_text(),
            re.MULTILINE,
        )
        self.assertEqual([package.CONTRACT_VERSION], found)

    def test_the_changelog_names_the_version(self):
        package = load(
            "deck_package_under_test",
            DECK_DIR / "erplibre_streamdeck/__init__.py",
        )
        changelog = (DECK_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"contract {package.CONTRACT_VERSION}", changelog)


class EntryPointsTest(unittest.TestCase):
    """Every file the Layout item names exists where it says."""

    FILES = (
        "erplibre_streamdeck/__main__.py",
        "erplibre_streamdeck/plugins/__init__.py",
        "erplibre_controller.py",
        "deck_lock.py",
        "requirements.txt",
        "translator.py",
        "translator_doctor.py",
        "translator_test.py",
        "translator_stream.py",
        "keyboard_talk.py",
        "draw_assets.py",
        "Assets/ATTRIBUTION.txt",
        "tests/fixtures/erplibre_home_settings.sh",
    )

    def test_the_files_exist_and_the_contract_names_them(self):
        text = contract_text()
        for name in self.FILES:
            with self.subTest(name=name):
                self.assertTrue((DECK_DIR / name).exists())
                base = name.split("/")[0] if "/" in name else name
                self.assertIn(f"`{base}", text)

    def test_the_exit_codes_are_the_ones_stated(self):
        lock = load("deck_lock_under_test", DECK_DIR / "deck_lock.py")
        self.assertEqual(2, lock.BUSY_EXIT)
        self.assertEqual(3, lock.NO_DECK_EXIT)
        text = contract_text()
        for code, name in ((2, "BUSY_EXIT"), (3, "NO_DECK_EXIT")):
            self.assertRegex(text, rf"\| {code} \|[^\n]*deck_lock\.{name}")

    def test_the_paths_module_imports_only_the_standard_library(self):
        """ERPLibre's tests load it outside the Stream Deck venv."""
        done = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, sys.argv[1]);"
                " import erplibre_streamdeck.paths, erplibre_streamdeck;"
                " print(sorted(m for m in sys.modules"
                " if m.split('.')[0] in ('PIL', 'StreamDeck', 'cv2')))",
                str(DECK_DIR),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual("[]", done.stdout.strip())


class ErplibreRootTest(unittest.TestCase):
    """Locating ERPLibre, items 1 to 3, on erplibre_root()."""

    CLONE = Path("/x/erp/script/stream_deck/deck")

    def test_the_variable_wins_over_the_clone_location(self):
        self.assertEqual(
            Path("/y/other"),
            paths.erplibre_root({"ERPLIBRE_ROOT": "/y/other"}, self.CLONE),
        )

    def test_a_relative_variable_is_made_absolute(self):
        self.assertEqual(
            Path(os.path.abspath("rel/erp")),
            paths.erplibre_root({"ERPLIBRE_ROOT": "rel/erp"}, Path("/z")),
        )

    def test_an_empty_variable_leaves_the_clone_location_decide(self):
        self.assertEqual(
            Path("/x/erp"),
            paths.erplibre_root({"ERPLIBRE_ROOT": ""}, self.CLONE),
        )

    def test_a_clone_at_script_stream_deck_deck_is_three_levels_down(self):
        self.assertEqual(Path("/x/erp"), paths.erplibre_root({}, self.CLONE))

    def test_any_other_location_runs_on_its_own(self):
        for deck in (
            Path("/x/erplibre-streamdeck"),
            Path("/x/script/stream_deck"),
            Path("/x/stream_deck/deck"),
            Path("/x/script/streamdeck/deck"),
            Path("/x/script/stream_deck/deck/sub"),
        ):
            with self.subTest(deck=str(deck)):
                self.assertIsNone(paths.erplibre_root({}, deck))


class ClonedInErplibreTest(unittest.TestCase):
    """The module, imported from a copy at <checkout>/script/stream_deck/
    deck/, finds the checkout and its settings library; $ERPLIBRE_ROOT
    moves both."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.checkout = Path(tmp.name, "checkout").resolve()
        self.deck = self.checkout / "script/stream_deck/deck"
        shutil.copytree(
            DECK_DIR / "erplibre_streamdeck",
            self.deck / "erplibre_streamdeck",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        self.env = {
            k: v for k, v in os.environ.items() if k != "ERPLIBRE_ROOT"
        }

    def located(self, env, cwd):
        done = subprocess.run(
            [
                sys.executable,
                "-c",
                "import json, sys; sys.path.insert(0, sys.argv[1]);"
                " from erplibre_streamdeck import paths;"
                " print(json.dumps([str(paths.DECK_DIR), str(paths.REPO_ROOT),"
                " str(paths.SETTINGS_LIB)]))",
                str(self.deck),
            ],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, done.returncode, done.stderr)
        return json.loads(done.stdout)

    def test_the_checkout_three_levels_up(self):
        self.assertEqual(
            [
                str(self.deck),
                str(self.checkout),
                str(
                    self.checkout / "script/install/erplibre_home_settings.sh"
                ),
            ],
            self.located(self.env, cwd=tempfile.gettempdir()),
        )

    def test_the_variable_moves_it(self):
        env = dict(self.env, ERPLIBRE_ROOT="elsewhere")
        cwd = self.checkout.parent
        self.assertEqual(
            [
                str(self.deck),
                str(cwd / "elsewhere"),
                str(
                    cwd / "elsewhere/script/install/erplibre_home_settings.sh"
                ),
            ],
            self.located(env, cwd=cwd),
        )


class SettingsThroughTheCheckoutTest(unittest.TestCase):
    """--list-plugins reads DECK_PLUGINS_OFF through the settings library
    of the checkout $ERPLIBRE_ROOT names. Runs the real program: skipped
    without an interpreter holding the Stream Deck library."""

    def test_deck_plugins_off_reaches_the_loader(self):
        python = S.real_python()
        if python is None:
            self.skipTest(f"no Stream Deck library: set {S.PYTHON_ENV}")
        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp, "checkout")
            lib = checkout / "script/install/erplibre_home_settings.sh"
            lib.parent.mkdir(parents=True)
            shutil.copy(S.FAKE_SETTINGS_LIB, lib)
            conf = Path(tmp, "config/erplibre-home/streamdeck.conf")
            conf.parent.mkdir(parents=True)
            conf.write_text("DECK_PLUGINS_OFF=tiling\n", encoding="utf-8")
            env = dict(
                os.environ,
                HOME=tmp,
                XDG_CONFIG_HOME=str(Path(tmp, "config")),
                XDG_STATE_HOME=str(Path(tmp, "state")),
                XDG_RUNTIME_DIR=tmp,
                ERPLIBRE_ROOT=str(checkout),
            )
            done = subprocess.run(
                [python, str(S.PACKAGE), "--list-plugins"],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("tiling: off", done.stdout.splitlines())
        self.assertIn("timers: active: repo", done.stdout.splitlines())

    def test_without_a_checkout_the_defaults_and_one_line(self):
        python = S.real_python()
        if python is None:
            self.skipTest(f"no Stream Deck library: set {S.PYTHON_ENV}")
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if k != "ERPLIBRE_ROOT"}
            env.update(HOME=tmp, XDG_CONFIG_HOME=tmp, XDG_RUNTIME_DIR=tmp)
            done = subprocess.run(
                [python, str(S.PACKAGE), "--list-plugins"],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("tiling: active: repo", done.stdout.splitlines())
        if paths.erplibre_root({}, DECK_DIR) is None:
            self.assertIn("no ERPLibre checkout", done.stderr)


if __name__ == "__main__":
    unittest.main()
