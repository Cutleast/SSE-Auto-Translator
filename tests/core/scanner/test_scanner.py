"""
Copyright (c) Cutleast
"""

import os
import sys

from ..core_test import CoreTest

sys.path.append(os.path.join(os.getcwd(), "src"))

from src.app import App
from src.core.mod_instance.mod import Mod
from src.core.mod_instance.mod_instance import ModInstance
from src.core.mod_instance.plugin import Plugin
from src.core.scanner.scanner import Scanner


class TestScanner(CoreTest):
    """
    Tests `core.scanner.scanner.Scanner`.
    """

    def test_basic_scan(self, app_context: App) -> None:
        """
        Tests `core.scanner.scanner.Scanner.run_basic_scan()` on the test mod instance.
        """

        # given
        scanner: Scanner = self.scanner()
        modinstance: ModInstance = self.modinstance()
        items: dict[Mod, list[Plugin]] = {mod: mod.plugins for mod in modinstance.mods}
        expected_results: dict[Mod, dict[Plugin, Plugin.Status]] = {
            self.get_mod_by_name("Wet and Cold SE"): {
                self.get_plugin_from_mod_name(
                    "Wet and Cold SE", "WetandCold.esp"
                ): Plugin.Status.RequiresTranslation
            },
            self.get_mod_by_name("Wet and Cold SE - German"): {
                self.get_plugin_from_mod_name(
                    "Wet and Cold SE - German", "WetandCold.esp"
                ): Plugin.Status.IsTranslated
            },
            self.get_mod_by_name("Obsidian Weathers and Seasons"): {
                self.get_plugin_from_mod_name(
                    "Obsidian Weathers and Seasons", "Obsidian Weathers.esp"
                ): Plugin.Status.RequiresTranslation
            },
        }

        # when
        scan_result: dict[Mod, dict[Plugin, Plugin.Status]] = scanner.run_basic_scan(
            items
        )

        # then
        assert len(scan_result) == len(items)

        for mod, plugins in scan_result.items():
            assert len(plugins) == len(items[mod])

            for plugin, status in plugins.items():
                if mod in expected_results and plugin in expected_results[mod]:
                    assert status == expected_results[mod][plugin]
