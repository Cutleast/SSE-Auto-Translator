"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import QSize, Signal
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

    def __init__(self) -> None:
        super().__init__()

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_filter_action()

        self.addSeparator()

        self.__init_download_list_actions()

    def __init_filter_action(self) -> None:
        self.__filter_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.filter"),
            self.tr("Filter items without selection options"),
        )
        self.__filter_action.setCheckable(True)
        self.__filter_action.triggered.connect(
            lambda: self.filter_toggled.emit(self.__filter_action.isChecked())
        )

    def __init_download_list_actions(self) -> None:
        self.__import_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.import"), self.tr("Import download list...")
        )
        self.__import_action.triggered.connect(self.import_requested.emit)

        self.__export_action = self.addAction(
            IconProvider.get_qta_icon("fa5s.share"), self.tr("Export download list...")
        )
        self.__export_action.triggered.connect(self.export_requested.emit)
