"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Any, Optional

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class Page(QWidget):
    """
    Base class for startup dialog pages.
    """

    next_signal = Signal()
    """
    Signal to emit when the user clicks the "Next" button.
    """

    prev_signal = Signal()
    """
    Signal to emit when the user clicks the "Back" button.
    """

    valid_signal = Signal(bool)
    """
    Signal to toggle the "Next" button.
    """

    _vlayout: QVBoxLayout
    _back_button: QPushButton
    _next_button: QPushButton

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setObjectName("primary")
        self.__init_ui()

    def __init_ui(self) -> None:
        self._vlayout = QVBoxLayout()
        self.setLayout(self._vlayout)

        self.__init_header()
        self._init_form()
        self.__init_footer()

    def __init_header(self) -> None:
        title_label = QLabel(self._get_title())
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("title_label")
        self._vlayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self._vlayout.addSpacing(25)

        help_label = QLabel(self._get_description())
        help_label.setWordWrap(True)
        self._vlayout.addWidget(help_label)

        self._vlayout.addSpacing(25)

    @abstractmethod
    def _init_form(self) -> None: ...

    @abstractmethod
    def _get_title(self) -> str: ...

    @abstractmethod
    def _get_description(self) -> str: ...

    def __init_footer(self) -> None:
        self._vlayout.addStretch()
        hlayout = QHBoxLayout()
        self._vlayout.addLayout(hlayout)

        self._back_button = QPushButton(self.tr("Back"))
        self._back_button.setIcon(qta.icon("fa5s.chevron-left", color="#ffffff"))
        self._back_button.clicked.connect(self.prev_signal)
        hlayout.addWidget(self._back_button, 0, Qt.AlignmentFlag.AlignLeft)

        hlayout.addStretch()

        self._next_button = QPushButton(self.tr("Next"))
        self._next_button.setIcon(qta.icon("fa5s.chevron-right", color="#ffffff"))
        self._next_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._next_button.clicked.connect(self.next_signal)
        hlayout.addWidget(self._next_button)

        self._next_button.setDisabled(True)
        self.valid_signal.connect(self._next_button.setEnabled)

    @abstractmethod
    def _validate(self) -> None: ...

    @abstractmethod
    def get_values(self) -> Any:
        """
        Get the values from the page.

        Returns:
            Any: The values from the page.
        """
