"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path

from utilities.db_gen.main import DbGen

from ...base_test import BaseTest


class TestDbGen(BaseTest):
    """
    Tests `utilities.db_gen.main.DbGen`.
    """

    def test_get_string_tables_german(self, data_folder: Path) -> None:
        """
        Tests `utilities.db_gen.main.DbGen.get_string_tables()` with german.
        """

        # given
        db_gen = DbGen()
        data_path: Path = data_folder / "db_gen"
        input_folder: Path = data_path / "orig"
        strings_folder: Path = data_path / "trans"
        language: str = "german"
        plugin_name: str = "_resourcepack.esl"

        # when
        string_tables: dict[str, dict[int, str]] = db_gen.get_string_tables(
            input_folder, strings_folder, language
        )

        # then
        assert len(string_tables) > 0
        assert plugin_name in string_tables
        assert len(string_tables[plugin_name]) > 0

    def test_get_string_tables_english(self, data_folder: Path) -> None:
        """
        Tests `utilities.db_gen.main.DbGen.get_string_tables()` with english.
        """

        # given
        db_gen = DbGen()
        data_path: Path = data_folder / "db_gen"
        input_folder: Path = data_path / "orig"
        language: str = "english"
        plugin_name: str = "_resourcepack.esl"

        # when
        string_tables: dict[str, dict[int, str]] = db_gen.get_string_tables(
            input_folder, input_folder, language
        )

        # then
        assert len(string_tables) > 0
        assert plugin_name in string_tables
        assert len(string_tables[plugin_name]) > 0

    def test_create_database(self, data_folder: Path) -> None:
        """
        Tests `utilities.db_gen.main.DbGen.create_database()`.
        """

        # given
        db_gen = DbGen()
        data_path: Path = data_folder / "db_gen"
        tmp_path: Path = self.tmp_folder()
        input_folder: Path = data_path / "orig"
        strings_folder: Path = data_path / "trans"
        output_path: Path = tmp_path / "db_gen_test"
        language: str = "german"
        db_file: Path = output_path / "_resourcepack.esl.json"

        # when
        db_gen.create_database(input_folder, strings_folder, language, output_path)

        # then
        assert db_file.is_file()

        # when
        db_data: list[dict[str, str | int | None]] = json.loads(
            db_file.read_text("utf8")
        )

        # then
        assert len(db_data) > 0
        assert db_data[0]["original"]
        assert db_data[0]["string"]
        assert db_data[0]["original"] != db_data[0]["string"]

    def test_get_strings_files_from_bsa(self, data_folder: Path) -> None:
        """
        Tests `utilities.db_gen.main.DbGen.get_strings_files_from_bsa()`.
        """

        # given
        data_path: Path = data_folder / "db_gen"
        bsa_path: Path = data_path / "trans" / "_ResourcePack.bsa"
        plugin_stem: str = "_ResourcePack"

        # when
        strings_files: list[str] = DbGen.get_strings_files_from_bsa(
            bsa_path, plugin_stem
        )

        # then
        assert len(strings_files) == 3
        assert strings_files == [
            "strings\\_resourcepack_german.strings",
            "strings\\_resourcepack_german.ilstrings",
            "strings\\_resourcepack_german.dlstrings",
        ]

    def test_map_strings_files(self, data_folder: Path) -> None:
        """
        Tests `utilities.db_gen.main.DbGen.map_strings_files()`.
        """

        # given
        data_path: Path = data_folder / "db_gen"
        input_folder: Path = data_path / "orig"
        strings_folder: Path = data_path / "trans"
        plugin_path: Path = input_folder / "_ResourcePack.esl"
        trans_bsa_path: Path = strings_folder / "_ResourcePack.bsa"

        # when
        strings_files: dict[Path, list[Path]] = DbGen.map_strings_files(
            input_folder, strings_folder
        )

        # then
        assert len(strings_files) == 1
        assert plugin_path in strings_files
        assert strings_files[plugin_path] == [
            trans_bsa_path / "strings/_resourcepack_german.strings",
            trans_bsa_path / "strings/_resourcepack_german.ilstrings",
            trans_bsa_path / "strings/_resourcepack_german.dlstrings",
        ]
