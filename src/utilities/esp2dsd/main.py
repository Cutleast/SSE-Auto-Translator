"""
Copyright (c) Cutleast
"""

import logging
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction  # type: ignore
from pathlib import Path
from typing import NoReturn, Optional, override

from core.database.exporter import Exporter
from core.plugin_interface.plugin import Plugin
from core.string.plugin_string import PluginString
from core.string.string_utils import StringUtils
from utilities.utility import Utility


class Esp2Dsd(Utility):
    """
    Utility that converts a plugin translation to a DSD file.
    """

    COMMAND: str = "esp2dsd"
    TRANSLATED_PLUGIN_ARG_NAME: str = "translated"
    TRANSLATED_PLUGIN_ARG_HELP: str = (
        "Path to the translated plugin or folder with translated plugins"
    )
    ORIGINAL_PLUGIN_ARG_NAME: str = "original"
    ORIGINAL_PLUGIN_ARG_HELP: str = "Path to the original plugin or folder with plugins"
    OUTPUT_PATH_ARG_ID: str = "output_path"
    OUTPUT_PATH_ARG_NAMES: tuple[str, str] = ("--output-path", "-o")
    OUTPUT_PATH_ARG_HELP: str = "Optional path to output folder"
    HELP: str = (
        "Converts a plugin translation to a DSD file. "
        f"Arguments {TRANSLATED_PLUGIN_ARG_NAME!r} and "
        f"{ORIGINAL_PLUGIN_ARG_NAME!r} are required when used."
    )

    @override
    def __repr__(self) -> str:
        return "Esp2Dsd"

    @override
    def add_subparser(self, subparsers: _SubParsersAction) -> None:
        subparser: ArgumentParser = subparsers.add_parser(
            Esp2Dsd.COMMAND, help=Esp2Dsd.HELP
        )
        subparser.add_argument(
            Esp2Dsd.TRANSLATED_PLUGIN_ARG_NAME, help=Esp2Dsd.TRANSLATED_PLUGIN_ARG_HELP
        )
        subparser.add_argument(
            Esp2Dsd.ORIGINAL_PLUGIN_ARG_NAME, help=Esp2Dsd.ORIGINAL_PLUGIN_ARG_HELP
        )
        subparser.add_argument(
            *Esp2Dsd.OUTPUT_PATH_ARG_NAMES, help=Esp2Dsd.OUTPUT_PATH_ARG_HELP
        )

    @override
    def run(self, args: Namespace, exit: bool = True) -> None | NoReturn:
        activated: bool = hasattr(args, Esp2Dsd.ORIGINAL_PLUGIN_ARG_NAME) and hasattr(
            args, Esp2Dsd.TRANSLATED_PLUGIN_ARG_NAME
        )

        if not activated:
            # Just continue with normal execution since module was not enabled
            return

        translated_plugin_name: Optional[str] = getattr(
            args, Esp2Dsd.TRANSLATED_PLUGIN_ARG_NAME, None
        )
        original_plugin_name: Optional[str] = getattr(
            args, Esp2Dsd.ORIGINAL_PLUGIN_ARG_NAME, None
        )
        output_path_name: Optional[str] = getattr(
            args, Esp2Dsd.OUTPUT_PATH_ARG_ID, None
        )

        translated_plugin_path: Path
        original_plugin_path: Path
        translated_plugin_path, original_plugin_path = self.validate_args(
            translated_plugin_name, original_plugin_name
        )

        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

        plugins: dict[Path, Path] = Esp2Dsd.map_plugins(
            translated_plugin_path, original_plugin_path
        )

        self.log.info(f"Converting {len(plugins)} plugins...")
        for p, (translated_plugin, original_plugin) in enumerate(plugins.items()):
            self.log.info(
                f"Converting translated plugin '{translated_plugin_path}' for "
                f"'{original_plugin_path}' to DSD... ({p + 1}/{len(plugins)})"
            )
            self.convert(
                translated_plugin,
                original_plugin,
                Path(output_path_name) if output_path_name is not None else None,
            )

        if exit:
            sys.exit()

    @staticmethod
    def map_plugins(
        translated_plugin_path: Path, original_plugin_path: Path
    ) -> dict[Path, Path]:
        """
        Maps translated and original plugins.

        Args:
            translated_plugin_path (Path): Path to the translated plugin or folder.
            original_plugin_path (Path): Path to the original plugin or folder.

        Raises:
            ValueError: when one of the paths is a folder while the other is a file
            ValueError: when the translated and original plugins have different names

        Returns:
            dict[Path, Path]: Dictionary with translated and original plugins.
        """

        if translated_plugin_path.is_dir() != original_plugin_path.is_dir():
            raise ValueError(
                "Translated and original plugin must both be a file or a folder!"
            )

        plugins: dict[Path, Path]
        if translated_plugin_path.is_dir():
            plugins = {
                original_file: translated_plugin_path / original_file.name
                for suffix in [".esl", ".esm", ".esp"]
                for original_file in original_plugin_path.glob(f"*{suffix}")
                if original_file.is_file()
                and (translated_plugin_path / original_file.name).is_file()
            } | {
                original_plugin_path / translated_file.name: translated_file
                for suffix in [".esl", ".esm", ".esp"]
                for translated_file in translated_plugin_path.glob(f"*{suffix}")
                if translated_file.is_dir()
                and (original_plugin_path / translated_file.name).is_file()
            }
        else:
            if translated_plugin_path.name != original_plugin_path.name:
                raise ValueError(
                    "Translated and original plugin must have the same name!"
                )

            plugins = {
                translated_plugin_path: original_plugin_path,
            }

        return plugins

    def convert(
        self,
        translated_plugin_path: Path,
        original_plugin_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Converts a plugin translation to a DSD file.

        Args:
            translated_plugin_path (Path): Path to the translated plugin.
            original_plugin_path (Path): Path to the original plugin.
            output_path (Optional[Path]): Path to the output folder.
                Defaults to `esp2dsd Output`.

        Returns:
            Path: Path to the folder with the created DSD file.
        """

        self.log.debug(
            f"Converting '{translated_plugin_path}' for '{original_plugin_path}' to DSD..."
        )

        translated_plugin = Plugin(translated_plugin_path)
        translated_strings: list[PluginString] = translated_plugin.extract_strings()
        original_plugin = Plugin(original_plugin_path)
        original_strings: list[PluginString] = original_plugin.extract_strings()

        mapped_strings: list[PluginString] = StringUtils.map_strings(
            original_strings, translated_strings
        )

        output_file_path: Path = Exporter.export_strings_to_dsd(
            mapped_strings,
            Path(original_plugin_path.name),
            output_path or Path("esp2dsd Output"),
        )
        self.log.debug(f"Created output file at '{output_file_path}'.")

        return output_file_path

    @staticmethod
    def validate_args(
        translated_plugin_name: Optional[str], original_plugin_name: Optional[str]
    ) -> tuple[Path, Path]:
        """
        Validates arguments and returns tuple with two paths.

        Args:
            translated_plugin_name (Optional[str]): Specified path to translated plugin or folder
            original_plugin_name (Optional[str]): Specified path to original plugin or folder

        Returns:
            tuple[Path, Path]: Paths to translated and original plugins
        """

        if translated_plugin_name is None or not translated_plugin_name.strip():
            raise ValueError("Translated plugin is required")
        elif original_plugin_name is None or not original_plugin_name.strip():
            raise ValueError("Original plugin is required")

        return Path(translated_plugin_name), Path(original_plugin_name)
