"""
Copyright (c) Cutleast
"""

import json
import shutil
from pathlib import Path
from struct import pack
from typing import Optional

import pytest
from bethkit import (
    BsaVersion,
    BsaWriter,
    Game,
    PluginWriter,
    StringFileKind,
    StringTable,
    WritableGroup,
    WritableRecord,
)

from core.file_types.plugin.file import ExternalStringId
from core.file_types.plugin.string import PluginString
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
        string_tables: dict[str, dict[ExternalStringId, str]] = db_gen.get_string_tables(
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
        string_tables: dict[str, dict[ExternalStringId, str]] = db_gen.get_string_tables(
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
        db_data: list[dict[str, Optional[str | int]]] = json.loads(
            db_file.read_text("utf8")
        )

        # then
        assert len(db_data) > 0
        assert db_data[0]["original"]
        assert db_data[0]["string"]
        assert db_data[0]["original"] != db_data[0]["string"]

    def test_create_database_skips_plugins_that_are_not_localized(
        self, data_folder: Path, tmp_path: Path
    ) -> None:
        """
        Tests that `utilities.db_gen.main.DbGen.create_database()` skips plugins that
        are not localized instead of aborting.
        """

        # given
        db_gen = DbGen()
        data_path: Path = data_folder / "db_gen"
        input_folder: Path = tmp_path / "orig"
        shutil.copytree(data_path / "orig", input_folder)
        shutil.copy(data_folder / "esp2dsd" / "orig" / "WetandCold.esp", input_folder)
        output_path: Path = tmp_path / "db_gen_test"

        # when
        db_gen.create_database(input_folder, data_path / "trans", "german", output_path)

        # then
        assert (output_path / "_resourcepack.esl.json").is_file()
        assert not (output_path / "wetandcold.esp.json").exists()

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

    @pytest.mark.parametrize(
        "kind, suffix",
        [
            (StringFileKind.STRINGS, ".strings"),
            (StringFileKind.DL_STRINGS, ".dlstrings"),
            (StringFileKind.IL_STRINGS, ".ilstrings"),
        ],
    )
    @pytest.mark.parametrize("archived", [False, True])
    def test_extract_string_tables(
        self, tmp_path: Path, kind: StringFileKind, suffix: str, archived: bool
    ) -> None:
        """
        Tests non-empty tables of each format from loose files and BSA streams.
        """

        # given
        table_path: Path = tmp_path / f"Example_german{suffix}"
        with StringTable.new(kind) as table:
            table.insert(7, "Grüße 日本語".encode())
            table.insert(8, b" \t\n")
            table.insert(9, b"Not referenced")
            table.write_to_file(table_path)

        if archived:
            archive_path: Path = tmp_path / "Example.bsa"
            with BsaWriter(BsaVersion.SSE) as writer:
                writer.add(f"strings/{table_path.name}", table_path.read_bytes())
                writer.write_to(archive_path)
            table_path = archive_path / "strings" / table_path.name

        db_gen = DbGen()

        # when
        strings: dict[ExternalStringId, str] = db_gen.extract_string_tables(
            [table_path], "german", {(kind, 7), (kind, 8), (kind, 10)}
        )

        # then
        assert strings == {(kind, 7): "Grüße 日本語"}

    def test_extract_legacy_encoding(self, tmp_path: Path) -> None:
        """
        Tests retaining legacy decoding when table payloads are not UTF-8.
        """

        # given
        table_path: Path = tmp_path / "Example_german.strings"
        with StringTable.new(StringFileKind.STRINGS) as table:
            table.insert(7, "Grüße".encode("cp1252"))
            table.write_to_file(table_path)
        db_gen = DbGen()

        # when
        strings: dict[ExternalStringId, str] = db_gen.extract_string_tables(
            [table_path], "german", {(StringFileKind.STRINGS, 7)}
        )

        # then
        assert strings == {(StringFileKind.STRINGS, 7): "Grüße"}

    def test_loose_table_overrides_bsa(self, tmp_path: Path, data_folder: Path) -> None:
        """
        Tests that a loose table overrides matching archived IDs.
        """

        # given
        input_path: Path = data_folder / "db_gen" / "orig"
        archive_path: Path = data_folder / "db_gen" / "trans" / "_ResourcePack.bsa"
        shutil.copyfile(archive_path, tmp_path / archive_path.name)
        db_gen = DbGen()
        references: dict[ExternalStringId, list[PluginString]] = (
            db_gen.extract_string_ids(input_path / "_ResourcePack.esl")
        )
        key: ExternalStringId = next(
            key for key in references if key[0] == StringFileKind.STRINGS
        )
        loose_path: Path = tmp_path / "Strings" / "_ResourcePack_german.strings"
        loose_path.parent.mkdir()
        with StringTable.new(key[0]) as table:
            table.insert(key[1], b"Loose translation")
            table.write_to_file(loose_path)

        # when
        tables: dict[str, dict[ExternalStringId, str]] = db_gen.get_string_tables(
            input_path, tmp_path, "german"
        )

        # then
        assert len(tables["_resourcepack.esl"]) == 27
        assert tables["_resourcepack.esl"][key] == "Loose translation"

    @staticmethod
    def __write_localized_plugin(path: Path) -> None:
        """
        Creates two books sharing a title ID and reusing that ID for a description.

        Args:
            path (Path): Destination plugin path.
        """

        with PluginWriter(Game.SKYRIM_SE) as writer, WritableGroup.new("BOOK") as group:
            writer.set_localized(True)
            for form_id in (0x1234, 0x1235):
                with WritableRecord.new("BOOK", form_id=form_id) as record:
                    record.add_subrecord("EDID", f"Book{form_id}\0".encode())
                    record.add_subrecord("FULL", pack("<I", 7))
                    if form_id == 0x1234:
                        record.add_subrecord("DESC", pack("<I", 7))
                    group.add_record(record)
            writer.add_group(group)
            writer.write_to_file(path)

    @pytest.mark.parametrize("missing_description", [False, True])
    def test_shared_ids_and_table_kinds(
        self, tmp_path: Path, missing_description: bool
    ) -> None:
        """
        Tests table-kind separation, shared-ID references and missing translations.
        """

        # given
        original_path: Path = tmp_path / "original"
        translated_path: Path = tmp_path / "translated"
        original_path.mkdir()
        translated_path.mkdir()
        plugin_path: Path = original_path / "Books.esp"
        TestDbGen.__write_localized_plugin(plugin_path)
        for folder, language, title, description in (
            (original_path, "english", "Book title", "Book description"),
            (translated_path, "german", "Buchtitel", "Buchbeschreibung"),
        ):
            strings_folder: Path = folder / "Strings"
            strings_folder.mkdir()
            for kind, text, suffix in (
                (StringFileKind.STRINGS, title, ".strings"),
                (StringFileKind.DL_STRINGS, description, ".dlstrings"),
            ):
                if (
                    missing_description
                    and language == "german"
                    and suffix == ".dlstrings"
                ):
                    continue
                with StringTable.new(kind) as table:
                    table.insert(7, text.encode("utf-8"))
                    table.write_to_file(strings_folder / f"Books_{language}{suffix}")
        db_gen = DbGen()
        output_folder: Path = tmp_path / "database"

        # when
        db_gen.create_database(original_path, translated_path, "german", output_folder)
        strings: list[dict[str, Optional[str | int]]] = json.loads(
            (output_folder / "books.esp.json").read_text("utf-8")
        )

        # then
        titles: list[dict[str, Optional[str | int]]] = [
            string for string in strings if string["type"] == "BOOK FULL"
        ]
        assert len(titles) == 2
        assert {string["form_id"] for string in titles} == {
            "00001234|Books.esp",
            "00001235|Books.esp",
        }
        assert all(string["original"] == "Book title" for string in titles)
        assert all(string["string"] == "Buchtitel" for string in titles)
        descriptions: list[dict[str, Optional[str | int]]] = [
            string for string in strings if string["type"] == "BOOK DESC"
        ]
        if missing_description:
            assert descriptions == []
        else:
            assert len(descriptions) == 1
            assert descriptions[0]["original"] == "Book description"
            assert descriptions[0]["string"] == "Buchbeschreibung"
