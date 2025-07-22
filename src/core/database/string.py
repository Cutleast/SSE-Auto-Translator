"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from __future__ import annotations

from enum import auto
from typing import Annotated, Any, Iterable, Optional, TypeVar, override

from pydantic import BaseModel, BeforeValidator, PlainSerializer, model_validator
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from core.utilities.container_utils import unique
from core.utilities.localized_enum import LocalizedEnum

T = TypeVar("T")


class String(BaseModel):
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

    original: str
    """
    String from original Plugin.
    """

    string: Optional[str] = None
    """
    Is None if string has no translation.
    """

    index: Optional[int] = None
    """
    String index in current record (only for INFO and QUST).
    """

    editor_id: Optional[str] = None
    """
    EditorIDs are the IDs that are visible in CK, xTranslator and xEdit
    but not all strings do have one.
    """

    class Status(LocalizedEnum):
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
        def get_color(cls, status: String.Status) -> Optional[QColor]:
            COLORS = {
                cls.NoTranslationRequired: QColor.fromString("#e9e042"),
                cls.TranslationComplete: QColor.fromString("#51c6d9"),
                cls.TranslationIncomplete: QColor.fromString("#c24cd4"),
                cls.TranslationRequired: QColor.fromString("#d74343"),
            }

            return COLORS.get(status)

        @override
        def get_localized_name(self) -> str:
            LOC_NAMES: dict[String.Status, str] = {
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

        @override
        def get_localized_description(self) -> str:
            return self.get_localized_name()

        def get_localized_filter_name(self) -> str:
            LOC_NAMES: dict[String.Status, str] = {
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

    status: Annotated[
        Status,
        # Deserialize by name
        BeforeValidator(
            lambda member: (
                String.Status[member]
                if not isinstance(member, String.Status)
                else member
            )
        ),
        # Serialize by name
        PlainSerializer(
            lambda member: member.name, return_type=str, when_used="always"
        ),
    ] = Status.NoneStatus
    """
    Status visible in Editor Tab.
    """

    @property
    def id(self) -> str:
        """
        Generates a unique ID for the string. Intended only for internal use.

        Included attributes:
        - lowered `form_id` without master index (first two digits)
        - `editor_id`
        - `type`
        - `index`
        """

        return f"{self.form_id[2:].lower()}###{self.editor_id}###{self.type}###{self.index}"

    @model_validator(mode="before")
    @classmethod
    def check_translated_string(cls, data: T) -> T:
        """
        Checks if the string has a translation and sets the status if it doesn't.

        Args:
            data (T): Raw string data.

        Returns:
            T: Raw string data.
        """

        if isinstance(data, dict):
            if "original" not in data and "string" in data:
                data["original"] = data.pop("string")
                data["status"] = String.Status.TranslationRequired.name

        return data

    @override
    def __hash__(self) -> int:
        return hash((self.id, self.original, self.string, self.status))

    @override
    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, String):
            return False

        return (
            self.id == value.id
            and self.status == value.status
            and self.string == value.string
        )

    @staticmethod
    def unique(strings: Iterable[String]) -> list[String]:
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
