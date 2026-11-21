# Changelog

All notable changes to the ERPLibre Stream Deck deck program. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The
version that matters to ERPLibre and the GNOME extension is the one of
`CONTRACT.md`, carried by `erplibre_streamdeck.CONTRACT_VERSION`.

## [Unreleased]

### Added
- `deck_lock.py` runs as a command, `python3 -I deck_lock.py <program>
  <command> [arguments…]`: it holds the deck lock while the command and
  every process that inherits the lock run, passes SIGTERM and SIGINT to
  them and exits with the command's code. A deck program started inside
  such a game runs under its lock, and a second one exits with code 2
  (`deck.inner`); contract 1.1. ERPLibre's hand-over from the deck
  service to a game runs it as `game`.
- The deck program, its controller, its lock and its translator as a
  repository of their own, with contract 1.0 (`CONTRACT.md`). ERPLibre
  clones it at `script/stream_deck/deck/`; until then they lived in
  ERPLibre's `script/stream_deck/`, with their tests in its `test/`.
- `ERPLIBRE_ROOT` names the ERPLibre checkout; without it, a clone at
  `script/stream_deck/deck/` finds the checkout three levels up, and any
  other location runs on its own, with the default settings.
- One test runner, `python -m unittest discover -s tests`, for the deck,
  the lock, the entry points, the translator and the contract.
  `tests/fixtures/erplibre_home_settings.sh` stands for ERPLibre's
  settings library outside a checkout; `STREAMDECK_PYTHON` names the
  interpreter of the tests that run the real Stream Deck library.

### Changed
- `paths.STREAM_DECK_DIR` is now `paths.DECK_DIR`, the repository root;
  `paths.REPO_ROOT` and `paths.SETTINGS_LIB` are `None` without an
  ERPLibre checkout.
- The usage names the programs from the repository root
  (`python erplibre_streamdeck`, `python erplibre_controller.py`).
- Key 3 of the controller runs `keyboard_talk.py` of this repository
  under the controller's interpreter; key 0 runs ERPLibre's
  `script/todo/source_todo.sh` from the checkout, whatever the current
  directory.
- The speech-to-text guide is `TRANSLATOR.md` (formerly `gpt.md`).

### Fixed
- On their own, `translator_doctor.py`, `translator_test.py` and
  `translator_stream.py` name the manual steps of `TRANSLATOR.md`, or
  the whisper.cpp model download, instead of ERPLibre's make targets;
  inside a checkout they name the target and the checkout to run it
  from (`translator.install_hint()`).
