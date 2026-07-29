"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt

from .string_list_widget import StringListWidget, Strings


class StringListWindow(StringListWidget):
    """
    Window for displaying a list of strings.
    """

    def __init__(
        self, name: str, strings: Strings, translation_mode: bool = False
    ) -> None:
        """
        Args:
            name (str): The name of displayed list.
            strings (Strings): The list of strings to display.
            translation_mode (bool, optional):
                If the strings belong to a translation. Defaults to False.
        """

        super().__init__(strings, translation_mode)

        self.setMinimumSize(1400, 800)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowTitle(
            name
            + self.tr(
                " (%n string)",
                " (%n strings)",
                self.get_visible_item_count(),
            )
        )
