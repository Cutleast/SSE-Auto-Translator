"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from enum import Enum, auto

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QTreeWidgetItem


@dataclass
class String:
    """
    Class for translation strings.
    """

    editor_id: str | None
    """
    EditorIDs are the IDs that are visible in CK, xTranslator and xEdit
    but not all strings do have one.
    """

    form_id: str | None
    """
    FormIDs are hexadecimal numbers that identify the record of the string.
    """

    index: int | None
    """
    String index in current record (only for INFO and QUST).
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

    class Status(Enum):
        """
        Enum for string status.
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
        def get(cls, name: str, default=None, /):
            try:
                return cls[name]
            except KeyError:
                return default

        @classmethod
        def get_color(cls, status: "String.Status") -> QColor | None:
            COLORS = {
                cls.NoTranslationRequired: QColor.fromString("#e9e042"),
                cls.TranslationComplete: QColor.fromString("#51c6d9"),
                cls.TranslationIncomplete: QColor.fromString("#c24cd4"),
                cls.TranslationRequired: QColor.fromString("#d74343"),
            }

            return COLORS.get(status)

        @classmethod
        def get_members(cls):
            result: list[cls] = [
                cls.NoTranslationRequired,
                cls.TranslationComplete,
                cls.TranslationIncomplete,
                cls.TranslationRequired,
            ]

            return result

    status: Status = None
    """
    Status visible in Editor Tab.
    """

    tree_item: QTreeWidgetItem = None
    """
    Tree Item in Editor Tab.
    """

    @classmethod
    def from_string_data(cls, string_data: dict[str, str]) -> "String":
        if "original" in string_data:
            status = cls.Status.get(
                string_data.get("status"), cls.Status.TranslationComplete
            )

            editor_id = string_data["editor_id"]
            form_id = string_data.get("form_id")
            if editor_id and not form_id:
                if editor_id.startswith("[") and editor_id.endswith("]"):
                    form_id = editor_id
                    editor_id = None

            return String(
                editor_id=editor_id,
                form_id=form_id,
                index=string_data.get("index"),
                type=string_data["type"],
                original_string=string_data["original"],
                translated_string=string_data["string"],
                status=status,
            )

        else:
            status = cls.Status.get(
                string_data.get("status"), cls.Status.TranslationRequired
            )

            editor_id = string_data["editor_id"]
            form_id = string_data.get("form_id")
            if editor_id and not form_id:
                if editor_id.startswith("[") and editor_id.endswith("]"):
                    form_id = editor_id
                    editor_id = None

            return String(
                editor_id=editor_id,
                form_id=form_id,
                index=string_data.get("index"),
                type=string_data["type"],
                original_string=string_data["string"],
                status=status,
            )

    def to_string_data(self) -> dict[str, str]:
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

    def __hash__(self):
        return hash((self.form_id.lower(), self.editor_id, self.index, self.type))

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, String):
            return hash(__value) == hash(self)

        raise ValueError(
            f"Comparison between String and object of type {type(__value)} not possible!"
        )
