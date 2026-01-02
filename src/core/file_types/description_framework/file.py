"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from core.mod_file.mod_file import ModFile
from core.string.string_status import StringStatus
from core.string.types import StringList

from .string import DescriptionFwString


class DescriptionFwFile(ModFile):
    """
    Class for Description Framework files (data/*_DESC.ini).
    """

    @property
    @override
    def path(self) -> Path:
        return Path(self.name)

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return ["*_DESC.ini"]

    @override
    @classmethod
    def can_be_in_bsas(cls) -> bool:
        return False

    @override
    def _extract_strings(self) -> StringList:
        result: StringList = []

        lines: list[str] = self.full_path.read_text(encoding="utf8").splitlines()
        for line in lines:
            if not line.strip() or line.startswith("#"):
                continue

            try:
                string_id, string = line.split("|", 1)
                string, priority = string.rsplit("|", 1)

                if string_id and string:
                    result.append(
                        DescriptionFwString(
                            string_id=string_id.strip(),
                            priority=int(priority) if priority else None,
                            original=string.strip(),
                            status=StringStatus.TranslationRequired,
                        )
                    )
            except ValueError:
                continue

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
                    f"{string.string_id}|{string.string}|{string.priority or 0}"
                    for string in strings
                    if isinstance(string, DescriptionFwString)
                ]
            ),
            encoding="utf8",
        )
