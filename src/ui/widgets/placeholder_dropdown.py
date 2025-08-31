"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtWidgets import QComboBox


class PlaceholderDropdown(QComboBox):
    """
    A dropdown with a placeholder item.
    """

    __placeholder_text: str

    def __init__(self, placeholder_text: Optional[str] = None) -> None:
        """
        Args:
            placeholder_text (Optional[str], optional):
                Text of the placeholder item. Defaults to localized "Please select...".
        """

        super().__init__()

        if placeholder_text is None:
            placeholder_text = self.tr("Please select...")

        self.__placeholder_text = placeholder_text

        self.addItem(self.__placeholder_text)

    @override
    def clear(self) -> None:
        super().clear()

        self.addItem(self.__placeholder_text)

    @override
    def currentIndex(self) -> int:
        """
        Returns:
            int: Current non-placeholder index or -1 if placeholder is selected.
        """

        return super().currentIndex() - 1  # subtract 1 to account for placeholder

    @override
    def currentText(self) -> str:
        """
        Returns:
            str: Current non-placeholder text or "" if placeholder is selected.
        """

        cur_text: str = super().currentText()

        if cur_text == self.__placeholder_text:
            return ""

        return cur_text

    @override
    def setCurrentText(self, text: str) -> None:
        """
        Args:
            text (str): Text to set, "" selects placeholder.
        """

        if text == "":
            text = self.__placeholder_text

        super().setCurrentText(text)

    @override
    def setCurrentIndex(self, index: int) -> None:
        """
        Args:
            index (int): Non-placeholder index or -1 to select placeholder.
        """

        return super().setCurrentIndex(index + 1)  # add 1 to account for placeholder

    @override
    def itemText(self, index: int) -> str:
        """
        Args:
            index (int): Non-placeholder index.

        Returns:
            str: Non-placeholder text.
        """

        return super().itemText(index + 1)  # add 1 to account for placeholder

    @override
    def count(self) -> int:
        """
        Returns:
            int: Number of non-placeholder items.
        """

        return super().count() - 1  # subtract 1 to account for placeholder
