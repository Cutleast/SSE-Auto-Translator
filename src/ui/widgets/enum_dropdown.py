"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Generic, Optional, TypeVar

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox

from core.utilities.localized_enum import LocalizedEnum

E = TypeVar("E", bound="Enum")


class EnumDropdown(QComboBox, Generic[E]):
    """
    QComboBox specialized for enums. Has support for localized enums.
    """

    currentValueChanged = Signal(Enum)
    """
    This signal gets emitted when the selected enum value changes.

    Args:
        E: The selected enum value
    """

    __enum_type: type[E]

    def __init__(self, enum_type: type[E], initial_value: Optional[E] = None) -> None:
        super().__init__()

        self.__enum_type = enum_type

        if issubclass(enum_type, LocalizedEnum):
            for i, e in enumerate(enum_type):
                self.addItem(e.get_localized_name())
                self.setItemData(
                    i, e.get_localized_description(), role=Qt.ItemDataRole.ToolTipRole
                )

        else:
            for e in enum_type:
                self.addItem(e.name)

        if initial_value is not None:
            if isinstance(initial_value, LocalizedEnum):
                self.setCurrentText(initial_value.get_localized_name())
            else:
                self.setCurrentText(initial_value.name)
        else:
            self.setCurrentIndex(0)

        self.currentTextChanged.connect(
            lambda _: self.currentValueChanged.emit(self.getCurrentValue())
        )

    def getCurrentValue(self) -> E:
        """
        Returns:
            E: The currently selected enum member.
        """

        if issubclass(self.__enum_type, LocalizedEnum):
            return self.__enum_type.get_by_localized_name(self.currentText())
        else:
            return self.__enum_type[self.currentText()]

    def setCurrentValue(self, value: E) -> None:
        """
        Sets the specified enum value as the currently selected.

        Args:
            value (E): Enum value to select
        """

        if isinstance(value, LocalizedEnum):
            self.setCurrentText(value.get_localized_name())
        else:
            self.setCurrentText(value.name)
