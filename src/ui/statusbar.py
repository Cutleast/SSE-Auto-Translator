"""
Copyright (c) Cutleast
"""

import os
from typing import override

import pyperclip as clipboard
import qtawesome as qta
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QStatusBar

from app_context import AppContext
from core.translation_provider.provider import Provider
from core.utilities import trim_string
from core.utilities.logger import Logger


class StatusBar(QStatusBar):
    """
    Status bar for main window.
    """

    log_signal = Signal(str)
    __logger: Logger

    def __init__(self) -> None:
        super().__init__()

        self.__logger = AppContext.get_app().logger
        self.__logger.set_callback(self.log_signal.emit)

        self.status_label = QLabel()
        self.status_label.setObjectName("status_label")
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
        copy_log_button.setIcon(
            qta.icon("mdi6.content-copy", color=self.palette().text().color())
        )
        copy_log_button.setIconSize(QSize(16, 16))
        copy_log_button.clicked.connect(
            lambda: clipboard.copy(self.__logger.get_content())
        )
        copy_log_button.setToolTip(self.tr("Copy log to clipboard"))
        self.addPermanentWidget(copy_log_button)

        open_log_button = QPushButton()
        open_log_button.setFixedSize(20, 20)
        open_log_button.setIcon(
            qta.icon("fa5s.external-link-alt", color=self.palette().text().color())
        )
        open_log_button.setIconSize(QSize(16, 16))
        open_log_button.setToolTip(self.tr("Open log file"))
        open_log_button.clicked.connect(
            lambda: os.startfile(self.__logger.get_file_path())
        )
        self.addPermanentWidget(open_log_button)

        AppContext.get_app().ready_signal.connect(self.__post_init)

    def __post_init(self) -> None:
        AppContext.get_app().timer_signal.connect(self.update)

    @override
    def update(self) -> None:
        """
        Updates status labels and API limit label.
        """

        provider: Provider = AppContext.get_app().provider
        rem_hreq, rem_dreq = provider.get_remaining_requests()

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
        self.api_label.setVisible(
            provider.preference != Provider.Preference.OnlyConfrerie
        )
