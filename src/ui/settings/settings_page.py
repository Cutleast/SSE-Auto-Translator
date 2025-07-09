"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Any, Generic, TypeVar, override

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QSpinBox

from core.config._base_config import BaseConfig
from ui.widgets.smooth_scroll_area import SmoothScrollArea

T = TypeVar("T", bound=BaseConfig)


class SettingsPage(SmoothScrollArea, Generic[T]):
    """
    Base class for settings pages.
    """

    changed_signal = Signal()
    """This signal gets emitted when a setting is changed."""

    restart_required_signal = Signal()
    """This signal gets emitted when a setting requires a restart."""

    _initial_config: T

    def __init__(self, initial_config: T) -> None:
        super().__init__()

        self._initial_config = initial_config

        self.setObjectName("transparent")

        self._init_ui()

    @abstractmethod
    def _init_ui(self) -> None: ...

    @abstractmethod
    def apply(self, config: T) -> None:
        """
        Applies changes to the config.

        Args:
            config (T): Config to apply changes to
        """

    def _on_change(self, *args: Any) -> None:
        """
        Safe method to emit `changed_signal`.
        """

        self.changed_signal.emit()

    def _on_restart_required(self, *args: Any) -> None:
        """
        Safe method to emit `restart_required_signal`.
        """

        self.restart_required_signal.emit()

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and (
                isinstance(source, QComboBox)
                or isinstance(source, QSpinBox)
                or isinstance(source, QDoubleSpinBox)
            )
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
