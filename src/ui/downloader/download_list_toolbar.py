"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar

from ui.utilities.icon_provider import IconProvider


class DownloadListToolBar(QToolBar):
    """
    Toolbar for the download list widget.
    """

    filter_toggled = Signal(bool)
    """
    Signal emitted when the user toggles the filter for items with just one option.

    Args:
        filter (bool): True if the filter is enabled, False otherwise.
    """

    import_requested = Signal()
    """Signal emitted when the user clicks on the import download list action."""

    export_requested = Signal()
    """Signal emitted when the user clicks on the export download list action."""

    __filter_action: QAction

    __import_action: QAction
    __export_action: QAction

    @override
    def __init__(self) -> None:
        super().__init__()

        self.setFloatable(False)

        self.__init_ui()

        self.__filter_action.triggered.connect(
            lambda: self.filter_toggled.emit(self.__filter_action.isChecked())
        )
        self.__import_action.triggered.connect(self.import_requested.emit)
        self.__export_action.triggered.connect(self.export_requested.emit)

    def __init_ui(self) -> None:
        self.__init_download_list_actions()

        self.addSeparator()

        self.__init_filter_action()

    def __init_filter_action(self) -> None:
        self.__filter_action = self.addAction(
            self.tr("Filter items without selection options")
        )
        IconProvider.bind_qta_icon(
            self.__filter_action, self.__filter_action.setIcon, "mdi6.filter"
        )
        self.__filter_action.setCheckable(True)

    def __init_download_list_actions(self) -> None:
        self.__import_action = self.addAction(self.tr("Import download list..."))
        IconProvider.bind_qta_icon(
            self.__import_action, self.__import_action.setIcon, "mdi6.import"
        )

        self.__export_action = self.addAction(self.tr("Export download list..."))
        IconProvider.bind_qta_icon(
            self.__export_action, self.__export_action.setIcon, "mdi6.share"
        )
