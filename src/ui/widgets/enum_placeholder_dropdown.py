"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Generic, Optional, TypeVar

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtCore import Qt, Signal

from ui.widgets.placeholder_dropdown import PlaceholderDropdown

E = TypeVar("E", bound="Enum")


class EnumPlaceholderDropdown(PlaceholderDropdown, Generic[E]):
    """
    PlaceholderDropdown specialized for enums. Has support for localized enums.
    """

    currentValueChanged = Signal(Enum)
    """
    This signal gets emitted when the selected enum value changes.

    Args:
        Optional[E]: The selected enum value or None
    """

    __enum_type: type[E]

    def __init__(
        self,
        enum_type: type[E],
        initial_value: Optional[E] = None,
        placeholder_text: Optional[str] = None,
    ) -> None:
        """
        Args:
            enum_type (type[E]): The enum type.
            initial_value (Optional[E], optional): The initial enum value. Defaults to None.
            placeholder_text (Optional[str], optional): The placeholder text. Defaults to None.
        """

        super().__init__(placeholder_text=placeholder_text)

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
            self.setCurrentIndex(-1)

        self.currentTextChanged.connect(
            lambda _: self.currentValueChanged.emit(self.getCurrentValue())
        )

    def getCurrentValue(self) -> Optional[E]:
        """
        Returns:
            Optional[E]:
                The currently selected enum member or None if placeholder is selected.
        """

        if self.currentIndex() == -1:
            return None
        elif issubclass(self.__enum_type, LocalizedEnum):
            return self.__enum_type.get_by_localized_name(self.currentText())
        else:
            return self.__enum_type[self.currentText()]

    def setCurrentValue(self, value: Optional[E]) -> None:
        """
        Sets the specified enum value as the currently selected.

        Args:
            value (Optional[E]): Enum value to select
        """

        if isinstance(value, LocalizedEnum):
            self.setCurrentText(value.get_localized_name())
        elif value is not None:
            self.setCurrentText(value.name)
        else:
            self.setCurrentIndex(-1)
