"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar


class DownloadsToolbar(QToolBar):
    """
    Toolbar for downloads tab.
    """

    toggle_nxm_requested = Signal(bool)
    """
    Signal emitted when the user clicks on the handle NXM action.
    
    Args:
        bool: The new checked state of the action.
    """

    toggle_pause_requested = Signal()
    """Signal emitted when the user clicks on the toggle pause action."""

    __handle_nxm_action: QAction
    __toggle_pause_action: QAction

    def __init__(self):
        super().__init__()

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_actions()

    def __init_actions(self) -> None:
        self.__handle_nxm_action = self.addAction(
            qta.icon("fa.chain", color="#ffffff"),
            self.tr("Handle Nexus Mods Downloads") + " " + self.tr("[Experimental]"),
        )
        self.__handle_nxm_action.setCheckable(True)
        self.__handle_nxm_action.triggered.connect(
            lambda: self.toggle_nxm_requested.emit(self.__handle_nxm_action.isChecked())
        )

        self.__toggle_pause_action = self.addAction(
            qta.icon("fa5s.pause", color=self.palette().text().color()), ""
        )
        self.__toggle_pause_action.triggered.connect(self.toggle_pause_requested.emit)

    def set_handle_nxm_action_checked(self, checked: bool) -> None:
        """
        Sets the checked state of the handle NXM action.

        Args:
            checked (bool): Whether the action should be checked.
        """

        self.__handle_nxm_action.setChecked(checked)

    def highlight_nxm_action(self) -> None:
        """
        Highlights the handle NXM action.
        """

        self.widgetForAction(self.__handle_nxm_action).setObjectName("accent_button")
        self.setStyleSheet(self.styleSheet())

    def update_toggle_pause_action(self, paused: bool) -> None:
        """
        Updates the toggle pause action.

        Args:
            paused (bool): Whether the downloads are paused.
        """

        if paused:
            self.__toggle_pause_action.setText(self.tr("Resume"))
            self.__toggle_pause_action.setIcon(
                qta.icon("fa5s.play", color=self.palette().text().color())
            )
        else:
            self.__toggle_pause_action.setText(self.tr("Pause"))
            self.__toggle_pause_action.setIcon(
                qta.icon("fa5s.pause", color=self.palette().text().color())
            )
