"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.ui.utilities.tree_widget import calculate_required_width
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from core.config.app_config import AppConfig
from core.database.translation import Translation
from core.translator_api.translator import Translator
from core.user_data.user_data import UserData
from ui.utilities.icon_provider import IconProvider
from ui.utilities.theme_manager import ThemeManager

from .editor.editor_tab import EditorTab


class EditorPage(QSplitter):
    """
    Page for translation editor.
    """

    tab_count_updated = Signal(int)
    """
    Signal emitted everytime one or more tabs are opened or closed.

    Args:
        int: New number of open tabs.
    """

    app_config: AppConfig
    user_data: UserData
    translator: Translator

    __tabs: dict[Translation, tuple[EditorTab, QTreeWidgetItem]] = {}
    """
    Mapping of translations to their tabs and the respective item in the list.
    """

    __tab_list_widget: QTreeWidget
    __page_widget: QStackedWidget

    def __init__(
        self,
        app_config: AppConfig,
        user_data: UserData,
        translator: Translator,
    ) -> None:
        super().__init__()

        self.app_config = app_config
        self.user_data = user_data
        self.translator = translator

        self.setOrientation(Qt.Orientation.Horizontal)
        self.__init_ui()

    def __init_ui(self) -> None:
        self.__tab_list_widget = QTreeWidget()
        self.__tab_list_widget.header().hide()
        self.__tab_list_widget.setColumnCount(2)
        self.__tab_list_widget.header().setStretchLastSection(False)
        self.__tab_list_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.__tab_list_widget.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.addWidget(self.__tab_list_widget)

        self.__page_widget = QStackedWidget()
        self.addWidget(self.__page_widget)

        self.__tab_list_widget.currentItemChanged.connect(
            lambda cur, _: self.__set_tab_from_item(cur)
        )

    def __set_tab_from_item(self, item: Optional[QTreeWidgetItem]) -> None:
        """
        Sets page according to selected `item`.
        """

        if item is None:
            return

        tabs: dict[QTreeWidgetItem, EditorTab] = {
            item: tab for tab, item in self.__tabs.values()
        }

        # Check if item is a top level item
        tab: EditorTab
        if item.parent() is None:  # type: ignore
            tab = tabs[item]
        else:
            tab = tabs[item.parent()]
            tab.go_to_modfile(Path(item.text(0)))

        self.__page_widget.setCurrentWidget(tab)

    def __set_tab(self, tab: EditorTab, modfile: Optional[Path] = None) -> None:
        """
        Switches to a specified tab and goes to a specified mod file, if any.

        Args:
            tab (EditorTab): The tab to switch to.
            modfile (Optional[Path]):
                The path of the mod file to go to, relative to the game's "Data" folder.
        """

        item: QTreeWidgetItem = self.__tabs[tab.translation][1]
        self.__tab_list_widget.setCurrentItem(item)

        if modfile is not None:
            tab.go_to_modfile(modfile)

    @property
    def tabs(self) -> list[EditorTab]:
        """
        List of all open editor tabs.
        """

        return [tab for tab, _ in self.__tabs.values()]

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates the displayed editor tabs.
        """

        for tab, item in self.__tabs.values():
            tab.update()

            if tab.changes_pending and not item.text(0).endswith("*"):
                item.setText(0, item.text(0) + "*")
            else:
                item.setText(0, item.text(0).removesuffix("*"))

    def close_translation(self, translation: Translation, silent: bool = False) -> None:
        """
        Closes all tabs belonging to `translation`.
        """

        tab: EditorTab
        item: QTreeWidgetItem
        tab, item = self.__tabs[translation]

        if tab.changes_pending and not silent:
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("Close"))
            message_box.setText(
                self.tr("Are you sure you want to close? All changes will be lost!")
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))

            # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
            message_box.setStyleSheet(ThemeManager.get_stylesheet() or "")

            if message_box.exec() != QMessageBox.StandardButton.Yes:
                return

        self.__tabs.pop(translation)

        self.__tab_list_widget.takeTopLevelItem(
            self.__tab_list_widget.invisibleRootItem().indexOfChild(item)
        )

        if self.tabs:
            self.__set_tab(self.tabs[-1])

        self.tab_count_updated.emit(len(self.tabs))
        self.update()

    def open_translation(self, translation: Translation) -> None:
        """
        Opens `translation` in new tab.
        """

        # Create new tab if translation is not already open
        if translation not in self.__tabs:
            translation_item = QTreeWidgetItem([translation.name])

            translation_tab = EditorTab(
                translation, self.app_config, self.user_data, self.translator
            )
            translation_tab.close_signal.connect(self.close_translation)
            self.__tabs[translation] = translation_tab, translation_item
            self.__page_widget.addWidget(translation_tab)

            close_button = QPushButton()
            close_button.setObjectName("list_close_button")
            close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            close_button.setIcon(IconProvider.get_qta_icon("mdi6.close-thick"))
            close_button.setFixedSize(26, 26)

            for modfile in sorted(translation.strings, key=lambda m: m.name.lower()):
                modfile_item = QTreeWidgetItem([str(modfile)])
                translation_item.addChild(modfile_item)

            self.__tab_list_widget.addTopLevelItem(translation_item)

            self.__tab_list_widget.setItemWidget(translation_item, 1, close_button)
            close_button.clicked.connect(lambda: self.close_translation(translation))

            translation_item.setExpanded(True)

        self.__tab_list_widget.resizeColumnToContents(1)

        # Switch to Tab
        self.__set_tab(self.tabs[-1])

        # Resize tab list to fit all translation and mod file names
        new_width: int = calculate_required_width(self.__tab_list_widget, 0)
        new_width += 100  # for the indentation and second column
        parent: Optional[QWidget] = self.parentWidget()
        total_width: int = parent.width() if parent else self.width()
        self.setSizes([new_width, total_width - new_width])

        self.tab_count_updated.emit(len(self.tabs))
        self.update()
