"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtGui import QAction, QCursor, QIcon

from core.mod_instance.mod import Mod
from core.mod_instance.plugin import Plugin
from ui.widgets.menu import Menu


class ModInstanceMenu(Menu):
    """
    Context menu for mod instance widget.
    """

    __parent: "ModInstanceWidget"

    __action_menu: Menu
    """
    Submenu for scan and download actions.
    """

    __translation_menu: Menu
    """
    Submenu for translation-related actions.
    """

    __plugin_menu: Menu
    """
    Submenu for plugin-related actions.
    """

    __uncheck_action: QAction
    __check_action: QAction
    __show_strings_action: QAction
    __import_as_translation_action: QAction

    def __init__(self, parent: "ModInstanceWidget"):
        super().__init__(parent=parent)

        self.__parent = parent

        self.__init_item_actions()
        self.__init_actions_menu()
        self.__init_translation_actions()
        self.__init_plugin_actions()
        self.__init_general_actions()

    def __init_item_actions(self) -> None:
        expand_all_action: QAction = self.addAction(
            qta.icon("mdi6.arrow-expand-vertical", color=self.palette().text().color()),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.__parent.expandAll)

        collapse_all_action: QAction = self.addAction(
            qta.icon(
                "mdi6.arrow-collapse-vertical", color=self.palette().text().color()
            ),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.__parent.collapseAll)

        self.__uncheck_action = self.addAction(self.tr("Uncheck selected plugin(s)"))
        self.__uncheck_action.setIcon(qta.icon("fa.close", color="#ffffff"))
        self.__uncheck_action.triggered.connect(self.__parent.uncheck_selected)

        self.__check_action = self.addAction(self.tr("Check selected plugin(s)"))
        self.__check_action.setIcon(qta.icon("fa.check", color="#ffffff"))
        self.__check_action.triggered.connect(self.__parent.check_selected)

        self.addSeparator()

    def __init_actions_menu(self) -> None:
        self.__action_menu = Menu(
            qta.icon("mdi6.lightning-bolt", color=self.palette().text().color()),
            self.tr("Actions"),
        )
        self.addMenu(self.__action_menu)

        basic_scan_action: QAction = self.__action_menu.addAction(
            QIcon(":/icons/detect_lang.svg"), self.tr("Basic scan...")
        )
        basic_scan_action.triggered.connect(self.__parent.basic_scan)

        online_scan_action: QAction = self.__action_menu.addAction(
            QIcon(":/icons/scan_online.svg"), self.tr("Online scan...")
        )
        online_scan_action.triggered.connect(self.__parent.online_scan)

        download_action: QAction = self.__action_menu.addAction(
            qta.icon("mdi6.download-multiple", color=self.palette().text().color()),
            self.tr("Download available translations..."),
        )
        download_action.triggered.connect(
            self.__parent.download_and_install_translations
        )

        deep_scan_action: QAction = self.__action_menu.addAction(
            qta.icon("mdi6.line-scan", color=self.palette().text().color()),
            self.tr("Deep scan..."),
        )
        deep_scan_action.triggered.connect(self.__parent.deep_scan)

        self.__action_menu.addSeparator()

        self.__import_as_translation_action = self.__action_menu.addAction(
            qta.icon(
                "mdi6.database-import-outline", color=self.palette().text().color()
            ),
            self.tr("Import as translation..."),
        )
        self.__import_as_translation_action.triggered.connect(
            self.__parent.import_as_translation
        )

    def __init_translation_actions(self) -> None:
        self.__translation_menu = Menu(
            qta.icon("mdi6.translate", color=self.palette().text().color()),
            self.tr("Translation"),
        )
        self.addMenu(self.__translation_menu)

        show_untranslated_strings_action: QAction = self.__translation_menu.addAction(
            qta.icon("mdi6.book-alert-outline", color=self.palette().text().color()),
            self.tr("Show untranslated strings..."),
        )
        show_untranslated_strings_action.triggered.connect(
            self.__parent.show_untranslated_strings
        )

        show_translation_action: QAction = self.__translation_menu.addAction(
            qta.icon("mdi6.translate", color=self.palette().text().color()),
            self.tr("Show translation..."),
        )
        show_translation_action.triggered.connect(self.__parent.show_translation)

        show_translation_strings_action: QAction = self.__translation_menu.addAction(
            qta.icon("mdi6.book-open-outline", color=self.palette().text().color()),
            self.tr("Show translation strings..."),
        )
        show_translation_strings_action.triggered.connect(
            self.__parent.show_translation_strings
        )

        edit_translation_action: QAction = self.__translation_menu.addAction(
            qta.icon("mdi6.text-box-edit", color=self.palette().text().color()),
            self.tr("Edit translation..."),
        )
        edit_translation_action.triggered.connect(self.__parent.edit_translation)

        self.addSeparator()

    def __init_plugin_actions(self) -> None:
        self.__plugin_menu = Menu(QIcon(":/icons/plugin.svg"), self.tr("Plugins"))
        self.addMenu(self.__plugin_menu)

        create_translation_action: QAction = self.__plugin_menu.addAction(
            qta.icon("mdi6.passport-plus", color=self.palette().text().color()),
            self.tr("Create new translation..."),
        )
        create_translation_action.triggered.connect(self.__parent.create_translation)

        show_structure_action: QAction = self.__plugin_menu.addAction(
            qta.icon("ph.tree-structure", color=self.palette().text().color()),
            self.tr("Show Plugin Structure... (Warning: this may take a while)"),
        )
        show_structure_action.triggered.connect(self.__parent.show_structure)

        add_to_ignore_list_action: QAction = self.__plugin_menu.addAction(
            qta.icon("mdi.playlist-remove", color=self.palette().text().color()),
            self.tr("Add plugin to ignore list"),
        )
        add_to_ignore_list_action.triggered.connect(self.__parent.add_to_ignore_list)

        open_action = self.__plugin_menu.addAction(
            qta.icon("fa5s.external-link-alt", color=self.palette().text().color()),
            self.tr("Open..."),
        )
        open_action.triggered.connect(self.__parent.open_plugin)

        self.addSeparator()

    def __init_general_actions(self) -> None:
        self.__show_strings_action = self.addAction(
            qta.icon("mdi6.book-open-outline", color="#ffffff"),
            self.tr("Show strings..."),
        )
        self.__show_strings_action.triggered.connect(self.__parent.show_strings)

        open_modpage_action: QAction = self.addAction(
            QIcon(":/icons/nexus_mods.svg"),
            self.tr("Open mod page on Nexus Mods..."),
        )
        open_modpage_action.triggered.connect(self.__parent.open_modpage)

        open_in_explorer_action: QAction = self.addAction(
            qta.icon("fa5s.folder", color="#ffffff"),
            self.tr("Open in Explorer..."),
        )
        open_in_explorer_action.triggered.connect(self.__parent.open_in_explorer)

    def open(self) -> None:
        """
        Opens the context menu at the current cursor position.
        """

        current_item: Optional[Mod | Plugin] = self.__parent.get_current_item()
        selected_plugins: list[Plugin] = self.__parent.get_selected_items()[1]

        self.__uncheck_action.setVisible(len(selected_plugins) > 0)
        self.__check_action.setVisible(len(selected_plugins) > 0)

        self.__action_menu.menuAction().setVisible(isinstance(current_item, Mod))
        self.__import_as_translation_action.setVisible(
            isinstance(current_item, Mod)
            and any(
                plugin.status == Plugin.Status.IsTranslated
                for plugin in current_item.plugins
            )
        )
        self.__plugin_menu.menuAction().setVisible(isinstance(current_item, Plugin))
        self.__translation_menu.menuAction().setVisible(
            isinstance(current_item, Plugin)
            and current_item.status == Plugin.Status.TranslationInstalled
        )

        self.__show_strings_action.setVisible(
            isinstance(current_item, Plugin)
            or (
                isinstance(current_item, Mod)
                and any(
                    plugin.status != Plugin.Status.NoStrings
                    for plugin in current_item.plugins
                )
            )
        )

        self.exec(QCursor.pos())


if __name__ == "__main__":
    from .mod_instance import ModInstanceWidget
