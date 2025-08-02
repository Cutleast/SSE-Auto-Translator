"""
Copyright (c) Cutleast
"""

from pathlib import Path

from PySide6.QtCore import Qt

from core.string.string import String

from .string_list_widget import StringListWidget


class StringListDialog(StringListWidget):
    """
    Dialog window for string preview.
    """

    def __init__(
        self,
        name: str,
        strings: list[String] | dict[Path, list[String]],
        show_translation: bool = False,
    ) -> None:
        super().__init__(strings, show_translation)

        self.setObjectName("root")
        self.setMinimumSize(1400, 800)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowTitle(
            name
            + self.tr(
                " (%n Strings)",
                " (%n String)",
                self.get_visible_item_count(),
            )
        )
