"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import field
from enum import auto
from typing import Any, Iterable, Optional, TypeVar, override

from pydantic.dataclasses import dataclass
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from core.utilities.base_enum import BaseEnum
from core.utilities.container_utils import unique

T = TypeVar("T")


@dataclass
class String:
    """
    Class for translation strings.
    """

    form_id: str
    """
    FormIDs are hexadecimal numbers that identify the record of the string.
    """

    type: str
    """
    Scheme: Record Subrecord, for eg. WEAP FULL
    """

    original_string: str
    """
    String from original Plugin.
    """

    translated_string: str | None = None
    """
    Is None if string has no translation.
    """

    index: int | None = None
    """
    String index in current record (only for INFO and QUST).
    """

    editor_id: str | None = None
    """
    EditorIDs are the IDs that are visible in CK, xTranslator and xEdit
    but not all strings do have one.
    """

    class Status(BaseEnum):
        """
        Enum for string status.
        """

        NoneStatus = auto()
        """
        String has no particular status.
        """

        NoTranslationRequired = auto()
        """
        String is marked as "No Translation Required" by user.
        """

        TranslationComplete = auto()
        """
        String is completely translated and validated by user.
        """

        TranslationIncomplete = auto()
        """
        String is automatically translated but not validated by user
        or user has partially translated this string.
        """

        TranslationRequired = auto()
        """
        String is not translated.
        """

        @classmethod
        def get_color(cls, status: "String.Status") -> Optional[QColor]:
            COLORS = {
                cls.NoTranslationRequired: QColor.fromString("#e9e042"),
                cls.TranslationComplete: QColor.fromString("#51c6d9"),
                cls.TranslationIncomplete: QColor.fromString("#c24cd4"),
                cls.TranslationRequired: QColor.fromString("#d74343"),
            }

            return COLORS.get(status)

        def get_localized_name(self) -> str:
            LOC_NAMES: dict["String.Status", str] = {
                String.Status.NoneStatus: QApplication.translate(
                    "string", "No status (no color)"
                ),
                String.Status.NoTranslationRequired: QApplication.translate(
                    "string", "String does not require a translation"
                ),
                String.Status.TranslationComplete: QApplication.translate(
                    "string", "String is completely translated"
                ),
                String.Status.TranslationIncomplete: QApplication.translate(
                    "string", "String is partially translated"
                ),
                String.Status.TranslationRequired: QApplication.translate(
                    "string", "String requires a translation"
                ),
            }

            return LOC_NAMES[self]

        def get_localized_filter_name(self) -> str:
            LOC_NAMES: dict["String.Status", str] = {
                String.Status.NoneStatus: QApplication.translate(
                    "string", "Show stateless strings"
                ),
                String.Status.NoTranslationRequired: QApplication.translate(
                    "string", "Show strings that do not require a translation"
                ),
                String.Status.TranslationComplete: QApplication.translate(
                    "string", "Show strings that are completely translated"
                ),
                String.Status.TranslationIncomplete: QApplication.translate(
                    "string", "Show strings that are partially translated"
                ),
                String.Status.TranslationRequired: QApplication.translate(
                    "string", "Show strings that require a translation"
                ),
            }

            return LOC_NAMES[self]

    status: Status = field(default=Status.NoneStatus)
    """
    Status visible in Editor Tab.
    """

    @classmethod
    def from_string_data(cls, string_data: dict[str, Any]) -> "String":
        editor_id: Optional[str] = string_data.get("editor_id")
        form_id: Optional[str] = string_data.get("form_id")
        index: Optional[int | str] = string_data.get("index")
        if isinstance(index, str):
            index = int(index)

        if form_id is None:
            raise ValueError("String data has no FormID!")

        if "original" in string_data:
            status = cls.Status.get(
                string_data.get("status", "TranslationComplete"),
                cls.Status.TranslationComplete,
            )

            return String(
                editor_id=editor_id,
                form_id=form_id,
                index=index,
                type=string_data["type"],
                original_string=string_data["original"],
                translated_string=string_data["string"],
                status=status,
            )

        else:
            status = cls.Status.get(
                string_data.get("status", "TranslationRequired"),
                cls.Status.TranslationRequired,
            )

            return String(
                editor_id=editor_id,
                form_id=form_id,
                index=index,
                type=string_data["type"],
                original_string=string_data["string"],
                status=status,
            )

    def to_string_data(self) -> dict[str, Optional[str | int]]:
        if self.translated_string is not None:
            return {
                "editor_id": self.editor_id,
                "form_id": self.form_id,
                "index": self.index,
                "type": self.type,
                "original": self.original_string,
                "string": self.translated_string,
                "status": self.status.name,
            }
        else:
            return {
                "editor_id": self.editor_id,
                "form_id": self.form_id,
                "index": self.index,
                "type": self.type,
                "string": self.original_string,
                "status": self.status.name,
            }

    @property
    def id(self) -> str:
        """
        Generates a unique ID for the string. Intended only for internal use.

        Included attributes:
        - `form_id`
        - `editor_id`
        - `type`
        - `index`
        """

        return f"{self.form_id[2:].lower()}###{self.editor_id}###{self.type}###{self.index}"

    @override
    def __hash__(self) -> int:
        return hash(
            (self.id, self.original_string, self.translated_string, self.status)
        )

    @override
    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, String):
            return False

        return (
            self.id == value.id
            and self.status == value.status
            and self.translated_string == value.translated_string
        )

    @staticmethod
    def unique(strings: Iterable["String"]) -> list["String"]:
        """
        Removes duplicates from a list of strings. Unique strings are
        identified by `String.id`.

        Convenience method for
            `unique(strings, key=lambda s: s.id)`.

        Args:
            strings: Iterable with duplicate strings.

        Returns:
            List of strings without duplicates.
        """

        return unique(strings, key=lambda s: s.id)

    # def __hash__(self) -> int:
    #     return hash((self.form_id[2:].lower(), self.editor_id, self.type, self.index))

    # def __eq__(self, __value: object) -> bool:
    #     if isinstance(__value, String):
    #         return hash(__value) == hash(self)

    #     raise ValueError(
    #         f"Comparison between String and object of type {type(__value)} not possible!"
    #     )
