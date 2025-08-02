"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt

from .string_list_widget import StringListWidget, Strings


class StringListDialog(StringListWidget):
    """
    Dialog window for string preview.
    """

    def __init__(
        self, name: str, strings: Strings, show_translation: bool = False
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
