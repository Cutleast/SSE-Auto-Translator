"""
Copyright (c) Cutleast
"""

from core.config.app_config import AppConfig
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.scanner.scanner import Scanner
from core.translation_provider.provider import Provider
from core.user_data.user_data import UserData

from ..core_test import CoreTest


class TestScanner(CoreTest):
    """
    Tests `core.scanner.scanner.Scanner`.
    """

    def test_basic_scan(self, app_config: AppConfig, user_data: UserData) -> None:
        """
        Tests `core.scanner.scanner.Scanner.run_basic_scan()` on the test mod instance.
        """

        # given
        modinstance: ModInstance = user_data.modinstance
        scanner = Scanner(
            modinstance,
            user_data.database,
            app_config,
            user_data.user_config,
            Provider(user_data.user_config),
            user_data.masterlist,
        )
        items: dict[Mod, list[ModFile]] = {
            mod: mod.modfiles for mod in modinstance.mods
        }
        expected_results: dict[Mod, dict[ModFile, TranslationStatus]] = {
            self.get_mod_by_name("Wet and Cold SE", modinstance): {
                self.get_modfile_from_mod_name(
                    "Wet and Cold SE", "WetandCold.esp", modinstance
                ): TranslationStatus.TranslationInstalled
            },
            self.get_mod_by_name("Wet and Cold SE - German", modinstance): {
                self.get_modfile_from_mod_name(
                    "Wet and Cold SE - German", "WetandCold.esp", modinstance
                ): TranslationStatus.IsTranslated
            },
            self.get_mod_by_name("RS Children Overhaul", modinstance): {
                self.get_modfile_from_mod_name(
                    "RS Children Overhaul", "RSChildren.esp", modinstance
                ): TranslationStatus.RequiresTranslation
            },
        }

        # when
        scan_result: dict[Mod, dict[ModFile, TranslationStatus]] = (
            scanner.run_basic_scan(items)
        )

        # then
        assert len(scan_result) == len(items)

        for mod, modfiles in scan_result.items():
            assert len(modfiles) == len(items[mod])

            for modfile, status in modfiles.items():
                if mod in expected_results and modfile in expected_results[mod]:
                    assert status == expected_results[mod][modfile]
