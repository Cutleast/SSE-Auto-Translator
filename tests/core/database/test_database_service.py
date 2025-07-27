"""
Copyright (c) Cutleast
"""

from pathlib import Path

from app import App
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.importer import Importer
from core.database.string import String
from core.database.translation import Translation
from core.mod_instance.mod import Mod
from core.utilities.game_language import GameLanguage

from ..core_test import CoreTest


class TestDatabaseService(CoreTest):
    """
    Tests `core.database.database_service.DatabaseService`.
    """

    def test_load_database(self) -> None:
        """
        Tests `DatabaseService.load_database()`.
        """

        # given
        appdb_path: Path = self.res_path() / "app" / "database"
        userdb_path: Path = self.data_path() / "data" / "user" / "database"
        language: GameLanguage = self.user_config().language

        # when
        database: TranslationDatabase = DatabaseService.load_database(
            appdb_path, userdb_path, language
        )

        # then
        assert len(database.user_translations) == 2
        assert sorted(map(lambda t: t.name, database.user_translations)) == [
            "Obsidian Weathers and Seasons - German",
            "Wet and Cold SE - German",
        ]

    def test_create_translation_for_mod(self, app_context: App) -> None:
        """
        Tests `DatabaseService.create_translation_for_mod()`.
        """

        # given
        mod: Mod = self.get_mod_by_name("RS Children Overhaul")
        database: TranslationDatabase = self.database()

        # when
        created_translation: Translation = DatabaseService.create_translation_for_mod(
            mod, database, add_and_save=False
        )

        # then
        assert len(created_translation.strings) == 3
        assert sorted(created_translation.strings.keys()) == [
            Path("RSChildren Patch - BS Bruma.esp"),
            Path("RSChildren.esp"),
            Path("RSkyrimChildren.esm"),
        ]

    def test_create_translation_from_mod(self, app_context: App) -> None:
        """
        Tests `DatabaseService.create_translation_from_mod()`.
        """

        # given
        original_mod: Mod = self.get_mod_by_name("Wet and Cold SE")
        translated_mod: Mod = self.get_mod_by_name("Wet and Cold SE - German")
        database: TranslationDatabase = self.database()

        # when
        translation_strings: dict[Path, list[String]] = (
            Importer.import_mod_as_translation(translated_mod, original_mod)
        )
        created_translation: Translation = DatabaseService.create_translation_from_mod(
            translated_mod,
            original_mod,
            translation_strings,
            database,
            add_and_save=False,
        )

        # then
        assert len(created_translation.strings) == 1
        assert sorted(created_translation.strings.keys()) == [Path("WetandCold.esp")]

        strings: list[String] = created_translation.strings[Path("WetandCold.esp")]
        string_hashes: list[int] = list(map(CoreTest.calc_unique_string_hash, strings))

        expected_strings: list[String] = [
            String(
                form_id="05062F4E|WetandCold.esp",
                type="ENCH FULL",
                original="Fortify Carry Weight",
                string="Tragfähigkeit verstärken",
                editor_id="_WetEnchArmorFortifyCarry03",
                status=String.Status.TranslationComplete,
            )
        ]

        assert len(strings) == 204
        for string in expected_strings:
            assert CoreTest.calc_unique_string_hash(string) in string_hashes, (
                f"<{string}> not in actual strings!"
            )
