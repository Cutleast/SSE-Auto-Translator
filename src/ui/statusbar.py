"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.ui.widgets.log_window import LogWindow
from PySide6.QtCore import QSize, Qt, QTimerEvent, Signal
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QStatusBar

from core.translation_provider.provider import Provider
from core.utilities import trim_string
from ui.utilities.icon_provider import IconProvider


class StatusBar(QStatusBar):
    """
    Status bar for main window.
    """

    log_signal = Signal(str)
    __logger: Logger
    __provider: Provider

    status_label: QLabel
    api_label: QLabel

    __log_window: Optional[LogWindow] = None

    def __init__(self, provider: Provider) -> None:
        super().__init__()

        self.__logger = Logger.get()
        self.__logger.set_callback(self.log_signal.emit)

        self.__provider = provider

        self.__init_ui()
        self.startTimer(1000, Qt.TimerType.PreciseTimer)

    def __init_ui(self) -> None:
        self.status_label = QLabel()
        self.status_label.setObjectName("protocol")
        self.status_label.setTextFormat(Qt.TextFormat.PlainText)
        self.log_signal.connect(
            lambda text: self.status_label.setText(
                trim_string(text.removesuffix("\n"), max_length=200)
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        self.insertPermanentWidget(0, self.status_label, stretch=1)

        self.api_label = QLabel()
        self.api_label.setToolTip(
            self.tr(
                "The hourly limit only applies if the daily limit has been used up."
            )
        )
        self.addPermanentWidget(self.api_label)

        copy_log_button = QPushButton()
        copy_log_button.setFixedSize(20, 20)
        copy_log_button.setIcon(IconProvider.get_qta_icon("mdi6.content-copy"))
        copy_log_button.setIconSize(QSize(16, 16))
        copy_log_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.__logger.get_content())
        )
        copy_log_button.setToolTip(self.tr("Copy log to clipboard"))
        self.addPermanentWidget(copy_log_button)

        open_log_button = QPushButton()
        open_log_button.setFixedSize(20, 20)
        open_log_button.setIcon(IconProvider.get_qta_icon("fa5s.external-link-alt"))
        open_log_button.setIconSize(QSize(16, 16))
        open_log_button.setToolTip(self.tr("View log"))
        open_log_button.clicked.connect(self.__open_log_window)
        self.addPermanentWidget(open_log_button)

    def __open_log_window(self) -> None:
        self.__log_window = LogWindow(self.__logger.get_content())
        self.log_signal.connect(
            self.__log_window.addMessage, Qt.ConnectionType.QueuedConnection
        )
        self.__log_window.show()

    @override
    def timerEvent(self, event: QTimerEvent) -> None:
        super().timerEvent(event)

        self.update()

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates status labels and API limit label.
        """

        rem_hreq, rem_dreq = self.__provider.get_remaining_requests()

        self.api_label.setText(
            self.tr("API: Hourly: {0} | Daily: {1}").format(rem_hreq, rem_dreq)
        )

        # Set text color according to remaining API requests
        if rem_hreq < 50 and rem_dreq == 0:
            self.api_label.setObjectName("critical_label")
        elif rem_hreq < 100 and rem_dreq == 0:
            self.api_label.setObjectName("warning_label")
        else:
            self.api_label.setObjectName("label")

        self.api_label.setStyleSheet(self.styleSheet())
        self.api_label.setVisible(rem_hreq != -1 and rem_dreq != -1)
