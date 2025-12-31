"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from core.file_source.file_source import FileSource
from core.mod_file.mod_file import ModFile
from core.string.string_status import StringStatus
from core.string.types import StringList

from .string import InterfaceString


class InterfaceFile(ModFile):
    """
    Class for interface translation files (data/interface/translations/*_<language>.txt).
    """

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return [f"interface/translations/*_{language}.txt"]

    @override
    @classmethod
    def can_be_in_bsas(cls) -> bool:
        return True

    @override
    def _extract_strings(self) -> StringList:
        result: StringList = []

        stream = None
        try:
            stream = FileSource.from_file(self.full_path).get_file_stream()

            for line in stream.read().decode("utf-16").splitlines():
                if not line.strip():
                    continue

                try:
                    string_id, string = line.split("\t", 1)

                    if string_id and string:
                        result.append(
                            InterfaceString(
                                mcm_id=string_id.strip(),
                                original=string.strip(),
                                status=StringStatus.TranslationRequired,
                            )
                        )
                except ValueError:
                    continue

        finally:
            if stream is not None:
                stream.close()

        return result

    @override
    def dump_strings(
        self,
        strings: StringList,
        output_folder: Path,
        use_dsd_format: bool,
        output_mod: bool = False,
    ) -> None:
        output_file: Path = output_folder / self.path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            "\n".join(
                [
                    f"{string.mcm_id}\t{string.string}"
                    for string in strings
                    if isinstance(string, InterfaceString)
                ]
            ),
            encoding="utf16",
        )
