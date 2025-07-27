"""
Copyright (c) Cutleast
"""

from pathlib import Path

from app import App
from core.database.database import TranslationDatabase
from core.database.importer import Importer
from core.database.string import String
from core.mod_instance.mod import Mod

from ..core_test import CoreTest


class TestImporter(CoreTest):
    """
    Tests `core.database.importer.Importer`.
    """

    def test_import_mod_as_translation(self) -> None:
        """
        Tests `core.database.importer.Importer.import_mod_as_translation()`.
        """

        # given
        importer = Importer()
        original_mod: Mod = self.get_mod_by_name("Wet and Cold SE")
        translation_mod: Mod = self.get_mod_by_name("Wet and Cold SE - German")

        # when
        translation_strings: dict[Path, list[String]] = (
            importer.import_mod_as_translation(translation_mod, original_mod)
        )

        # then
        assert translation_strings
        assert Path("WetandCold.esp") in translation_strings

    def test_extract_strings_from_archive(self, app_context: App) -> None:
        """
        Tests `core.database.importer.Importer.extract_strings_from_archive()`.
        """

        # given
        database: TranslationDatabase = app_context.database
        importer: Importer = Importer()
        test_file_path: Path = self.data_path() / "Wet and Cold SE - German.7z"

        # when
        app_context.mod_instance.mods.remove(  # Remove mod so that it doesn't conflict with the imported mod
            self.get_mod_by_name("Wet and Cold SE - German")
        )
        assert database.user_translations == []
        imported_strings: dict[Path, list[String]] = (
            importer.extract_strings_from_archive(
                test_file_path, self.modinstance(), self.tmp_folder(), database.language
            )
        )

        # then
        assert Path("wetandcold.esp") in imported_strings
        assert imported_strings[Path("wetandcold.esp")]

        # clean
        self.reset_app_components(app_context)
