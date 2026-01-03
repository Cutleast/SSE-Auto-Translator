"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from core.file_source.file_source import FileSource
from core.mod_file.mod_file import ModFile
from core.string.types import StringList

from .phoenix_api import PhoenixApi


class PapyrusFile(ModFile):
    """
    Class for compiled Papyrus scripts (*.pex).
    """

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return ["scripts/*.pex"]

    @override
    @classmethod
    def can_be_in_bsas(cls) -> bool:
        return True

    @override
    def _extract_strings(self) -> StringList:
        return PhoenixApi.get().load_pex_file(
            FileSource.from_file(self.full_path).get_real_file()
        )

    @override
    def dump_strings(
        self,
        strings: StringList,
        output_folder: Path,
        use_dsd_format: bool,
        output_mod: bool = False,
    ) -> None:
        raise NotImplementedError(
            "Writing strings to Papyrus scripts is not yet implemented!"
        )
