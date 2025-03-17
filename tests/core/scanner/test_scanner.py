"""
Copyright (c) Cutleast
"""

from app import App
from core.mod_instance.mod import Mod
from core.mod_instance.mod_file import ModFile
from core.mod_instance.mod_instance import ModInstance
from core.scanner.scanner import Scanner

from ..core_test import CoreTest


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
        items: dict[Mod, list[ModFile]] = {
            mod: mod.modfiles for mod in modinstance.mods
        }
        expected_results: dict[Mod, dict[ModFile, ModFile.Status]] = {
            self.get_mod_by_name("Wet and Cold SE"): {
                self.get_modfile_from_mod_name(
                    "Wet and Cold SE", "WetandCold.esp"
                ): ModFile.Status.RequiresTranslation
            },
            self.get_mod_by_name("Wet and Cold SE - German"): {
                self.get_modfile_from_mod_name(
                    "Wet and Cold SE - German", "WetandCold.esp"
                ): ModFile.Status.IsTranslated
            },
            self.get_mod_by_name("Obsidian Weathers and Seasons"): {
                self.get_modfile_from_mod_name(
                    "Obsidian Weathers and Seasons", "Obsidian Weathers.esp"
                ): ModFile.Status.RequiresTranslation
            },
        }

        # when
        scan_result: dict[Mod, dict[ModFile, ModFile.Status]] = scanner.run_basic_scan(
            items
        )

        # then
        assert len(scan_result) == len(items)

        for mod, modfiles in scan_result.items():
            assert len(modfiles) == len(items[mod])

            for modfile, status in modfiles.items():
                if mod in expected_results and modfile in expected_results[mod]:
                    assert status == expected_results[mod][modfile]
