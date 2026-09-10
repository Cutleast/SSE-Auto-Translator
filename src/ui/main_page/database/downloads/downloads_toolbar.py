"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.theme.manager import ThemeManager
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar, QWidget

from ui.utilities.icon_provider import IconProvider


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

    __paused: bool
    __nxm_highlighted: bool

    __handle_nxm_action: QAction
    __handle_nxm_icon: IconProvider.ThemeIconBinding

    __toggle_pause_action: QAction
    __toggle_pause_icon: IconProvider.ThemeIconBinding

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__paused = False
        self.__nxm_highlighted = False

        self.setIconSize(QSize(24, 24))
        self.setFloatable(False)

        self.__init_actions()

    def __init_actions(self) -> None:
        self.__handle_nxm_action = self.addAction(
            self.tr("Handle Nexus Mods downloads") + " " + self.tr("[Experimental]")
        )
        self.__handle_nxm_icon = IconProvider.bind_custom_icon(
            self.__handle_nxm_action,
            self.__handle_nxm_action.setIcon,
            lambda: IconProvider.get_qta_icon(
                "mdi6.link-variant",
                color=(
                    IconProvider.Color.Primary
                    if self.__nxm_highlighted
                    else IconProvider.Color.Text
                ),
                color_active=(
                    IconProvider.Color.Primary
                    if self.__nxm_highlighted
                    else IconProvider.Color.Text
                ),
            ),
        )
        self.__handle_nxm_action.setCheckable(True)
        self.__handle_nxm_action.triggered.connect(
            lambda: self.toggle_nxm_requested.emit(self.__handle_nxm_action.isChecked())
        )

        self.__toggle_pause_action = self.addAction("")
        self.__toggle_pause_icon = IconProvider.bind_custom_icon(
            self.__toggle_pause_action,
            self.__toggle_pause_action.setIcon,
            self.__get_toggle_pause_icon,
        )
        self.__toggle_pause_action.triggered.connect(self.toggle_pause_requested.emit)

    def __get_toggle_pause_icon(self) -> QIcon:
        if self.__paused:
            return IconProvider.get_qta_icon("mdi6.play")
        else:
            return IconProvider.get_qta_icon("mdi6.pause")

    def set_handle_nxm_action_checked(self, checked: bool) -> None:
        """
        Sets the checked state of the handle NXM action.

        Args:
            checked (bool): Whether the action should be checked.
        """

        self.__handle_nxm_action.setChecked(checked)

    def set_handle_nxm_action_enabled(self, enabled: bool) -> None:
        """
        Enables or disables Nexus Mods download handling.

        Args:
            enabled (bool): Whether a translation provider is available.
        """

        self.__handle_nxm_action.setEnabled(enabled)

    def highlight_nxm_action(self) -> None:
        """
        Highlights the handle NXM action.
        """

        self.__nxm_highlighted = True
        widget: QWidget = self.widgetForAction(self.__handle_nxm_action)
        widget.setProperty("highlighted", self.__nxm_highlighted)

        self.__handle_nxm_icon.refresh()
        ThemeManager.update_widget_styles(widget)

    def set_paused(self, paused: bool) -> None:
        """
        Args:
            paused (bool): Whether the downloads are paused.
        """

        self.__paused = paused
        self.__toggle_pause_icon.refresh()

        if paused:
            self.__toggle_pause_action.setText(self.tr("Resume"))
        else:
            self.__toggle_pause_action.setText(self.tr("Pause"))
