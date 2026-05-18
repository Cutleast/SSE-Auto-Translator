"""
Copyright (c) Cutleast
"""

import importlib
import sys
from types import ModuleType, SimpleNamespace

from pytest import MonkeyPatch


def load_search_filter(monkeypatch: MonkeyPatch):
    fake_types = ModuleType("core.string.types")
    fake_types.String = object
    monkeypatch.setitem(sys.modules, "core.string.types", fake_types)
    sys.modules.pop("core.string.search_filter", None)

    import core.string.search_filter as search_filter

    return importlib.reload(search_filter)


def test_matches_filter_id_is_case_insensitive(monkeypatch: MonkeyPatch) -> None:
    search_filter = load_search_filter(monkeypatch)
    string = SimpleNamespace(
        display_id="04000D65|Obsidian Weathers.esp - ObsidianSpell - SPEL FULL",
        original="Hello",
        string="Hallo",
    )

    assert search_filter.matches_filter({"id": "obsidianspell"}, string)
