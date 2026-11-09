"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

from core.config.app_config import AppConfig
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.scanner.scanner import Scanner
from core.string.types import StringList
from core.translation_provider.nm_api.nxm_id import NxmModId
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.source import Source
from core.user_data.user_data import UserData
from tests.base_test import BaseTest
from tests.integration_test import IntegrationTest
from tests.setup.data_factory import DataFactory


class TestScanner(BaseTest):
    """
    Tests `core.scanner.scanner.Scanner` with small in-memory mod instances.
    """

    @staticmethod
    def create_scanner(
        app_config: AppConfig,
        mod_instance: ModInstance,
        tmp_path: Path,
        provider: Optional[TranslationProvider] = None,
    ) -> Scanner:
        """
        Creates a scanner for the specified mod instance and an empty database.

        Args:
            app_config (AppConfig): The test app configuration.
            mod_instance (ModInstance): The mod instance to scan.
            tmp_path (Path): The temporary folder of the test.
            provider (Optional[TranslationProvider], optional):
                The translation provider to use. Defaults to a mocked provider.

        Returns:
            Scanner: The scanner.
        """

        return Scanner(
            mod_instance,
            DataFactory.database(tmp_path),
            app_config,
            DataFactory.user_config(),
            provider or MagicMock(spec=TranslationProvider),
            DataFactory.masterlist(),
        )

    def test_online_scan(self, app_config: AppConfig, tmp_path: Path) -> None:
        """
        Tests `core.scanner.scanner.Scanner.run_online_scan()` with a mocked provider
        that has a translation for exactly one mod file.
        """

        # given
        children_mod: Mod = DataFactory.mod(
            "RS Children Overhaul",
            [
                DataFactory.plugin_file(
                    Path(name), TranslationStatus.RequiresTranslation
                )
                for name in [
                    "RSChildren.esp",
                    "RSChildren Patch - BS Bruma.esp",
                    "RSkyrimChildren.esm",
                ]
            ],
            mod_id=2650,
        )
        unknown_mod: Mod = DataFactory.mod(
            "Unknown Mod",
            [
                DataFactory.plugin_file(
                    Path("Unknown.esp"), TranslationStatus.RequiresTranslation
                )
            ],
        )
        provider = MagicMock(spec=TranslationProvider)
        provider.is_available = True
        provider.is_mod_id_valid.return_value = True
        provider.get_translations.side_effect = lambda **kwargs: (
            {Source.NexusMods: [NxmModId(mod_id=42)]}
            if kwargs["file_name"] == "RSChildren.esp"
            else {}
        )
        scanner: Scanner = TestScanner.create_scanner(
            app_config,
            DataFactory.mod_instance([children_mod, unknown_mod]),
            tmp_path,
            provider,
        )

        # when
        scan_result: dict[Mod, dict[ModFile, TranslationStatus]] = (
            scanner.run_online_scan(
                {children_mod: children_mod.modfiles, unknown_mod: unknown_mod.modfiles}
            )
        )

        # then
        assert {
            modfile.name: status for modfile, status in scan_result[children_mod].items()
        } == {
            "RSChildren.esp": TranslationStatus.TranslationAvailableOnline,
            "RSChildren Patch - BS Bruma.esp": TranslationStatus.NoTranslationAvailable,
            "RSkyrimChildren.esm": TranslationStatus.NoTranslationAvailable,
        }
        # a mod without a mod id cannot have translations online
        assert list(scan_result[unknown_mod].values()) == [
            TranslationStatus.NoTranslationAvailable
        ]
        assert provider.get_translations.call_count == 3

    def test_online_scan_without_provider(
        self, app_config: AppConfig, tmp_path: Path
    ) -> None:
        """
        Tests that the online scan is skipped if no provider is available.
        """

        # given
        mod: Mod = DataFactory.mod(
            "Some Mod",
            [
                DataFactory.plugin_file(
                    Path("Some.esp"), TranslationStatus.RequiresTranslation
                )
            ],
            mod_id=1,
        )
        provider = MagicMock(spec=TranslationProvider)
        provider.is_available = False
        scanner: Scanner = TestScanner.create_scanner(
            app_config, DataFactory.mod_instance([mod]), tmp_path, provider
        )

        # when
        scan_result: dict[Mod, dict[ModFile, TranslationStatus]] = (
            scanner.run_online_scan({mod: mod.modfiles})
        )

        # then
        assert scan_result == {}
        provider.get_translations.assert_not_called()

    def test_string_search(self, app_config: AppConfig, tmp_path: Path) -> None:
        """
        Tests `core.scanner.scanner.Scanner.run_string_search()` on the plugin of a
        test mod.
        """

        # given
        mod: Mod = DataFactory.instance_mod("Wet and Cold SE")
        scanner: Scanner = TestScanner.create_scanner(
            app_config, DataFactory.mod_instance([mod]), tmp_path
        )

        # when
        results: dict[Path, StringList] = scanner.run_string_search(
            {mod: mod.modfiles}, {"original": "Fortify Carry Weight"}
        )

        # then
        assert list(results) == [Path("Wet and Cold SE > WetandCold.esp")]
        assert results[Path("Wet and Cold SE > WetandCold.esp")]
        assert all(
            "fortify carry weight" in string.original.lower()
            for strings in results.values()
            for string in strings
        )


class TestScannerIntegration(IntegrationTest):
    """
    Integration tests for `core.scanner.scanner.Scanner` on the complete test mod
    instance and database.
    """

    @staticmethod
    def create_scanner(app_config: AppConfig, user_data: UserData) -> Scanner:
        """
        Creates a scanner for the test user data.

        Args:
            app_config (AppConfig): The test app configuration.
            user_data (UserData): The test user data.

        Returns:
            Scanner: The scanner.
        """

        return Scanner(
            user_data.mod_instance,
            user_data.database,
            app_config,
            user_data.user_config,
            TranslationProvider(user_data.user_config),
            user_data.masterlist,
        )

    def test_basic_scan(self, app_config: AppConfig, user_data: UserData) -> None:
        """
        Tests `core.scanner.scanner.Scanner.run_basic_scan()` on the test mod instance.
        """

        # given
        mod_instance: ModInstance = user_data.mod_instance
        scanner: Scanner = TestScannerIntegration.create_scanner(app_config, user_data)
        items: dict[Mod, list[ModFile]] = {
            mod: mod.modfiles for mod in mod_instance.mods
        }
        expected_results: dict[Mod, dict[ModFile, TranslationStatus]] = {
            self.get_mod_by_name("Wet and Cold SE", mod_instance): {
                self.get_modfile_from_mod_name(
                    "Wet and Cold SE", "WetandCold.esp", mod_instance
                ): TranslationStatus.TranslationInstalled
            },
            self.get_mod_by_name("Wet and Cold SE - German", mod_instance): {
                self.get_modfile_from_mod_name(
                    "Wet and Cold SE - German", "WetandCold.esp", mod_instance
                ): TranslationStatus.IsTranslated
            },
            self.get_mod_by_name("RS Children Overhaul", mod_instance): {
                self.get_modfile_from_mod_name(
                    "RS Children Overhaul", "RSChildren.esp", mod_instance
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

    def test_translation_scan(self, app_config: AppConfig, user_data: UserData) -> None:
        """
        Tests that `core.scanner.scanner.Scanner.run_translation_scan()` finds the
        original mod of an installed translation that is not yet in the database.
        """

        # given
        scanner: Scanner = TestScannerIntegration.create_scanner(app_config, user_data)
        items: dict[Mod, list[ModFile]] = {
            mod: mod.modfiles for mod in user_data.mod_instance.mods
        }
        scan_result: dict[Mod, dict[ModFile, TranslationStatus]] = (
            scanner.run_basic_scan(items)
        )
        # the scanner only reports the states, they are applied by the state service
        for modfile_states in scan_result.values():
            for modfile, status in modfile_states.items():
                modfile.status = status

        translation_mod: Mod = self.get_mod_by_name(
            "The Dragonborn's Bestiary - German", user_data.mod_instance
        )
        original_mod: Mod = self.get_mod_by_name(
            "The Dragonborn's Bestiary", user_data.mod_instance
        )

        # when
        result: dict[Mod, Mod] = scanner.run_translation_scan(
            list(user_data.mod_instance.mods)
        )

        # then
        assert result.get(translation_mod) is original_mod
