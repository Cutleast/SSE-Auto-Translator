"""
Copyright (c) Cutleast
"""

from pathlib import Path

from app import App
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService

from ..core_test import CoreTest


class TestStateService(CoreTest):
    """
    Tests `core.mod_instance.state_service.StateService`.
    """

    def test_database_change_updates_modfile_states(self, app_context: App) -> None:
        """
        Tests that adding or removing a translation from the database updates the
        affected mod file states.
        """

        # given
        database: TranslationDatabase = self.database()
        modinstance: ModInstance = self.modinstance()
        new_translation: Translation = DatabaseService.create_blank_translation(
            "A new translation",
            strings={Path("Ordinator - Perks of Skyrim.esp"): []},
            database=database,
        )
        modfile: ModFile = self.get_modfile_from_mod_name(
            "Ordinator - Perks of Skyrim", "Ordinator - Perks of Skyrim.esp"
        )
        StateService(modinstance, database)

        # then
        assert modfile.status != TranslationStatus.TranslationInstalled

        # when
        DatabaseService.add_translation(new_translation, database, save=False)

        # then
        assert modfile.status == TranslationStatus.TranslationInstalled

        # when
        DatabaseService.delete_translation(new_translation, database, save=False)

        # then
        assert modfile.status == TranslationStatus.RequiresTranslation
