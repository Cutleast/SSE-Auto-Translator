"""
Copyright (c) Cutleast
"""

import json
import logging
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction  # type: ignore
from pathlib import Path
from typing import Any, NoReturn, Optional, override

from sse_bsa import BSAArchive

from core.plugin_interface.plugin import Plugin
from core.string.string import String
from core.string_table_parser.string_table import StringTable
from core.string_table_parser.string_table_parser import StringTableParser
from core.utilities.constants import BASE_GAME_PLUGINS
from core.utilities.filesystem import split_path_with_bsa
from utilities.utility import Utility


class DbGen(Utility):
    """
    Utility that creates translation databases from a localized translation.
    """

    COMMAND: str = "dbgen"
    INPUT_FOLDER_ARG_NAME: str = "input_folder"
    INPUT_FOLDER_ARG_HELP: str = (
        "Path to the input folder (eg. Data folder of the game)"
    )
    STRINGS_FOLDER_ARG_NAME: str = "strings_folder"
    STRINGS_FOLDER_ARG_HELP: str = (
        "Path to the folder with the translated .dlstring/.ilstrings/.strings files."
    )
    LANGUAGE_ARG_NAME: str = "language"
    LANGUAGE_ARG_HELP: str = (
        'Language of the translated strings files. Must not be "english"!'
    )
    OUTPUT_PATH_ARG_ID: str = "output_path"
    OUTPUT_PATH_ARG_NAMES: tuple[str, str] = ("--output-path", "-o")
    OUTPUT_PATH_ARG_HELP: str = "Optional path to output folder"
    HELP: str = "Creates a translation database from a localized translation."

    VANILLA_STRINGS_BSAS: tuple[str, str] = (
        "Skyrim - Interface.bsa",
        "Skyrim - Patch.bsa",
    )
    """
    These BSA files contain the strings for the base game plugins and should be
    processed in this order because the patch file is newer and should overwrite
    the interface file.
    """

    @override
    def __repr__(self) -> str:
        return "DbGen"

    @override
    def add_subparser(self, subparsers: _SubParsersAction) -> None:
        subparser: ArgumentParser = subparsers.add_parser(
            DbGen.COMMAND, help=DbGen.HELP
        )
        subparser.add_argument(
            DbGen.INPUT_FOLDER_ARG_NAME, help=DbGen.INPUT_FOLDER_ARG_HELP
        )
        subparser.add_argument(
            DbGen.STRINGS_FOLDER_ARG_NAME, help=DbGen.STRINGS_FOLDER_ARG_HELP
        )
        subparser.add_argument(DbGen.LANGUAGE_ARG_NAME, help=DbGen.LANGUAGE_ARG_HELP)
        subparser.add_argument(
            *DbGen.OUTPUT_PATH_ARG_NAMES, help=DbGen.OUTPUT_PATH_ARG_HELP
        )

    @override
    def run(self, args: Namespace, exit: bool = True) -> None | NoReturn:
        activated: bool = (
            hasattr(args, DbGen.INPUT_FOLDER_ARG_NAME)
            and hasattr(args, DbGen.STRINGS_FOLDER_ARG_NAME)
            and hasattr(args, DbGen.LANGUAGE_ARG_NAME)
        )

        if not activated:
            # Just continue with normal execution since module was not enabled
            return

        input_folder_name: Optional[str] = getattr(args, DbGen.INPUT_FOLDER_ARG_NAME)
        strings_folder_name: Optional[str] = getattr(
            args, DbGen.STRINGS_FOLDER_ARG_NAME
        )
        language_name: Optional[str] = getattr(args, DbGen.LANGUAGE_ARG_NAME)
        output_path_name: Optional[str] = getattr(args, DbGen.OUTPUT_PATH_ARG_ID)
        output_folder_path: Optional[Path] = (
            Path(output_path_name) if output_path_name else None
        )

        input_folder_path: Path
        strings_folder_path: Path
        input_folder_path, strings_folder_path = self.validate_args(
            input_folder_name, strings_folder_name
        )

        if language_name is None:
            # TODO: Add support for "*" to generate databases for all languages
            raise ValueError("Language is not specified!")

        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

        self.create_database(
            input_folder_path, strings_folder_path, language_name, output_folder_path
        )

        if exit:
            sys.exit(0)

    def create_database(
        self,
        input_folder_path: Path,
        strings_folder_path: Path,
        language_name: str,
        output_folder_path: Optional[Path] = None,
    ) -> None:
        """
        Creates a translation database from a localized translation.

        Args:
            input_folder_path (Path): Folder with plugins.
            strings_folder_path (Path): Folder with strings files.
            language_name (str): Name of the language.
            output_folder_path (Optional[Path], optional):
                Path to output folder. Defaults to None.
        """

        self.log.info("Creating translation database...")

        original_string_tables: dict[str, dict[int, str]] = self.get_string_tables(
            input_folder_path, input_folder_path, "english"
        )
        translated_string_tables: dict[str, dict[int, str]] = self.get_string_tables(
            input_folder_path, strings_folder_path, language_name
        )
        plugin_paths: list[Path] = [
            plugin
            for pattern in ["*.esl", "*.esm", "*.esp"]
            for plugin in input_folder_path.glob(pattern)
            if plugin.is_file()
        ]

        self.log.debug("Extracting string ids from plugins...")
        string_ids: dict[Path, dict[int, String]] = {}
        for plugin_path in plugin_paths:
            string_ids[plugin_path] = self.extract_string_ids(plugin_path)

        if output_folder_path is None:
            output_folder_path = Path("dbgen_output")

        database: dict[str, list[dict[str, str | int | None]]] = self.map_string_tables(
            string_ids, original_string_tables, translated_string_tables
        )

        self.log.info(f"Writing database to '{output_folder_path}'...")

        output_folder_path.mkdir(parents=True, exist_ok=True)

        for plugin_name, plugin_strings in database.items():
            output_file_path: Path = output_folder_path / f"{plugin_name}.json"
            self.log.debug(
                f"Writing {len(plugin_strings)} string(s) to '{output_file_path}'..."
            )
            with output_file_path.open("w", encoding="utf-8") as output_file:
                json.dump(plugin_strings, output_file, indent=4, ensure_ascii=False)

        self.log.info(f"Database generation completed for {len(database)} plugin(s).")

    def get_string_tables(
        self, plugins_folder_path: Path, strings_folder_path: Path, language_name: str
    ) -> dict[str, dict[int, str]]:
        """
        Maps plugins in the specified plugins folder to the strings files
        in the strings folder and extracts the string tables for the specified language.

        Args:
            plugins_folder_path (Path): Folder with plugins.
            strings_folder_path (Path): Folder with strings files.
            language_name (str): Name of the language.

        Returns:
            dict[str, dict[int, str]]:
                Dictionary with plugin names, string ids and strings
        """

        self.log.debug(
            f"Mapping strings files from plugins in '{plugins_folder_path}'"
            f" to '{strings_folder_path}'..."
        )
        strings_files: dict[Path, list[Path]] = DbGen.map_strings_files(
            plugins_folder_path, strings_folder_path
        )

        self.log.debug(
            f"Extracting string tables for {len(strings_files)} "
            f"plugin(s) for language {language_name!r}..."
        )
        string_tables: dict[str, dict[int, str]] = {}
        for plugin_path, string_table_paths in strings_files.items():
            string_tables[plugin_path.name.lower()] = self.extract_string_tables(
                string_table_paths, language_name
            )

        return string_tables

    def map_string_tables(
        self,
        string_ids: dict[Path, dict[int, String]],
        original_string_tables: dict[str, dict[int, str]],
        translated_string_tables: dict[str, dict[int, str]],
    ) -> dict[str, list[dict[str, str | int | None]]]:
        """
        Maps string ids to the specified original string tables
        and translated string tables.

        Args:
            string_ids (dict[Path, dict[int, String]]):
                Dictionary with plugin paths, string ids and strings
            original_string_tables (dict[str, dict[int, str]]):
                Dictionary with plugin names, string ids and original strings
            translated_string_tables (dict[str, dict[int, str]]):
                Dictionary with plugin names, string ids and translated strings

        Returns:
            dict[str, list[dict[str, str | int | None]]]:
                Dictionary with plugin names and list of database-ready strings
        """

        self.log.info("Mapping strings to string ids...")

        database: dict[str, list[dict[str, Any]]] = {}
        for plugin_path, strings in string_ids.items():
            plugin_name: str = plugin_path.name.lower()

            if plugin_name not in original_string_tables:
                self.log.warning(
                    f"Plugin {plugin_path.name!r} has no original string table. "
                    "Skipping..."
                )
                continue

            if plugin_name not in translated_string_tables:
                self.log.warning(
                    f"Plugin {plugin_path.name!r} has no translated string table. "
                    "Skipping..."
                )
                continue

            original_string_table: dict[int, str] = original_string_tables[plugin_name]
            translated_string_table: dict[int, str] = translated_string_tables[
                plugin_name
            ]

            plugin_strings: list[dict[str, str | int | None]] = []
            for string_id, string in strings.items():
                if string_id not in original_string_table:
                    self.log.warning(
                        f"String id {string_id} is not in original string table. "
                        "Skipping..."
                    )
                    continue

                if string_id not in translated_string_table:
                    self.log.warning(
                        f"String id {string_id} is not in translated string table. "
                        "Skipping..."
                    )
                    continue

                string_data: dict[str, str | int | None] = string.model_dump(
                    mode="json"
                )
                string_data["original"] = original_string_table[string_id]
                string_data["string"] = translated_string_table[string_id]
                string_data.pop("status")  # Don't store status in database
                plugin_strings.append(string_data)

            if plugin_strings:
                database[plugin_name] = plugin_strings

        return database

    @staticmethod
    def map_strings_files(
        input_folder_path: Path, strings_folder_path: Path
    ) -> dict[Path, list[Path]]:
        """
        Maps plugins from the input folder to a list of their strings files
        in the strings folder.

        Args:
            input_folder_path (Path):
                Path to the folder with the plugins (eg. Data folder).
            strings_folder_path (Path): Path to the folder with the strings files

        Returns:
            dict[Path, list[Path]]:
                Dictionary with plugins as keys and strings files as values
        """

        plugins: list[Path] = [
            plugin
            for pattern in ["*.esl", "*.esm", "*.esp"]
            for plugin in input_folder_path.glob(pattern)
            if plugin.is_file()
        ]

        result: dict[Path, list[Path]] = {}

        bsa_file: Path
        for plugin in plugins:
            if plugin.name.lower() in BASE_GAME_PLUGINS:
                strings_files: dict[str, Path] = {}

                for bsa in DbGen.VANILLA_STRINGS_BSAS:
                    bsa_file = strings_folder_path / bsa
                    if bsa_file.is_file():
                        strings_files.update(
                            {
                                f: bsa_file / f
                                for f in DbGen.get_strings_files_from_bsa(
                                    bsa_file, plugin.stem
                                )
                            }
                        )

                if strings_files:
                    result[plugin] = list(strings_files.values())

            else:
                bsa_file = strings_folder_path / (plugin.stem + ".bsa")
                if bsa_file.is_file():
                    result[plugin] = [
                        bsa_file / f
                        for f in DbGen.get_strings_files_from_bsa(bsa_file, plugin.stem)
                    ]

                result.setdefault(plugin, []).extend(
                    strings_folder_path.glob(f"{plugin.name}_*.*strings")
                )

        return result

    @staticmethod
    def get_strings_files_from_bsa(bsa_file_path: Path, plugin_stem: str) -> list[str]:
        """
        Gets a list of strings files for the specified plugin name from the
        specified BSA file.

        Args:
            bsa_file_path (Path): Path to the BSA file
            plugin_stem (str): Name of the plugin without suffix

        Returns:
            list[str]: List of strings files
        """

        archive = BSAArchive(bsa_file_path)
        files: list[str] = archive.glob(f"strings/{plugin_stem.lower()}_*.*strings")

        return files

    def extract_string_tables(
        self, strings_files: list[Path], language: str
    ) -> dict[int, str]:
        """
        Extracts the string tables from the specified strings files
        for the specifed plugin stem and language.

        Args:
            strings_files (list[Path]): List of strings files for this plugin
            language (str): Language to extract strings for

        Returns:
            dict[int, str]: Dictionary with string ids and strings
        """

        string_tables: dict[int, str] = {}

        for strings_file in filter(lambda f: language in f.name, strings_files):
            bsa_path: Optional[Path]
            bsa_string_file: Optional[Path]
            bsa_path, bsa_string_file = split_path_with_bsa(strings_file)

            if bsa_string_file is None:
                raise ValueError("Strings file must not be a BSA file!")

            self.log.info(f"Extracting strings from {strings_file.name!r}...")
            parser = StringTableParser(strings_file)

            string_table: StringTable
            if bsa_path is not None:
                archive = BSAArchive(bsa_path)
                string_table = parser.parse(
                    archive.get_file_stream(str(bsa_string_file).replace("\\", "/"))
                )
            else:
                with strings_file.open("rb") as stream:
                    string_table = parser.parse(stream)

            additional_strings: dict[int, str] = string_table.extract_strings()
            string_tables.update(additional_strings)
            self.log.info(f"Extracted {len(additional_strings)} string(s).")

        return string_tables

    def extract_string_ids(self, plugin_path: Path) -> dict[int, String]:
        """
        Parses and extracts string ids from the specified plugin.

        Args:
            plugin_path (Path): Path to the plugin

        Returns:
            dict[int, String]: Dictionary with string ids and strings
        """

        self.log.info(f"Extracting string ids from {plugin_path.name!r}...")

        plugin = Plugin(plugin_path)
        string_ids: dict[int, String] = {
            int(string.original): string
            for string in plugin.extract_strings(
                extract_localized=True, unfiltered=True
            )
        }

        self.log.info(f"Extracted {len(string_ids)} string(s).")

        return string_ids

    def validate_args(
        self, input_folder_name: Optional[str], strings_folder_name: Optional[str]
    ) -> tuple[Path, Path]:
        """
        Validates arguments and returns tuple with two paths.

        Args:
            input_folder_name (Optional[str]):
                Specified path to input folder (eg. Data folder of the game).
            strings_folder_name (Optional[str]): Specified path to strings folder

        Raises:
            ValueError: If input folder or strings folder is not specified

        Returns:
            tuple[Path, Path]: Paths to input folder and strings folder
        """

        if input_folder_name is None or not input_folder_name.strip():
            raise ValueError("Input folder is required")
        elif strings_folder_name is None or not strings_folder_name.strip():
            raise ValueError("Strings folder is required")

        return Path(input_folder_name), Path(strings_folder_name)
