"""
Copyright (c) Cutleast
"""

from threading import Event
from typing import override

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.exceptions import (
    TaskCancelledError,
    format_exception,
)
from cutleast_core_lib.ui.progress.widget import ProgressWidget
from cutleast_core_lib.ui.widgets.copy_button import CopyButton
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ui.utilities.icon_provider import IconProvider


class DownloadItemWidget(QWidget):
    """
    Combo-widget for displaying the progress and state of a download item.
    Also has buttons for canceling and removing a download item.
    """

    download_requested = Signal()
    """Signal emitted when the download button is clicked."""

    copy_requested = Signal()
    """Signal emitted when the copy button is clicked."""

    remove_requested = Signal()
    """Signal emitted when the remove button is clicked."""

    __cancel_event: Event

    __hlayout: QHBoxLayout

    __progress_widget: ProgressWidget
    __cancel_button: QPushButton

    __download_button: QPushButton

    __status_label: ElidedLabel
    __copy_button: CopyButton
    __remove_button: QPushButton

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__cancel_event = Event()

        self.__init_ui()

        self.__cancel_button.clicked.connect(self.__cancel_event.set)
        self.__download_button.clicked.connect(self.download_requested.emit)
        self.__copy_button.clicked.connect(self.copy_requested.emit)
        self.__remove_button.clicked.connect(self.remove_requested.emit)

        self.set_pending()

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)

        self.__hlayout = QHBoxLayout()
        self.__hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__hlayout)

        self.__progress_widget = ProgressWidget()
        self.__hlayout.addWidget(self.__progress_widget, stretch=1)

        self.__cancel_button = QPushButton()
        self.__cancel_button.setIcon(IconProvider.get_qta_icon("mdi6.cancel"))
        self.__cancel_button.setProperty("transparent", True)
        self.__cancel_button.setToolTip(self.tr("Cancel download"))
        self.__hlayout.addWidget(self.__cancel_button)

        self.__download_button = QPushButton(self.tr("Start download..."))
        self.__download_button.setIcon(IconProvider.get_qta_icon("mdi6.download"))
        self.__download_button.setProperty("transparent", True)
        self.__hlayout.addWidget(self.__download_button)

        self.__status_label = ElidedLabel()
        self.__status_label.setProperty("monospace", True)
        self.__hlayout.addWidget(self.__status_label)

        self.__copy_button = CopyButton()
        self.__copy_button.setProperty("transparent", True)
        self.__hlayout.addWidget(self.__copy_button)

        self.__remove_button = QPushButton()
        self.__remove_button.setIcon(IconProvider.get_qta_icon("mdi6.close"))
        self.__remove_button.setProperty("transparent", True)
        self.__remove_button.setToolTip(self.tr("Remove download"))
        self.__hlayout.addWidget(self.__remove_button)

    def __clear_state(self) -> None:
        for widget in (
            self.__progress_widget,
            self.__cancel_button,
            self.__download_button,
            self.__status_label,
            self.__copy_button,
            self.__remove_button,
        ):
            widget.hide()

    def set_pending(self) -> None:
        """
        Sets the widget to the pending state, which is the initial state of a download
        item.
        """

        self.__clear_state()

        self.__status_label.setText(self.tr("Pending..."))

        self.__status_label.show()
        self.__remove_button.show()

    def set_running(self) -> None:
        """
        Sets the widget to the running state displaying a progress bar and a cancel
        button.
        """

        self.__clear_state()

        self.__progress_widget.show()
        self.__cancel_button.show()

    def set_interaction_required(self) -> None:
        """
        Sets the widget to the interaction required state displaying a download button
        and a copy button.
        """

        self.__clear_state()

        self.__download_button.show()
        self.__copy_button.show()

    def set_failed(self, exception: Exception) -> None:
        """
        Sets the widget to the failed state displaying a copy button and a remove
        button.

        Args:
            exception (Exception): The exception that caused the failure.
        """

        self.__clear_state()

        self.__status_label.setText(str(exception))
        self.__status_label.setToolTip(format_exception(exception, False))

        # turn the status label red to indicate an error
        self.__status_label.setObjectName("critical_label")
        self.__status_label.style().unpolish(self.__status_label)
        self.__status_label.style().polish(self.__status_label)

        self.__status_label.show()
        self.__copy_button.show()
        self.__remove_button.show()

    def update_progress(self, progress_update: ProgressUpdate) -> None:
        """
        Updates the progress bar with the given progress update.

        Args:
            progress_update (ProgressUpdate): The progress update to display.
        """

        if self.__cancel_event.is_set():
            raise TaskCancelledError

        self.__progress_widget.updateMainProgress(progress_update)
