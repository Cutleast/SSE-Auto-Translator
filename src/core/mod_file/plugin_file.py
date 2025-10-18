"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

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
        from core.database.exporter import Exporter

        if use_dsd_format:
            Exporter.export_strings_to_dsd(
                strings, self.path, output_folder, output_mod=output_mod
            )
        else:
            plugin = Plugin(self.full_path)
            plugin.replace_strings(strings)

            output_file: Path = output_folder / self.path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(plugin.dump())
