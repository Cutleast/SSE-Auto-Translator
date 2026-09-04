"""
Copyright (c) Cutleast
"""

from typing import Any, Optional, cast, override

from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.widgets.menu import Menu
from cutleast_core_lib.ui.widgets.menu_checkbox import MenuCheckBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QActionEvent, QResizeEvent
from PySide6.QtWidgets import QCheckBox, QToolBar, QToolButton, QWidget, QWidgetAction

from core.file_types.file_type import FileType
from core.mod_file.translation_status import TranslationStatus
from ui.utilities.icon_provider import IconProvider, ResourceIcon


class MainToolBar(QToolBar):
    """
    Toolbar for main page.
    """

    state_filter_changed = Signal(list)
    """
    Signal emitted when the user changes the checked state filters.

    Args:
        list[TranslationStatus]: List of checked state filters
    """

    type_filter_changed = Signal(list)
    """
    Signal emitted when the user changes the checked type filters.

    Args:
        list[FileType]: List of checked type filters
    """

    ignore_list_requested = Signal()
    """Signal when the user clicks on the ignore list action."""

    modlist_scan_requested = Signal()
    """Signal when the user clicks on the modlist scan action."""

    online_scan_requested = Signal()
    """Signal when the user clicks on the online scan action."""

    download_requested = Signal()
    """Signal when the user clicks on the download action."""

    build_output_requested = Signal()
    """Signal when the user clicks on the build output action."""

    string_search_requested = Signal()
    """Signal when the user clicks on the string search action."""

    export_states_requested = Signal()
    """Signal when the user clicks on the export states action."""

    __filter_action: QAction
    __filter_menu: Menu
    __state_filter_items: dict[TranslationStatus, QCheckBox]
    __type_filter_items: dict[FileType, QCheckBox]

    __main_action_icons: dict[QAction, IconProvider.ThemeIconBinding]
    __modlist_scan_action: QAction
    __online_scan_action: QAction
    __download_action: QAction
    __build_output_action: QAction

    __string_search_action: QAction
    __export_states_action: QAction

    __highlighted_action: Optional[QAction]
    __text_required_width: Optional[int]
    __texts_shown: bool

    TEXT_HYSTERESIS: int = 24

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__highlighted_action = None
        self.__text_required_width = None
        self.__texts_shown = False

        self.setFloatable(False)

        self.__init_actions()
        self.__init_utility_actions()
        self.__init_filter_actions()

        self.__set_action_texts_visible(False)

        self.__highlight_action(self.__modlist_scan_action)

        self.__modlist_scan_action.triggered.connect(self.__on_modlist_scan_requested)
        self.__online_scan_action.triggered.connect(self.__on_online_scan_requested)
        self.__download_action.triggered.connect(self.__on_download_requested)
        self.__build_output_action.triggered.connect(self.__on_build_output_requested)

    def __init_actions(self) -> None:
        self.__main_action_icons = {}

        def get_icon_color(action: QAction) -> IconProvider.Color:
            return (
                IconProvider.Color.Primary
                if action is self.__highlighted_action
                else IconProvider.Color.Text
            )

        self.__modlist_scan_action = self.addAction(self.tr("Scan modlist"))
        self.__modlist_scan_action.setShortcut("Ctrl+Shift+1")
        self.__main_action_icons[self.__modlist_scan_action] = (
            IconProvider.bind_custom_icon(
                self.__modlist_scan_action,
                self.__modlist_scan_action.setIcon,
                lambda: IconProvider.get_res_icon(
                    ResourceIcon.DetectLang,
                    color=get_icon_color(self.__modlist_scan_action),
                    color_active=get_icon_color(self.__modlist_scan_action),
                ),
            )
        )

        self.__online_scan_action = self.addAction(self.tr("Search for translations"))
        self.__online_scan_action.setShortcut("Ctrl+Shift+2")
        self.__main_action_icons[self.__online_scan_action] = (
            IconProvider.bind_custom_icon(
                self.__online_scan_action,
                self.__online_scan_action.setIcon,
                lambda: IconProvider.get_res_icon(
                    ResourceIcon.ScanOnline,
                    color=get_icon_color(self.__online_scan_action),
                    color_active=get_icon_color(self.__online_scan_action),
                ),
            )
        )

        self.__download_action = self.addAction(self.tr("Download translations"))
        self.__download_action.setShortcut("Ctrl+Shift+3")
        self.__main_action_icons[self.__download_action] = IconProvider.bind_custom_icon(
            self.__download_action,
            self.__download_action.setIcon,
            lambda: IconProvider.get_qta_icon(
                "mdi6.download-multiple",
                color=get_icon_color(self.__download_action),
                color_active=get_icon_color(self.__download_action),
            ),
        )

        self.__build_output_action = self.addAction(self.tr("Build output mod"))
        self.__build_output_action.setShortcut("Ctrl+Shift+4")
        self.__main_action_icons[self.__build_output_action] = (
            IconProvider.bind_custom_icon(
                self.__build_output_action,
                self.__build_output_action.setIcon,
                lambda: IconProvider.get_qta_icon(
                    "mdi6.export-variant",
                    color=get_icon_color(self.__build_output_action),
                    color_active=get_icon_color(self.__build_output_action),
                ),
            )
        )

        self.addSeparator()

    def __init_utility_actions(self) -> None:
        self.__string_search_action = self.addAction(
            self.tr("Search modlist for string..."),
        )
        IconProvider.bind_qta_icon(
            self.__string_search_action,
            self.__string_search_action.setIcon,
            "mdi6.layers-search",
        )
        self.__string_search_action.triggered.connect(self.string_search_requested.emit)

        self.__export_states_action = self.addAction(self.tr("Export mod file states"))
        IconProvider.bind_qta_icon(
            self.__export_states_action,
            self.__export_states_action.setIcon,
            "mdi6.share",
        )
        self.__export_states_action.triggered.connect(self.export_states_requested.emit)

        self.addSeparator()

    def __init_filter_actions(self) -> None:
        open_ignore_list_action = self.addAction(self.tr("Open ignore list"))
        IconProvider.bind_qta_icon(
            open_ignore_list_action,
            open_ignore_list_action.setIcon,
            "mdi6.playlist-remove",
        )
        open_ignore_list_action.triggered.connect(self.ignore_list_requested.emit)

        self.__filter_menu = Menu()

        self.__type_filter_items = {}
        for file_type in FileType:
            filter_box = MenuCheckBox(file_type.get_localized_name(), self.__filter_menu)
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(self.__on_type_filter_change)
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__type_filter_items[file_type] = filter_box

        self.__filter_menu.addSeparator()

        self.__state_filter_items = {}
        for status in TranslationStatus:
            filter_box = MenuCheckBox(status.get_localized_name(), self.__filter_menu)
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(self.__on_state_filter_change)
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__state_filter_items[status] = filter_box

        self.__filter_action = self.addAction(self.tr("Filter options"))
        IconProvider.bind_qta_icon(
            self.__filter_action, self.__filter_action.setIcon, "mdi6.filter"
        )
        self.__filter_action.setCheckable(True)
        self.__filter_action.setMenu(self.__filter_menu)
        self.__filter_action.triggered.connect(self.__on_filter_action_triggered)
        self.addAction(self.__filter_action)

    def __on_filter_action_triggered(self) -> None:
        # reverse the checked state
        self.__filter_action.setChecked(not self.__filter_action.isChecked())

        cast(QToolButton, self.widgetForAction(self.__filter_action)).showMenu()

    def __on_filter_change(self, *args: Any) -> None:
        state_filter_active: bool = (
            len(
                {checkbox.isChecked() for checkbox in self.__state_filter_items.values()}
            )
            > 1
        )
        type_filter_active: bool = (
            len({checkbox.isChecked() for checkbox in self.__type_filter_items.values()})
            > 1
        )

        self.__filter_action.setChecked(state_filter_active or type_filter_active)

    def __on_state_filter_change(self, *args: Any) -> None:
        self.__on_filter_change()

        self.state_filter_changed.emit(
            [
                status
                for status, checkbox in self.__state_filter_items.items()
                if checkbox.isChecked()
            ]
        )

    def set_provider_features_enabled(self, enabled: bool) -> None:
        """
        Enables or disables actions that require a translation provider.

        Args:
            enabled (bool): Whether a translation provider is available.
        """

        self.__online_scan_action.setEnabled(enabled)
        self.__download_action.setEnabled(enabled)

    def __on_type_filter_change(self, *args: Any) -> None:
        self.__on_filter_change()

        self.type_filter_changed.emit(
            [
                file_type
                for file_type, checkbox in self.__type_filter_items.items()
                if checkbox.isChecked()
            ]
        )

    def __on_modlist_scan_requested(self) -> None:
        self.modlist_scan_requested.emit()
        self.__highlight_action(self.__online_scan_action)

    def __on_online_scan_requested(self) -> None:
        self.online_scan_requested.emit()
        self.__highlight_action(self.__download_action)

    def __on_download_requested(self) -> None:
        self.download_requested.emit()
        self.__highlight_action(self.__build_output_action)

    def __on_build_output_requested(self) -> None:
        self.build_output_requested.emit()
        self.__highlight_action(None)

    def __highlight_action(self, action: Optional[QAction]) -> None:
        """
        Highlights a toolbar action and unhighlights the others.

        Args:
            action (Optional[QAction]):
                The action to highlight or None if no action should be highlighted.
        """

        self.__highlighted_action = action

        for _action, icon in self.__main_action_icons.items():
            widget: QWidget = self.widgetForAction(_action)
            widget.setProperty("highlighted", _action is action)

            icon.refresh()
            ThemeManager.update_widget_styles(widget)

    def __get_main_buttons(self) -> list[QToolButton]:
        """
        Gets the buttons whose text visibility is changed responsively.

        Returns:
            list[QToolButton]: Primary toolbar action buttons.
        """

        return [
            cast(QToolButton, self.widgetForAction(action))
            for action in (
                self.__modlist_scan_action,
                self.__online_scan_action,
                self.__download_action,
                self.__build_output_action,
            )
        ]

    def __set_action_texts_visible(self, visible: bool) -> None:
        """
        Shows or hides text beside the primary toolbar action icons.

        Args:
            visible (bool): Whether action text should be visible.
        """

        style: Qt.ToolButtonStyle = (
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            if visible
            else Qt.ToolButtonStyle.ToolButtonIconOnly
        )

        for button in self.__get_main_buttons():
            button.setToolButtonStyle(style)

    def __calculate_text_required_width(self) -> int:
        """
        Calculates the toolbar width required while primary action text is visible.

        Returns:
            int: Required width with text beside all primary action icons.
        """

        buttons: list[QToolButton] = self.__get_main_buttons()
        old_styles: list[Qt.ToolButtonStyle] = [
            button.toolButtonStyle() for button in buttons
        ]

        self.__set_action_texts_visible(True)
        self.ensurePolished()

        required_width: int = self.sizeHint().width()

        for button, style in zip(buttons, old_styles, strict=True):
            button.setToolButtonStyle(style)

        return required_width

    @override
    def actionEvent(self, event: QActionEvent, /) -> None:
        super().actionEvent(event)

        self.__text_required_width = None

    @override
    def resizeEvent(self, event: QResizeEvent, /) -> None:
        super().resizeEvent(event)

        available_width: int = self.contentsRect().width()
        if self.__text_required_width is None:
            self.__text_required_width = self.__calculate_text_required_width()

        if self.__texts_shown:
            show_text: bool = available_width >= (
                self.__text_required_width - MainToolBar.TEXT_HYSTERESIS
            )
        else:
            show_text = available_width >= (
                self.__text_required_width + MainToolBar.TEXT_HYSTERESIS
            )

        if show_text != self.__texts_shown:
            self.__set_action_texts_visible(show_text)
            self.__texts_shown = show_text

    def set_shortcut_target(self, target: QWidget) -> None:
        """
        Sets the target widget for the toolbar action shortcuts.

        Args:
            target (QWidget): Widget to receive shortcut events.
        """

        self.__modlist_scan_action.setShortcutContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        target.addAction(self.__modlist_scan_action)

        self.__online_scan_action.setShortcutContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        target.addAction(self.__online_scan_action)

        self.__download_action.setShortcutContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        target.addAction(self.__download_action)

        self.__build_output_action.setShortcutContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        target.addAction(self.__build_output_action)
