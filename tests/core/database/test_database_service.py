"""
Copyright (c) Cutleast
"""

import json
import shutil
from pathlib import Path
from typing import Any

from cutleast_core_lib.core.alerts.alert import Alert
from cutleast_core_lib.core.alerts.manager import AlertManager

from core.database.database import TranslationDatabase
from core.database.database_reload_result import DatabaseReloadResult
from core.database.database_service import DatabaseService
from core.database.translation import Translation
from core.file_types.plugin.string import PluginString
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.string.string_extractor import StringExtractor
from core.string.string_status import StringStatus
from core.string.types import StringList
from core.utilities.game_language import GameLanguage
from tests.setup.data_factory import DataFactory
from tests.setup.paths import DATA_PATH, RES_PATH

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
        appdb_path: Path = RES_PATH / "app" / "database"
        userdb_path: Path = DATA_PATH / "data" / "user" / "database"
        language: GameLanguage = GameLanguage.German

        # when
        database: TranslationDatabase = DatabaseService.load_database(
            appdb_path, userdb_path, language
        )

        # then
        assert len(database.user_translations) == 2
        assert sorted(t.name for t in database.user_translations) == [
            "Obsidian Weathers and Seasons - German",
            "Wet and Cold SE - German",
        ]

    def test_create_translation_for_mod(self, tmp_path: Path) -> None:
        """
        Tests `DatabaseService.create_translation_for_mod()`.
        """

        # given
        mod: Mod = DataFactory.instance_mod("RS Children Overhaul")
        main_esp: ModFile = self.get_modfile_from_mod(mod, "RSChildren.esp")
        main_esp.status = TranslationStatus.TranslationAvailableInDatabase
        database: TranslationDatabase = DataFactory.database(tmp_path)

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

        # when
        created_translation = DatabaseService.create_translation_for_mod(
            mod, database, only_complete_coverage=True, add_and_save=False
        )

        # then
        assert len(created_translation.strings) == 1
        assert sorted(created_translation.strings.keys()) == [Path("RSChildren.esp")]

    def test_create_translation_for_mod_file(self, tmp_path: Path) -> None:
        """
        Tests `DatabaseService.create_translation_for_mod()`.
        """

        # given
        modfile: ModFile = self.get_modfile_from_mod(
            DataFactory.instance_mod("RS Children Overhaul"), "RSChildren.esp"
        )
        database: TranslationDatabase = DataFactory.database(tmp_path)

        # when
        created_translation: Translation = (
            DatabaseService.create_translation_for_modfile(
                modfile, database, add_and_save=False
            )
        )

        # then
        assert created_translation.name == "RSChildren.esp - German"
        assert list(created_translation.strings.keys()) == [Path("RSChildren.esp")]

    def test_create_translation_from_mod(self, tmp_path: Path) -> None:
        """
        Tests `DatabaseService.create_translation_from_mod()`.
        """

        # given
        original_mod: Mod = DataFactory.instance_mod("Wet and Cold SE")
        translated_mod: Mod = DataFactory.instance_mod("Wet and Cold SE - German")
        database: TranslationDatabase = DataFactory.database(tmp_path)

        # when
        translation_strings: dict[Path, StringList] = (
            StringExtractor.map_strings_from_mods(translated_mod, original_mod)
        )
        created_translation: Translation = DatabaseService.create_translation_from_mod(
            translated_mod,
            original_mod,
            translation_strings,
            database,
            add_and_save=False,
        )

        # then
        assert len(created_translation.strings) == 2
        assert sorted(created_translation.strings.keys()) == [
            Path("interface/translations/wetandcold_german.txt"),
            Path("WetandCold.esp"),
        ]

        strings: StringList = created_translation.strings[Path("WetandCold.esp")]
        string_hashes: list[int] = list(map(CoreTest.calc_unique_string_hash, strings))

        expected_strings: StringList = [
            PluginString(
                form_id="05062F4E|WetandCold.esp",
                type="ENCH FULL",
                original="Fortify Carry Weight",
                string="Tragfähigkeit verstärken",
                editor_id="_WetEnchArmorFortifyCarry03",
                status=StringStatus.TranslationComplete,
            )
        ]

        assert len(strings) == 204
        for string in expected_strings:
            assert CoreTest.calc_unique_string_hash(string) in string_hashes, (
                f"<{string}> not in actual strings!"
            )

    @staticmethod
    def __load_database_copy(tmp_path: Path) -> TranslationDatabase:
        """
        Copies the test user database to the specified folder and loads it.

        Args:
            tmp_path (Path): The folder to copy the user database to.

        Returns:
            TranslationDatabase: The loaded database copy.
        """

        userdb_path: Path = tmp_path / "userdb"
        shutil.copytree(DATA_PATH / "data" / "user" / "database", userdb_path)

        return DatabaseService.load_database(
            RES_PATH / "app" / "database", userdb_path, GameLanguage.German
        )

    def test_reload_database_updates_changed_strings(self, tmp_path: Path) -> None:
        """
        Tests that `DatabaseService.reload_database()` reloads the strings of existing
        translations in-place.
        """

        # given
        database: TranslationDatabase = TestDatabaseService.__load_database_copy(
            tmp_path
        )
        translation: Translation = next(
            t for t in database.user_translations if t.name.startswith("Wet and Cold")
        )
        json_file: Path = translation.path / "WetandCold.esp.json"
        raw_strings: list[dict[str, Any]] = json.loads(
            json_file.read_text(encoding="utf-8")
        )
        raw_strings[0]["string"] = "Alte Konfiguration"
        raw_strings[0]["status"] = "TranslationIncomplete"
        json_file.write_text(json.dumps(raw_strings), encoding="utf-8")

        changed: list[Translation] = []
        reloaded: list[tuple[list[Translation], list[Path]]] = []
        database.changed_signal.connect(changed.append)
        database.reload_signal.connect(lambda t, m: reloaded.append((t, m)))

        # when
        result: DatabaseReloadResult = DatabaseService.reload_database(database)

        # then
        assert result == DatabaseReloadResult(reloaded=2, added=0, removed=0, failed=0)
        reloaded_translation: Translation = next(
            t for t in database.user_translations if t.name.startswith("Wet and Cold")
        )
        assert reloaded_translation is translation
        assert translation.strings[Path("WetandCold.esp")][0].string == (
            "Alte Konfiguration"
        )
        assert not translation.is_complete
        assert translation in changed
        assert len(reloaded) == 1
        assert translation in reloaded[0][0]
        assert reloaded[0][1] == []

    def test_reload_database_reports_removed_modfiles(self, tmp_path: Path) -> None:
        """
        Tests that `DatabaseService.reload_database()` reports mod files that were
        removed from a translation.
        """

        # given
        database: TranslationDatabase = TestDatabaseService.__load_database_copy(
            tmp_path
        )
        translation: Translation = next(
            t for t in database.user_translations if t.name.startswith("Wet and Cold")
        )
        (translation.path / "WetandCold.esp.json").unlink()

        reloaded: list[tuple[list[Translation], list[Path]]] = []
        database.reload_signal.connect(lambda t, m: reloaded.append((t, m)))

        # when
        DatabaseService.reload_database(database)

        # then
        assert translation.strings == {}
        assert reloaded[0][1] == [Path("WetandCold.esp")]

    def test_reload_database_adds_new_index_entries(self, tmp_path: Path) -> None:
        """
        Tests that `DatabaseService.reload_database()` adds translations that were
        added to the index file.
        """

        # given
        database: TranslationDatabase = TestDatabaseService.__load_database_copy(
            tmp_path
        )
        db_path: Path = database.userdb_path / database.language.id
        shutil.copytree(
            db_path / "Wet and Cold SE - German", db_path / "New Translation"
        )
        index_path: Path = db_path / "index.json"
        index_data: list[dict[str, Any]] = json.loads(
            index_path.read_text(encoding="utf-8")
        )
        index_data.append({"name": "New Translation", "source": "Local"})
        index_path.write_text(json.dumps(index_data), encoding="utf-8")

        added: list[list[Translation]] = []
        database.add_signal.connect(added.append)

        # when
        DatabaseService.reload_database(database)

        # then
        assert len(database.user_translations) == 3
        assert len(added) == 1
        assert [t.name for t in added[0]] == ["New Translation"]
        assert list(added[0][0].strings) == [Path("WetandCold.esp")]

    def test_reload_database_removes_missing_index_entries(self, tmp_path: Path) -> None:
        """
        Tests that `DatabaseService.reload_database()` removes translations that were
        removed from the index file without deleting their files.
        """

        # given
        database: TranslationDatabase = TestDatabaseService.__load_database_copy(
            tmp_path
        )
        db_path: Path = database.userdb_path / database.language.id
        index_path: Path = db_path / "index.json"
        index_data: list[dict[str, Any]] = json.loads(
            index_path.read_text(encoding="utf-8")
        )
        remaining_entries: list[dict[str, Any]] = [
            entry for entry in index_data if not entry["name"].startswith("Wet and Cold")
        ]
        index_path.write_text(json.dumps(remaining_entries), encoding="utf-8")

        removed: list[list[Translation]] = []
        database.remove_signal.connect(removed.append)

        # when
        DatabaseService.reload_database(database)

        # then
        assert [t.name for t in database.user_translations] == [
            "Obsidian Weathers and Seasons - German"
        ]
        assert [t.name for t in removed[0]] == ["Wet and Cold SE - German"]
        assert (db_path / "Wet and Cold SE - German").is_dir()

    def test_reload_database_keeps_translation_with_malformed_file(
        self, tmp_path: Path
    ) -> None:
        """
        Tests that `DatabaseService.reload_database()` leaves a translation unchanged
        and reports an alert if one of its files is malformed.
        """

        # given
        database: TranslationDatabase = TestDatabaseService.__load_database_copy(
            tmp_path
        )
        translation: Translation = next(
            t for t in database.user_translations if t.name.startswith("Wet and Cold")
        )
        old_strings: dict[Path, StringList] = translation.strings
        (translation.path / "WetandCold.esp.json").write_text("{", encoding="utf-8")

        reloaded: list[tuple[list[Translation], list[Path]]] = []
        database.reload_signal.connect(lambda t, m: reloaded.append((t, m)))

        # when
        result: DatabaseReloadResult = DatabaseService.reload_database(database)

        # then
        assert result == DatabaseReloadResult(reloaded=1, added=0, removed=0, failed=1)
        assert translation in database.user_translations
        assert translation.strings is old_strings
        assert translation not in reloaded[0][0]
        assert reloaded[0][1] == []

        alerts: list[Alert] = AlertManager.get().alerts
        assert len(alerts) == 1
        assert alerts[0].severity == Alert.Severity.Error
        assert translation.name in alerts[0].title

    def test_reload_database_keeps_translation_with_invalid_index_entry(
        self, tmp_path: Path
    ) -> None:
        """
        Tests that `DatabaseService.reload_database()` keeps a translation whose index
        entry is present but invalid.
        """

        # given
        database: TranslationDatabase = TestDatabaseService.__load_database_copy(
            tmp_path
        )
        index_path: Path = database.userdb_path / database.language.id / "index.json"
        index_data: list[dict[str, Any]] = json.loads(
            index_path.read_text(encoding="utf-8")
        )
        for entry in index_data:
            entry["timestamp"] = "invalid"
        index_path.write_text(json.dumps(index_data), encoding="utf-8")

        removed: list[list[Translation]] = []
        database.remove_signal.connect(removed.append)

        # when
        result: DatabaseReloadResult = DatabaseService.reload_database(database)

        # then
        assert result == DatabaseReloadResult(reloaded=0, added=0, removed=0, failed=2)
        assert len(database.user_translations) == 2
        assert removed == []
        assert len(AlertManager.get().alerts) == 2
