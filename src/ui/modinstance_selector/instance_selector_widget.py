"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QSpinBox,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from core.mod_managers.instance_info import InstanceInfo
from core.mod_managers.mod_manager import ModManager
from ui.widgets.enum_placeholder_dropdown import EnumPlaceholderDropdown

from . import INSTANCE_WIDGETS
from .base_selector_widget import BaseSelectorWidget


class InstanceSelectorWidget(QWidget):
    """
    Widget for selecting mod instances.
    """

    instance_valid = Signal(bool)
    """
    This signal is emitted when the validation status of the selected instance changes.
    """

    changed = Signal()
    """
    This signal is emitted everytime the user changes something at the selection.
    """

    __cur_instance_data: Optional[InstanceInfo] = None
    """
    Currently selected instance data.
    """

    __cur_mod_manager: Optional[ModManager] = None
    """
    Currently selected mod manager.
    """

    __mod_managers: dict[ModManager, BaseSelectorWidget]
    """
    Maps mod managers to their corresponding instance widgets.
    """

    __vlayout: QVBoxLayout
    __mod_manager_dropdown: EnumPlaceholderDropdown[ModManager]
    __instance_stack_layout: QStackedLayout
    __placeholder_widget: QWidget

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        self.__mod_manager_dropdown.currentValueChanged.connect(
            self.__set_cur_mod_manager
        )

    def __init_ui(self) -> None:
        self.setObjectName("transparent")

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_instance_widgets()

    def __init_header(self) -> None:
        glayout = QGridLayout()
        glayout.setContentsMargins(0, 0, 0, 0)
        glayout.setColumnStretch(0, 1)
        glayout.setColumnStretch(1, 3)
        self.__vlayout.addLayout(glayout)

        mod_manager_label = QLabel(self.tr("Mod Manager:"))
        glayout.addWidget(mod_manager_label, 1, 0)

        self.__mod_manager_dropdown = EnumPlaceholderDropdown(ModManager)
        self.__mod_manager_dropdown.installEventFilter(self)
        glayout.addWidget(self.__mod_manager_dropdown, 1, 1)

    def __init_instance_widgets(self) -> None:
        self.__instance_stack_layout = QStackedLayout()
        self.__instance_stack_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__placeholder_widget = QWidget()
        self.__instance_stack_layout.addWidget(self.__placeholder_widget)
        self.__vlayout.addLayout(self.__instance_stack_layout)

        self.__mod_managers = {}

        for instance_widget_type in INSTANCE_WIDGETS:
            mod_manager: ModManager = instance_widget_type.get_mod_manager()
            instance_widget: BaseSelectorWidget = instance_widget_type()

            instance_widget.changed.connect(self.changed.emit)
            instance_widget.valid.connect(self.__on_valid)

            self.__instance_stack_layout.addWidget(instance_widget)
            self.__mod_managers[mod_manager] = instance_widget

    def __set_cur_mod_manager(self, mod_manager: Optional[ModManager]) -> None:
        if mod_manager is not None:
            instance_widget: BaseSelectorWidget = self.__mod_managers[mod_manager]
            instance_widget.set_instances(mod_manager.get_api().get_instance_names())
            self.__instance_stack_layout.setCurrentWidget(instance_widget)
            self.__on_valid(instance_widget.validate())
        else:
            self.__instance_stack_layout.setCurrentWidget(self.__placeholder_widget)
            self.__on_valid(False)

        self.__cur_mod_manager = mod_manager
        self.changed.emit()

    def __on_valid(self, valid: bool) -> None:
        if valid and self.__cur_mod_manager is not None:
            instance_widget: BaseSelectorWidget = self.__mod_managers[
                self.__cur_mod_manager
            ]
            self.__cur_instance_data = instance_widget.get_instance()
        else:
            self.__cur_instance_data = None

        self.instance_valid.emit(self.__cur_instance_data is not None)

    def validate(self) -> bool:
        """
        Returns whether the currently selected instance data is valid.

        Returns:
            bool: whether the currently selected instance data is valid
        """

        mod_manager: Optional[ModManager] = (
            self.__mod_manager_dropdown.getCurrentValue()
        )
        if mod_manager is None:
            return False

        instance_widget: BaseSelectorWidget = self.__mod_managers[mod_manager]
        return instance_widget.validate()

    def get_cur_instance_data(self) -> Optional[InstanceInfo]:
        """
        Returns the currently selected instance data.

        Returns:
            Optional[InstanceInfo]: The instance data or None if no instance data is selected.
        """

        return self.__cur_instance_data

    def set_cur_instance_data(self, instance_data: Optional[InstanceInfo]) -> None:
        """
        Sets the currently selected instance data.

        Args:
            instance_data (Optional[InstanceInfo]):
                The instance data to select. `None` resets the selection.
        """

        self.__cur_instance_data = instance_data

        if instance_data is not None:
            self.__mod_manager_dropdown.setCurrentValue(instance_data.get_mod_manager())
            widget: BaseSelectorWidget = self.__mod_managers[
                instance_data.get_mod_manager()
            ]
            widget.set_instance(instance_data)
        else:
            self.__cur_mod_manager = None
            for widget in self.__mod_managers.values():
                widget.reset()

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and (isinstance(source, QComboBox) or isinstance(source, QSpinBox))
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
