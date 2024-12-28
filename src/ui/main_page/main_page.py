"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional, TypeVar

from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.cacher.cacher import Cacher
from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.search_filter import SearchFilter
from core.database.string import String
from core.downloader.download_manager import DownloadManager
from core.downloader.translation_download import TranslationDownload
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.plugin import Plugin
from core.scanner.scanner import Scanner
from core.utilities.container_utils import join_dicts
from ui.widgets.download_list_dialog import DownloadListDialog
from ui.widgets.error_dialog import ErrorDialog
from ui.widgets.ignore_list_dialog import IgnoreListDialog
from ui.widgets.lcd_number import LCDNumber
from ui.widgets.link_button import LinkButton
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.search_bar import SearchBar
from ui.widgets.stacked_bar import StackedBar
from ui.widgets.string_list_dialog import StringListDialog
from ui.widgets.string_search_dialog import StringSearchDialog

from .database.database_widget import DatabaseWidget
from .main_toolbar import MainToolBar
from .mod_instance.mod_instance import ModInstanceWidget
from .result_dialog import ResultDialog

T = TypeVar("T")


class MainPageWidget(QWidget):
    """
    Main page of AT, displays modlist including MO2 separators.
    """

    log: logging.Logger = logging.getLogger("Main")

    mod_instance: ModInstance
    ignore_list: list[str]

    cacher: Cacher
    database: TranslationDatabase
    user_config: UserConfig

    __vlayout: QVBoxLayout
    __title_label: QLabel
    __plugins_num_label: LCDNumber
    __tool_bar: MainToolBar
    __search_bar: SearchBar
    __bar_chart: StackedBar

    __modinstance_widget: ModInstanceWidget
    __database_widget: DatabaseWidget

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        AppContext.get_app().ready_signal.connect(self.__post_init)

    def __post_init(self) -> None:
        self.cacher = AppContext.get_app().cacher
        self.database = AppContext.get_app().database
        self.user_config = AppContext.get_app().user_config
        self.mod_instance = AppContext.get_app().mod_instance
        self.mod_instance.update_signal.connect(self.__update)

        self.__update()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_splitter()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__title_label = QLabel(self.tr("Modlist"))
        self.__title_label.setObjectName("relevant_label")
        hlayout.addWidget(self.__title_label)

        hlayout.addStretch()

        num_label = QLabel(self.tr("Plugins:"))
        num_label.setObjectName("relevant_label")
        hlayout.addWidget(num_label)

        self.__plugins_num_label = LCDNumber()
        self.__plugins_num_label.setDigitCount(4)
        hlayout.addWidget(self.__plugins_num_label)

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__tool_bar = MainToolBar(self)
        hlayout.addWidget(self.__tool_bar)

        self.__search_bar = SearchBar()
        hlayout.addWidget(self.__search_bar)

        ko_fi_button = LinkButton(
            "https://ko-fi.com/cutleast",
            self.tr("Support us on Ko-Fi"),
            QIcon(":/icons/ko-fi.png"),
        )
        hlayout.addWidget(ko_fi_button)

        discord_button = LinkButton(
            "https://discord.gg/pqEHdWDf8z",
            self.tr("Join us on Discord"),
            QIcon(":/icons/discord.png"),
        )
        hlayout.addWidget(discord_button)

        nexus_mods_button = LinkButton(
            "https://next.nexusmods.com/profile/Cutleast",
            self.tr("Check out my profile on Nexus Mods"),
            QIcon(":/icons/nexus_mods.png"),
        )
        hlayout.addWidget(nexus_mods_button)

        self.__bar_chart = StackedBar(
            [0 for s in Plugin.Status],
            colors=[Plugin.Status.get_color(s) for s in Plugin.Status],
        )
        self.__bar_chart.setFixedHeight(3)
        self.__vlayout.addWidget(self.__bar_chart)

    def __init_splitter(self) -> None:
        splitter = QSplitter()
        self.__vlayout.addWidget(splitter, stretch=1)

        self.__modinstance_widget = ModInstanceWidget()
        splitter.addWidget(self.__modinstance_widget)

        self.__database_widget = DatabaseWidget()
        splitter.addWidget(self.__database_widget)

        self.__search_bar.searchChanged.connect(
            self.__modinstance_widget.set_name_filter
        )
        self.__search_bar.searchChanged.connect(self.__database_widget.set_name_filter)

        splitter.setSizes([int(0.6 * splitter.width()), int(0.4 * splitter.width())])

    def __update(self) -> None:
        self.__title_label.setText(self.mod_instance.display_name)
        self.__plugins_num_label.display(len(self.mod_instance.plugins))
        self.__update_header()

    def __update_header(self) -> None:
        plugin_states: dict[Plugin.Status, int] = (
            self.mod_instance.get_plugin_state_summary()
        )
        self.__bar_chart.setValues(list(plugin_states.values()))

        num_tooltip = ""

        for status, count in plugin_states.items():
            color: Optional[QColor] = Plugin.Status.get_color(status)

            if color is None:
                num_tooltip += f"<tr><td>{status.get_localized_name()}:\
                    </td><td align=right>{count}</td></tr>"
            else:
                num_tooltip += f"<tr><td><font color='{color.name()}'>{status.get_localized_name()}:\
                    </font></td><td align=right><font color='{color.name()}'>{count}</font></td></tr>"

        self.__plugins_num_label.setToolTip(num_tooltip)
        self.__bar_chart.setToolTip(num_tooltip)

    def open_ignore_list(self) -> None:
        """
        Opens Ignore List in a new Popup Dialog.
        """

        IgnoreListDialog(QApplication.activeModalWidget()).exec()
        self.user_config.save()

    def show_scan_result(self, plugins: Optional[list[Plugin]] = None) -> None:
        """
        Displays scan result popup.

        Args:
            plugins (Optional[list[Plugin]]):
                The plugins to display the result for.
                Defaults to the currently checked plugins.
        """

        if plugins is None:
            plugins = [
                plugin
                for plugins in self.__modinstance_widget.get_checked_items().values()
                for plugin in plugins
            ]

        ResultDialog(
            self.mod_instance.get_plugin_state_summary(plugins),
            QApplication.activeModalWidget(),
        ).exec()

    def show_help(self) -> None:
        """
        Displays help popup.
        """

        self.__modinstance_widget.show_help()

    def basic_scan(self) -> None:
        """
        Runs a basic scan over the currently checked plugins.
        """

        scanner: Scanner = AppContext.get_app().scanner

        checked_items: dict[Mod, list[Plugin]] = (
            self.__modinstance_widget.get_checked_items()
        )
        checked_mods: list[Mod] = list(checked_items.keys())

        scan_result: dict[Plugin, Plugin.Status] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: scanner.run_basic_scan(checked_items, ldialog),
            ).values()
        )
        self.mod_instance.set_plugin_states(scan_result)

        app_config: AppConfig = AppContext.get_app().app_config
        if app_config.auto_import_translations:
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: scanner.import_installed_translations(
                    checked_mods, ldialog
                ),
            )

        self.show_scan_result(list(scan_result.keys()))
        self.__tool_bar.highlight_action(self.__tool_bar.online_scan_action)

    def online_scan(self) -> None:
        """
        Runs an online scan over the currently checked plugins.
        """

        scanner: Scanner = AppContext.get_app().scanner

        checked_items: dict[Mod, list[Plugin]] = (
            self.__modinstance_widget.get_checked_items()
        )

        scan_result: dict[Plugin, Plugin.Status] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: scanner.run_online_scan(checked_items, ldialog),
            ).values()
        )
        self.mod_instance.set_plugin_states(scan_result)

        self.show_scan_result(list(scan_result.keys()))
        self.__tool_bar.highlight_action(self.__tool_bar.download_action)

    def download_and_install_translations(self) -> None:
        """
        Collects available translations for the currently checked plugins
        and opens a DownloadListDialog.
        """

        download_manager: DownloadManager = AppContext.get_app().download_manager
        download_entries: dict[str, list[TranslationDownload]] = (
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: download_manager.collect_available_downloads(
                    self.__modinstance_widget.get_checked_items(), ldialog
                ),
            )
        )
        DownloadListDialog(
            download_entries, parent=QApplication.activeModalWidget()
        ).exec()

        self.__tool_bar.highlight_action(self.__tool_bar.build_output_action)

    def deep_scan(self) -> None:
        """
        Runs a deep scan over the installed translations.
        """

        result: dict[Plugin, Plugin.Status] = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), AppContext.get_app().scanner.run_deep_scan
        )
        self.mod_instance.set_plugin_states(result)
        self.show_scan_result(list(result.keys()))

    def run_string_search(self) -> None:
        """
        Similar to Database Search feature but for loaded modlist.
        """

        dialog = StringSearchDialog(
            QApplication.activeModalWidget(), translations=False
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            filter: SearchFilter = dialog.get_filter()
            scanner: Scanner = AppContext.get_app().scanner

            search_result: dict[str, list[String]] = LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: scanner.run_string_search(
                    self.__modinstance_widget.get_checked_items(),
                    filter,
                    ldialog,
                ),
            )

            if search_result:
                StringListDialog(
                    self.tr("Search Results"), search_result, show_translation=False
                ).show()
            else:
                ErrorDialog(
                    QApplication.activeModalWidget(),
                    title=self.tr("No strings found!"),
                    text=self.tr(
                        "Did not find any strings matching the given filter!\n"
                        'Click on "Show Details" to view used filter.'
                    ),
                    details=str(filter),
                    yesno=False,
                ).show()

    def set_state_filter(self, state_filter: list[Plugin.Status]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[Plugin.Status]): The states to filter by.
        """

        self.__modinstance_widget.set_state_filter(state_filter)
