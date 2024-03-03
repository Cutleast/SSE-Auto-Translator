"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QTreeWidgetItem

from enum import Enum, auto
from dataclasses import dataclass


@dataclass
class String:
    """
    Class for translation strings.
    """

    editor_id: str
    """
    Despite the name, this can be a FormID for Dialogues and Quests.
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

            return String(
                editor_id=string_data["editor_id"],
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

            return String(
                editor_id=string_data["editor_id"],
                index=string_data.get("index"),
                type=string_data["type"],
                original_string=string_data["string"],
                status=status,
            )

    def to_string_data(self) -> dict[str, str]:
        if self.translated_string is not None:
            return {
                "editor_id": self.editor_id,
                "index": self.index,
                "type": self.type,
                "original": self.original_string,
                "string": self.translated_string,
                "status": self.status.name,
            }
        else:
            return {
                "editor_id": self.editor_id,
                "index": self.index,
                "type": self.type,
                "string": self.original_string,
                "status": self.status.name,
            }

    def __hash__(self):
        return hash((self.editor_id, self.index, self.type, self.original_string))
