"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from core.database.translation_service import TranslationService
from core.plugin_interface.plugin import Plugin
from core.string import StringList

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
        return Plugin(self.full_path).extract_strings(unfiltered=True)

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
            plugin = Plugin(self.full_path)
            plugin.replace_strings(strings)

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
