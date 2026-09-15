"""
Copyright (c) Cutleast
"""

from typing import Optional, cast, override

from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from cutleast_core_lib.ui.widgets.copy_button import CopyButton
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel
from cutleast_core_lib.ui.widgets.icon_button import IconButton
from cutleast_core_lib.ui.widgets.log_window import LogWindow
from PySide6.QtCore import Qt, QTimerEvent, Signal
from PySide6.QtWidgets import QApplication, QLabel, QStatusBar

from core.translation_provider.provider import TranslationProvider
from ui.utilities.icon_provider import IconProvider


class StatusBar(QStatusBar):
    """
    Status bar for main window.
    """

    __log_signal = Signal(str)

    __logger: Logger
    __provider: TranslationProvider

    __status_label: QLabel
    __api_label: QLabel

    __log_window: Optional[LogWindow] = None

    def __init__(self, provider: TranslationProvider) -> None:
        """
        Args:
            provider (TranslationProvider): The translation provider.
        """

        super().__init__()

        self.__logger = Logger.get()
        self.__logger.set_callback(self.__log_signal.emit)

        self.__provider = provider

        self.__init_ui()
        self.__api_label.setVisible(self.__provider.is_available)
        self.startTimer(1000, Qt.TimerType.PreciseTimer)

    def __init_ui(self) -> None:
        self.setSizeGripEnabled(False)

        self.__status_label = ElidedLabel()
        self.__status_label.setProperty("monospace", True)
        self.__status_label.setTextFormat(Qt.TextFormat.PlainText)
        self.__log_signal.connect(
            lambda text: self.__status_label.setText(cast(str, text).splitlines()[0]),
            Qt.ConnectionType.QueuedConnection,
        )
        self.insertPermanentWidget(0, self.__status_label, stretch=1)

        self.__api_label = QLabel()
        self.__api_label.setObjectName("api_label")
        self.__api_label.setToolTip(
            self.tr("The hourly limit only applies if the daily limit has been used up.")
        )
        self.addPermanentWidget(self.__api_label)

        copy_log_button = CopyButton()
        copy_log_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.__logger.get_content())
        )
        copy_log_button.setToolTip(self.tr("Copy log to clipboard"))
        self.addPermanentWidget(copy_log_button)

        open_log_button = IconButton()
        IconProvider.bind_qta_icon(
            open_log_button, open_log_button.setIcon, "mdi6.open-in-new"
        )
        open_log_button.setToolTip(self.tr("View log"))
        open_log_button.clicked.connect(self.__open_log_window)
        self.addPermanentWidget(open_log_button)

    def __open_log_window(self) -> None:
        if self.__log_window is None:
            self.__log_window = LogWindow(self.__logger.get_content())
            self.__log_signal.connect(
                self.__log_window.addMessage, Qt.ConnectionType.QueuedConnection
            )

        WindowManager.get().show(self.__log_window, delete_on_close=False)

    def close_log_window(self) -> None:
        """
        Closes the log window if it is open.
        """

        if self.__log_window is not None:
            self.__log_window.close()
            self.__log_window = None

    @override
    def timerEvent(self, event: QTimerEvent) -> None:
        super().timerEvent(event)

        self.__update()

    def __update(self) -> None:
        """
        Updates status labels and API limit label.
        """

        try:
            rem_hreq, rem_dreq = self.__provider.get_remaining_requests()
        except ValueError:
            self.__api_label.setVisible(False)
            return

        self.__api_label.setText(
            self.tr("API: Hourly: {0} | Daily: {1}").format(rem_hreq, rem_dreq)
        )

        # Set text color according to remaining API requests
        if rem_hreq < 50 and rem_dreq == 0:
            self.__api_label.setProperty("state", "error")
        elif rem_hreq < 100 and rem_dreq == 0:
            self.__api_label.setProperty("state", "warning")
        else:
            self.__api_label.setProperty("state", "")

        ThemeManager.update_widget_styles(self.__api_label)
        self.__api_label.setVisible(rem_hreq != -1 and rem_dreq != -1)
