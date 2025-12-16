"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from sse_plugin_interface.plugin import SSEPlugin
from sse_plugin_interface.plugin_string import PluginString as SSEPluginString
from sse_plugin_interface.utilities import is_valid_string

from core.database.translation_service import TranslationService
from core.file_source.file_source import FileSource
from core.string import PluginString, StringList
from core.string.string_status import StringStatus

from .mod_file import ModFile


class PluginFile(ModFile):
    """
    Class for plugin files (*.esp, *.esm, *.esl).
    """

    @property
    @override
    def path(self) -> Path:
        return Path(self.name)

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return [
            "*.esp",
            "*.esm",
            "*.esl",
        ]

    @override
    @classmethod
    def can_be_in_bsas(cls) -> bool:
        return False

    @override
    def _extract_strings(self) -> StringList:
        plugin = SSEPlugin.from_stream(
            FileSource.from_file(self.full_path).get_file_stream(), self.name
        )

        raw_strings: list[SSEPluginString] = plugin.extract_strings()

        return PluginFile.convert_sse_plugin_strings(raw_strings)

    @staticmethod
    def convert_sse_plugin_strings(raw_strings: list[SSEPluginString]) -> StringList:
        """
        Converts a list of raw extracted plugin strings to the translatable objects used
        by SSE-AT. Also filters out blank strings.

        Args:
            raw_strings (list[SSEPluginString]): List of raw strings.

        Returns:
            StringList: List of translatable strings.
        """

        strings: StringList = []
        for raw_string in raw_strings:
            if not raw_string.string.strip():
                continue

            string = PluginString(
                editor_id=raw_string.editor_id,
                form_id=raw_string.form_id,
                index=raw_string.index,
                type=raw_string.type,
                original=raw_string.string,
                status=(
                    StringStatus.TranslationRequired
                    if is_valid_string(raw_string.string)
                    else StringStatus.NoTranslationRequired
                ),
            )
            strings.append(string)

        return strings

    @override
    def dump_strings(
        self,
        strings: StringList,
        output_folder: Path,
        use_dsd_format: bool,
        output_mod: bool = False,
    ) -> None:
        if use_dsd_format:
            self.__export_strings_to_dsd(strings, output_folder, output_mod)
        else:
            plugin = SSEPlugin.from_stream(
                FileSource.from_file(self.full_path).get_file_stream(), self.name
            )

            replacement_strings: list[SSEPluginString] = []
            for string in strings:
                if not isinstance(string, PluginString):
                    continue

                replacement_string = SSEPluginString(
                    editor_id=string.editor_id,
                    form_id=string.form_id,
                    index=string.index,
                    type=string.type,
                    string=(
                        string.string if string.string is not None else string.original
                    ),
                )
                replacement_strings.append(replacement_string)

            plugin.replace_strings(replacement_strings)

            output_file: Path = output_folder / self.path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(plugin.dump())

    def __export_strings_to_dsd(
        self, strings: StringList, path: Path, output_mod: bool = False
    ) -> Path:
        """
        Exports strings to a DSD file at the specified path.

        Args:
            strings (StringList): Strings to export.
            path (Path): Path to export to.
            output_mod (bool, optional):
                Whether the export is used in the output mod. Affects the JSON filename.
                Defaults to False.

        Returns:
            Path: Path to the exported DSD file.
        """

        plugin_folder: Path = (
            path / "SKSE" / "Plugins" / "DynamicStringDistributor" / self.path
        )

        plugin_folder.mkdir(parents=True, exist_ok=True)

        json_filename: str
        if output_mod:
            # the output mod uses a different naming scheme to prevent it from being
            # imported again by SSE-AT
            json_filename = "SSE-AT_output.json"
        else:
            json_filename = "SSE-AT_exported.json"

        strings = list(
            filter(
                lambda s: (s.original != s.string and s.string),
                strings,
            )
        )

        dsd_path: Path = plugin_folder / json_filename
        TranslationService.save_strings_to_json_file(dsd_path, strings, indent=4)

        return dsd_path
