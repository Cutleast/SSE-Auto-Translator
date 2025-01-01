"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar


class DownloadsToolbar(QToolBar):
    """
    Toolbar for downloads tab.
    """

    __parent: "DownloadsTab"

    handle_nxm_action: QAction
    toggle_pause_action: QAction

    def __init__(self, parent: "DownloadsTab"):
        super().__init__(parent)

        self.__parent = parent

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_actions()

    def __init_actions(self) -> None:
        self.handle_nxm_action = self.addAction(
            qta.icon("fa.chain", color="#ffffff"),
            self.tr("Handle Nexus Mods Downloads") + " " + self.tr("[Experimental]"),
        )
        self.handle_nxm_action.setCheckable(True)
        self.handle_nxm_action.triggered.connect(lambda _: self.__parent.toggle_nxm())

        self.toggle_pause_action = self.addAction(
            qta.icon("fa5s.pause", color=self.palette().text().color()), ""
        )
        self.toggle_pause_action.triggered.connect(self.__parent.toggle_pause)


if __name__ == "__main__":
    from .downloads_tab import DownloadsTab
