"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.database_updater import DatabaseUpdater
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.string.string_loader import StringLoader
from core.string.string_status import StringStatus
from core.string.types import StringList
from tests.setup.data_factory import DataFactory
from tests.setup.sync_executor import ExecutorPatcher

from ..core_test import CoreTest


class TestDatabaseUpdater(CoreTest):
    """
    Tests `core.database.database_updater.DatabaseUpdater`.
    """

    def test_update_translation_resets_changed_strings_and_saves(
        self, tmp_path: Path
    ) -> None:
        """
        Tests `DatabaseUpdater.update_translation()`.
        """

        # given
        mod: Mod = DataFactory.instance_mod("RS Children Overhaul")
        mod_instance: ModInstance = DataFactory.mod_instance([mod])
        database: TranslationDatabase = DataFactory.database(tmp_path)
        modfile: ModFile = self.get_modfile_from_mod(mod, "RSChildren.esp")
        original_strings: StringList = modfile.get_strings()
        translation_strings: StringList = [
            string.model_copy(deep=True) for string in original_strings
        ]
        translation_strings[0].original = "Outdated original"
        translation_strings[0].string = "Translated text"
        translation_strings[0].status = StringStatus.TranslationComplete

        translation: Translation = DatabaseService.create_blank_translation(
            name="Smoke Update Translation",
            strings={modfile.path: translation_strings},
            database=database,
        )
        updater = DatabaseUpdater(database, mod_instance)

        # when
        updated_modfile_states: dict[ModFile, TranslationStatus] = (
            updater.update_translation(translation)
        )

        # then
        assert updated_modfile_states == {
            modfile: TranslationStatus.TranslationIncomplete
        }

        updated_strings: StringList = translation.strings[modfile.path]
        assert updated_strings[0].original == original_strings[0].original
        assert updated_strings[0].string == original_strings[0].original
        assert updated_strings[0].status == StringStatus.TranslationRequired

        json_file_path: Path = translation.path / "RSChildren.esp.json"
        assert json_file_path.is_file()
        assert (
            StringLoader.load_strings_from_json_file(json_file_path) == updated_strings
        )

    def test_update_database_translations_adds_missing_modfiles(
        self, tmp_path: Path, sync_executor: ExecutorPatcher
    ) -> None:
        """
        Tests `DatabaseUpdater.update_database_translations()`.
        """

        # given
        mod: Mod = DataFactory.instance_mod("RS Children Overhaul")
        # a mod without translation must be skipped
        mod_instance: ModInstance = DataFactory.mod_instance(
            [mod, DataFactory.mod("Unrelated Mod")]
        )
        modfile: ModFile = self.get_modfile_from_mod(mod, "RSChildren.esp")
        database: TranslationDatabase = DataFactory.database(tmp_path)
        for current_modfile in mod.modfiles:
            if current_modfile.path != modfile.path:
                current_modfile.status = TranslationStatus.RequiresTranslation

        translation: Translation = DatabaseService.create_blank_translation(
            name="RS Children Overhaul - Smoke",
            strings={
                modfile.path: [
                    string.model_copy(deep=True) for string in modfile.get_strings()
                ]
            },
            database=database,
        )
        database.user_translations.append(translation)

        updater = DatabaseUpdater(database, mod_instance)
        sync_executor(updater)

        # when
        updated_modfile_states: dict[ModFile, TranslationStatus] = (
            updater.update_database_translations(thread_num=1)
        )

        # then
        assert sorted(translation.strings.keys()) == [
            Path("RSChildren Patch - BS Bruma.esp"),
            Path("RSChildren.esp"),
            Path("RSkyrimChildren.esm"),
        ]

        assert (translation.path / "RSChildren Patch - BS Bruma.esp.json").is_file()
        assert (translation.path / "RSChildren.esp.json").is_file()
        assert (translation.path / "RSkyrimChildren.esm.json").is_file()

        assert {mf.path: st for mf, st in updated_modfile_states.items()} == {
            Path(
                "RSChildren Patch - BS Bruma.esp"
            ): TranslationStatus.TranslationIncomplete,
            Path("RSkyrimChildren.esm"): TranslationStatus.TranslationIncomplete,
        }
