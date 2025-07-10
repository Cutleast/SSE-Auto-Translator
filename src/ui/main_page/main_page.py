"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import Optional, TypeVar

from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.cache.cache import Cache
from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.search_filter import SearchFilter
from core.database.string import String
from core.downloader.download_manager import DownloadManager
from core.downloader.translation_download import TranslationDownload
from core.masterlist.masterlist import Masterlist
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.translation_provider.mod_id import ModId
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.utilities.container_utils import join_dicts
from core.utilities.exe_info import get_current_path
from ui.downloader.download_list_dialog import DownloadListDialog
from ui.widgets.error_dialog import ErrorDialog
from ui.widgets.ignore_list_dialog import IgnoreListDialog
from ui.widgets.lcd_number import LCDNumber
from ui.widgets.link_button import LinkButton
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.search_bar import SearchBar
from ui.widgets.stacked_bar import StackedBar
from ui.widgets.string_list.string_list_dialog import StringListDialog
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

    cache: Cache
    database: TranslationDatabase
    app_config: AppConfig
    user_config: UserConfig
    masterlist: Masterlist
    mod_instance: ModInstance
    scanner: Scanner
    provider: Provider
    download_manager: DownloadManager
    state_service: StateService
    nxm_listener: NXMHandler

    __vlayout: QVBoxLayout
    __title_label: QLabel
    __modfiles_num_label: LCDNumber
    __tool_bar: MainToolBar
    __search_bar: SearchBar
    __bar_chart: StackedBar

    __modinstance_widget: ModInstanceWidget
    __database_widget: DatabaseWidget

    def __init__(
        self,
        cache: Cache,
        database: TranslationDatabase,
        app_config: AppConfig,
        user_config: UserConfig,
        masterlist: Masterlist,
        mod_instance: ModInstance,
        scanner: Scanner,
        provider: Provider,
        download_manager: DownloadManager,
        state_service: StateService,
        nxm_listener: NXMHandler,
    ) -> None:
        super().__init__()

        self.cache = cache
        self.database = database
        self.app_config = app_config
        self.user_config = user_config
        self.masterlist = masterlist
        self.mod_instance = mod_instance
        self.scanner = scanner
        self.provider = provider
        self.download_manager = download_manager
        self.state_service = state_service
        self.nxm_listener = nxm_listener

        self.__init_ui()

        self.state_service.update_signal.connect(self.__update)
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

        num_label = QLabel(self.tr("Translatable files:"))
        num_label.setObjectName("relevant_label")
        hlayout.addWidget(num_label)

        self.__modfiles_num_label = LCDNumber()
        self.__modfiles_num_label.setDigitCount(4)
        hlayout.addWidget(self.__modfiles_num_label)

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
            [0 for _ in TranslationStatus],
            colors=[TranslationStatus.get_color(s) for s in TranslationStatus],
        )
        self.__bar_chart.setFixedHeight(3)
        self.__vlayout.addWidget(self.__bar_chart)

    def __init_splitter(self) -> None:
        splitter = QSplitter()
        self.__vlayout.addWidget(splitter, stretch=1)

        self.__modinstance_widget = ModInstanceWidget(
            self.cache,
            self.database,
            self.app_config,
            self.user_config,
            self.masterlist,
            self.scanner,
            self.provider,
            self.download_manager,
            self.nxm_listener,
            self.mod_instance,
            self.state_service,
        )
        splitter.addWidget(self.__modinstance_widget)

        self.__database_widget = DatabaseWidget(
            self.database,
            self.provider,
            self.mod_instance,
            self.app_config,
            self.scanner,
            self.download_manager,
            self.nxm_listener,
        )
        splitter.addWidget(self.__database_widget)

        self.__search_bar.searchChanged.connect(
            self.__modinstance_widget.set_name_filter
        )
        self.__search_bar.searchChanged.connect(self.__database_widget.set_name_filter)

        splitter.setSizes([int(0.6 * splitter.width()), int(0.4 * splitter.width())])

    def __update(self) -> None:
        self.__title_label.setText(self.mod_instance.display_name)
        self.__modfiles_num_label.display(len(self.mod_instance.modfiles))
        self.__update_header()

    def __update_header(self) -> None:
        modfile_states: dict[TranslationStatus, int] = (
            self.state_service.get_modfile_state_summary()
        )
        self.__bar_chart.setValues(list(modfile_states.values()))

        num_tooltip = ""

        for status, count in modfile_states.items():
            color: Optional[QColor] = TranslationStatus.get_color(status)

            if color is None:
                num_tooltip += f"<tr><td>{status.get_localized_name()}:\
                    </td><td align=right>{count}</td></tr>"
            else:
                num_tooltip += f"<tr><td><font color='{color.name()}'>{status.get_localized_name()}:\
                    </font></td><td align=right><font color='{color.name()}'>{count}</font></td></tr>"

        self.__modfiles_num_label.setToolTip(num_tooltip)
        self.__bar_chart.setToolTip(num_tooltip)

    def open_ignore_list(self) -> None:
        """
        Opens Ignore List in a new Popup Dialog.
        """

        IgnoreListDialog(
            self.masterlist, self.user_config, QApplication.activeModalWidget()
        ).exec()
        self.user_config.save()

        # TODO: Make this more elegant
        self.state_service.update_signal.emit()

    def show_scan_result(self, modfiles: Optional[list[ModFile]] = None) -> None:
        """
        Displays scan result popup.

        Args:
            modfiles (Optional[list[ModFile]]):
                The mod files to display the result for.
                Defaults to the currently checked mod files.
        """

        if modfiles is None:
            modfiles = [
                modfile
                for _modfiles in self.__modinstance_widget.get_checked_items().values()
                for modfile in _modfiles
            ]

        ResultDialog(
            self.state_service.get_modfile_state_summary(modfiles),
            QApplication.activeModalWidget(),
        ).exec()

    def show_help(self) -> None:
        """
        Displays help popup.
        """

        self.__modinstance_widget.show_help()

    def basic_scan(self) -> None:
        """
        Runs a basic scan over the currently checked mod files.
        """

        checked_items: dict[Mod, list[ModFile]] = (
            self.__modinstance_widget.get_checked_items()
        )
        checked_mods: list[Mod] = list(checked_items.keys())

        scan_result: dict[ModFile, TranslationStatus] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.run_basic_scan(checked_items, ldialog),
            ).values()
        )
        self.state_service.set_modfile_states(scan_result)

        if self.app_config.auto_import_translations:
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.import_installed_translations(
                    checked_mods, ldialog
                ),
            )

        self.show_scan_result(list(scan_result.keys()))
        self.__tool_bar.highlight_action(self.__tool_bar.online_scan_action)

    def online_scan(self) -> None:
        """
        Runs an online scan over the currently checked mod files.
        """

        checked_items: dict[Mod, list[ModFile]] = (
            self.__modinstance_widget.get_checked_items()
        )

        scan_result: dict[ModFile, TranslationStatus] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.run_online_scan(checked_items, ldialog),
            ).values()
        )
        self.state_service.set_modfile_states(scan_result)

        self.show_scan_result(list(scan_result.keys()))
        self.__tool_bar.highlight_action(self.__tool_bar.download_action)

    def download_and_install_translations(self) -> None:
        """
        Collects available translations for the currently checked mod files
        and opens a DownloadListDialog.
        """

        download_entries: dict[tuple[str, ModId], list[TranslationDownload]] = (
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.download_manager.collect_available_downloads(
                    self.__modinstance_widget.get_checked_items(), ldialog
                ),
            )
        )
        DownloadListDialog(
            download_entries,
            self.provider,
            self.database,
            self.download_manager,
            self.nxm_listener,
            parent=QApplication.activeModalWidget(),
        ).exec()

        self.__tool_bar.highlight_action(self.__tool_bar.build_output_action)

    def build_output(self) -> None:
        """
        Builds the output mod at the configured location.
        """

        output_path: Path = LoadingDialog.run_callable(
            QApplication.activeModalWidget(),
            lambda ldialog: self.database.exporter.build_output_mod(
                self.app_config.output_path or (get_current_path() / "SSE-AT Output"),
                self.mod_instance,
                self.app_config.get_tmp_dir(),
                ldialog,
            ),
        )

        message_box = QMessageBox()
        message_box.setWindowTitle(self.tr("Success!"))
        message_box.setText(self.tr("Created output mod at: ") + str(output_path))
        message_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
            | QMessageBox.StandardButton.Help
            | QMessageBox.StandardButton.Open
        )
        message_box.button(QMessageBox.StandardButton.Ok).setText(self.tr("Ok"))
        message_box.button(QMessageBox.StandardButton.Help).setText(
            self.tr("Open output mod in Explorer")
        )
        btn = message_box.button(QMessageBox.StandardButton.Open)
        btn.setText(self.tr("Open DSD modpage on Nexus Mods"))
        btn.clicked.disconnect()
        btn.clicked.connect(
            lambda: os.startfile(
                "https://www.nexusmods.com/skyrimspecialedition/mods/107676"
            )
        )

        choice = message_box.exec()

        if choice == message_box.StandardButton.Help:
            os.startfile(output_path)

    def deep_scan(self) -> None:
        """
        Runs a deep scan over the installed translations.
        """

        result: dict[ModFile, TranslationStatus] = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.scanner.run_deep_scan
        )
        self.state_service.set_modfile_states(result)
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

            search_result: dict[str, list[String]] = LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.run_string_search(
                    self.__modinstance_widget.get_checked_items(), filter, ldialog
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

    def set_state_filter(self, state_filter: list[TranslationStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[TranslationStatus]): The states to filter by.
        """

        self.__modinstance_widget.set_state_filter(state_filter)
