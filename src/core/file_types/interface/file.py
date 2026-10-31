"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import BinaryIO, ClassVar, Optional, override

from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from PySide6.QtWidgets import QApplication

from core.file_source.file_source_factory import FileSourceFactory
from core.mod_file.context import ModFileContext
from core.mod_file.mod_file import ModFile
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translation_context.related_string import RelatedString

from .string import InterfaceString


class InterfaceFile(ModFile):
    """
    Class for interface translation files (data/interface/translations/*_<language>.txt).
    """

    NEIGHBOR_COUNT: ClassVar[int] = 2
    """Number of preceding and following entries shown as related strings."""

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

        stream: Optional[BinaryIO] = None
        try:
            stream = FileSourceFactory.for_file_path(self.full_path).get_file_stream()

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
                    f"{string.mcm_id}\t{
                        string.string if string.string is not None else string.original
                    }"
                    for string in strings
                    if isinstance(string, InterfaceString)
                ]
            ),
            encoding="utf16",
        )

    @override
    @classmethod
    def get_string_contexts(
        cls,
        mod_file_path: Path,
        strings: StringList,
        all_strings: dict[Path, StringList],
    ) -> ReferenceDict[String, ModFileContext]:
        # Entries are usually grouped by MCM page and option, which makes the adjacent
        # entries the most helpful context.
        file_strings: StringList = all_strings.get(mod_file_path, strings)
        indexes: dict[str, int] = {
            string.id: index for index, string in enumerate(file_strings)
        }
        string_kind: str = QApplication.translate("InterfaceFile", "Interface text")

        contexts: ReferenceDict[String, ModFileContext] = ReferenceDict()
        for string in strings:
            related_strings: list[RelatedString] = []
            index: Optional[int] = indexes.get(string.id)
            if index is not None:
                related_strings = InterfaceFile.__get_neighbors(
                    index, file_strings, mod_file_path
                )

            contexts[string] = ModFileContext(
                string_kind=string_kind, related_strings=related_strings
            )

        return contexts

    @staticmethod
    def __get_neighbors(
        index: int, file_strings: StringList, mod_file_path: Path
    ) -> list[RelatedString]:
        """
        Gets the entries surrounding an entry of an interface file.

        Args:
            index (int): Index of the entry in the file.
            file_strings (StringList): All strings of the file in their file order.
            mod_file_path (Path): Path of the file.

        Returns:
            list[RelatedString]: The surrounding entries in their file order.
        """

        start: int = max(index - InterfaceFile.NEIGHBOR_COUNT, 0)
        end: int = min(index + InterfaceFile.NEIGHBOR_COUNT + 1, len(file_strings))

        neighbors: list[RelatedString] = []
        for neighbor_index in range(start, end):
            if neighbor_index == index:
                continue

            relation: str
            if neighbor_index < index:
                relation = QApplication.translate("InterfaceFile", "Previous entry")
            else:
                relation = QApplication.translate("InterfaceFile", "Next entry")

            neighbors.append(
                RelatedString(
                    relation=relation,
                    string=file_strings[neighbor_index],
                    mod_file=mod_file_path,
                )
            )

        return neighbors
