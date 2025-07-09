"""
Copyright (c) Cutleast
"""

from pathlib import Path

from app import App
from core.database.database import Translation, TranslationDatabase
from core.database.importer import Importer
from core.database.string import String
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.translation_provider.source import Source

from ..core_test import CoreTest


class TestImporter(CoreTest):
    """
    Tests `core.database.importer.Importer`.
    """

    def test_import_mod_as_translation(self, app_context: App) -> None:
        """
        Tests `core.database.importer.Importer.import_mod_as_translation()`.
        """

        # given
        database: TranslationDatabase = app_context.database
        importer: Importer = database.importer
        original_mod: Mod = self.get_mod_by_name("Wet and Cold SE")
        original_plugin: ModFile = self.get_modfile_from_mod(
            original_mod, "WetandCold.esp"
        )
        translation_mod: Mod = self.get_mod_by_name("Wet and Cold SE - German")
        translated_plugin: ModFile = self.get_modfile_from_mod(
            translation_mod, "WetandCold.esp"
        )

        # when
        assert database.user_translations == []
        original_plugin.status = TranslationStatus.RequiresTranslation
        translated_plugin.status = TranslationStatus.IsTranslated
        importer.import_mod_as_translation(translation_mod, original_mod)

        # then
        assert len(database.user_translations) == 1
        translation: Translation = database.user_translations[0]
        assert translation.mod_id == translation_mod.mod_id
        assert translation.original_mod_id == original_mod.mod_id
        assert translation.source == Source.NexusMods
        assert translation.name == "Wet and Cold SE - German"
        assert translation.strings
        assert "wetandcold.esp" in translation.strings
        assert original_plugin.status == TranslationStatus.TranslationInstalled
        assert translated_plugin.status == TranslationStatus.IsTranslated

        # clean
        self.reset_app_components(app_context)

    def test_extract_strings_from_archive(self, app_context: App) -> None:
        """
        Tests `core.database.importer.Importer.extract_strings_from_archive()`.
        """

        # given
        database: TranslationDatabase = app_context.database
        importer: Importer = database.importer
        test_file_path: Path = self.data_path() / "Wet and Cold SE - German.7z"

        # when
        app_context.mod_instance.mods.remove(  # Remove mod so that it doesn't conflict with the imported mod
            self.get_mod_by_name("Wet and Cold SE - German")
        )
        assert database.user_translations == []
        imported_strings: dict[str, list[String]] = (
            importer.extract_strings_from_archive(test_file_path)
        )

        # then
        assert "wetandcold.esp" in imported_strings
        assert imported_strings["wetandcold.esp"]

        # clean
        self.reset_app_components(app_context)
