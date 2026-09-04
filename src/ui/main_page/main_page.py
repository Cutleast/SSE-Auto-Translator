"""
Copyright (c) Cutleast
"""

import logging
import os
import webbrowser
from pathlib import Path
from typing import Optional, cast, override

from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.ui.progress.dialog import ProgressDialog
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel
from cutleast_core_lib.ui.widgets.error_dialog import ErrorDialog
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QColor, QShowEvent
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.database.exporter import Exporter
from core.database.translation import Translation
from core.downloader.download_manager import DownloadListEntries, DownloadManager
from core.downloader.file_download import FileDownload
from core.file_types.file_type import FileType
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.string.search_filter import SearchFilter
from core.string.types import StringList
from core.translation_provider.provider import TranslationProvider
from core.user_data.user_data import UserData
from core.utilities.container_utils import join_dicts
from ui.downloader.download_list_window import DownloadListWindow
from ui.string_list.string_list_window import StringListWindow
from ui.utilities.icon_provider import IconProvider
from ui.widgets.ignore_list_dialog import IgnoreListDialog
from ui.widgets.stacked_bar import StackedBar
from ui.widgets.string_search_dialog import StringSearchDialog

from .database.database_widget import DatabaseWidget
from .main_toolbar import MainToolBar
from .mod_instance.mod_instance import ModInstanceWidget
from .result_dialog import ResultDialog


class MainPageWidget(QWidget):
    """
    Main page of AT, displays modlist including MO2 separators.
    """

    KOFI_URL: str = "https://ko-fi.com/cutleast"
    """URL to Ko-fi page."""

    edit_translation_requested = Signal(Translation)
    """
    Signal emitted when the user requests to edit a translation.

    Args:
        Translation: The translation to edit.
    """

    log: logging.Logger = logging.getLogger("Main")

    __mod_instance: ModInstance

    __app_config: AppConfig
    __user_data: UserData
    __scanner: Scanner
    __provider: TranslationProvider
    __download_manager: DownloadManager
    __state_service: StateService

    __vlayout: QVBoxLayout
    __title_label: QLabel
    __modfiles_num_label: QLabel
    __tool_bar: MainToolBar
    __search_bar: SearchBar
    __bar_chart: StackedBar

    __splitter: QSplitter
    __modinstance_widget: ModInstanceWidget
    __database_widget: DatabaseWidget

    def __init__(
        self,
        app_config: AppConfig,
        user_data: UserData,
        scanner: Scanner,
        provider: TranslationProvider,
        download_manager: DownloadManager,
        state_service: StateService,
    ) -> None:
        """
        Args:
            app_config (AppConfig): The application configuration.
            user_data (UserData): The user data.
            scanner (Scanner): The scanner.
            provider (TranslationProvider): The translation provider.
            download_manager (DownloadManager): The download manager.
            state_service (StateService): The state service.
        """

        super().__init__()

        self.setObjectName("root")

        self.__mod_instance = user_data.mod_instance
        self.__app_config = app_config
        self.__user_data = user_data
        self.__scanner = scanner
        self.__provider = provider
        self.__download_manager = download_manager
        self.__state_service = state_service

        self.__init_ui()

        self.__tool_bar.state_filter_changed.connect(self.__on_state_filter_changed)
        self.__tool_bar.type_filter_changed.connect(self.__on_type_filter_changed)
        self.__tool_bar.ignore_list_requested.connect(self.__open_ignore_list)
        self.__tool_bar.modlist_scan_requested.connect(self.__run_basic_scan)
        self.__tool_bar.online_scan_requested.connect(self.__run_online_scan)
        self.__tool_bar.download_requested.connect(self.__run_downloads)
        self.__tool_bar.build_output_requested.connect(self.__build_output)
        self.__tool_bar.string_search_requested.connect(self.__run_string_search)
        self.__tool_bar.export_states_requested.connect(self.__export_modfile_states)

        self.__search_bar.searchChanged.connect(self.__on_search_changed)

        self.__modinstance_widget.basic_scan_requested.connect(
            lambda: self.__run_basic_scan(only_selected=True)
        )
        self.__modinstance_widget.online_scan_requested.connect(
            lambda: self.__run_online_scan(only_selected=True)
        )
        self.__modinstance_widget.downloads_requested.connect(
            lambda: self.__run_downloads(only_selected=True)
        )
        self.__modinstance_widget.highlight_translation_requested.connect(
            self.__database_widget.highlight_translation
        )
        self.__modinstance_widget.edit_translation_requested.connect(
            self.edit_translation_requested.emit
        )

        self.__database_widget.edit_translation_requested.connect(
            self.edit_translation_requested.emit
        )

        self.__state_service.update_signal.connect(self.__update)
        ThemeManager.get().theme_changed.connect(lambda _: self.__update_header())

        self.__update()
        self.__tool_bar.refresh_filter()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_splitter()
        self.__init_modinstance_widget()
        self.__init_database_widget()

    def __init_header(self) -> None:
        self.__tool_bar = MainToolBar()
        self.__tool_bar.set_provider_features_enabled(self.__provider.is_available)
        self.__tool_bar.set_shortcut_target(self)
        self.__vlayout.addWidget(self.__tool_bar)

        first_action: QAction = self.__tool_bar.actions()[0]

        title_label = QLabel(self.tr("Modlist"))
        title_label.setProperty("title", True)
        self.__tool_bar.insertWidget(first_action, title_label)

        self.__title_label = ElidedLabel(self.tr("Modlist"))
        self.__title_label.setProperty("subtitle", True)
        self.__title_label.setMaximumWidth(300)
        self.__tool_bar.insertWidget(first_action, self.__title_label)

        self.__tool_bar.insertSeparator(first_action)

        self.__search_bar = SearchBar()
        self.__tool_bar.addWidget(self.__search_bar)

        self.__tool_bar.addSeparator()

        num_label = QLabel(self.tr("Translatable files:"))
        num_label.setProperty("subtitle", True)
        self.__tool_bar.addWidget(num_label)

        self.__modfiles_num_label = QLabel()
        self.__modfiles_num_label.setProperty("subtitle", True)
        self.__tool_bar.addWidget(self.__modfiles_num_label)

        self.__bar_chart = StackedBar(
            values=[0 for _ in TranslationStatus],
            colors=[TranslationStatus.get_base_color(s) for s in TranslationStatus],
        )
        self.__bar_chart.setFixedHeight(3)
        self.__vlayout.addWidget(self.__bar_chart)

    def __init_splitter(self) -> None:
        self.__splitter = QSplitter()
        self.__vlayout.addWidget(self.__splitter, stretch=1)

    def __init_modinstance_widget(self) -> None:
        modinstance_wrapper = QWidget()
        self.__splitter.addWidget(modinstance_wrapper)
        modinstance_vlayout = QVBoxLayout()
        modinstance_vlayout.setContentsMargins(0, 0, 0, 0)
        modinstance_wrapper.setLayout(modinstance_vlayout)

        self.__modinstance_widget = ModInstanceWidget(
            self.__app_config, self.__user_data, self.__provider, self.__state_service
        )
        WidgetStateManager.get().register_state(
            "modinstance_widget_header", self.__modinstance_widget.header()
        )
        modinstance_vlayout.addWidget(self.__modinstance_widget)

        footer_hlayout = QHBoxLayout()
        footer_hlayout.setContentsMargins(0, 0, 0, 0)
        modinstance_vlayout.addLayout(footer_hlayout)

        info_icon = QLabel()
        IconProvider.bind_qta_icon(
            info_icon,
            lambda icon: info_icon.setPixmap(
                icon.pixmap(
                    ThemeManager.get().theme.metrics.icon,
                    ThemeManager.get().theme.metrics.icon,
                )
            ),
            "mdi6.alert",
            color=IconProvider.Color.Secondary,
        )
        footer_hlayout.addWidget(info_icon)

        info_label = QLabel(
            self.tr(
                "SSE-AT has to be restarted after mod list changes. Changes are not "
                "automatically detected."
            )
        )
        info_label.setProperty("secondary", True)
        info_label.setWordWrap(True)
        footer_hlayout.addWidget(info_label, stretch=1)

    def __init_database_widget(self) -> None:
        self.__database_widget = DatabaseWidget(
            database=self.__user_data.database,
            provider=self.__provider,
            mod_instance=self.__mod_instance,
            app_config=self.__app_config,
            scanner=self.__scanner,
            download_manager=self.__download_manager,
            state_service=self.__state_service,
        )
        self.__splitter.addWidget(self.__database_widget)

    def __update(self) -> None:
        self.__title_label.setText(self.__mod_instance.display_name)
        self.__modfiles_num_label.setText(
            str(self.__modinstance_widget.get_visible_modfile_item_count())
        )
        self.__update_header()

    def __update_header(self) -> None:
        modfile_states: dict[TranslationStatus, int] = (
            self.__state_service.get_modfile_state_summary(
                self.__modinstance_widget.get_visible_modfiles()
            )
        )
        self.__bar_chart.setValues(list(modfile_states.values()))
        self.__bar_chart.setColors(
            [TranslationStatus.get_base_color(s) for s in TranslationStatus]
        )

        num_tooltip = ""

        for status, count in modfile_states.items():
            color: Optional[QColor] = TranslationStatus.get_fg_color(status)

            if color is None:
                num_tooltip += f"<tr><td>{status.get_localized_name()}:\
                    </td><td align=right>{count}</td></tr>"
            else:
                num_tooltip += f"<tr><td><font color='{color.name()}'>{status.get_localized_name()}:\
                    </font></td><td align=right><font color='{color.name()}'>{count}</font></td></tr>"

        self.__modfiles_num_label.setToolTip(num_tooltip)
        self.__bar_chart.setToolTip(num_tooltip)

    def __on_search_changed(self, text: str, case_sensitive: bool) -> None:
        self.__database_widget.set_name_filter(text, case_sensitive)
        self.__modinstance_widget.set_name_filter(text, case_sensitive)

        self.__update()

    def __on_state_filter_changed(self, state_filter: list[TranslationStatus]) -> None:
        self.__modinstance_widget.set_state_filter(state_filter)

        self.__update()

    def __on_type_filter_changed(self, type_filter: list[FileType]) -> None:
        self.__modinstance_widget.set_type_filter(type_filter)

        self.__update()

    def __open_ignore_list(self) -> None:
        """
        Opens Ignore List in a new Popup Dialog.
        """

        IgnoreListDialog(
            masterlist=self.__user_data.masterlist,
            user_config=self.__user_data.user_config,
            parent=QApplication.activeModalWidget(),
        ).exec()
        self.__user_data.user_config.save()

        self.__modinstance_widget.update()

    def __show_scan_result(self, modfiles: Optional[list[ModFile]] = None) -> None:
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
            summary=self.__state_service.get_modfile_state_summary(modfiles),
            parent=QApplication.activeModalWidget(),
        ).exec()

    def __run_basic_scan(self, only_selected: bool = False) -> None:
        """
        Runs a basic scan over the currently checked mod files.

        Args:
            only_selected (bool, optional):
                Whether to scan only the currently selected mods and mod files.
                Defaults to False.
        """

        mods: list[Mod]
        modfiles: dict[Mod, list[ModFile]]
        if not only_selected:
            modfiles = self.__modinstance_widget.get_checked_items()
            mods = self.__mod_instance.mods
        else:
            mods = self.__modinstance_widget.get_selected_items()[0]
            modfiles = self.__modinstance_widget.get_selected_modfiles()

        scan_result: dict[ModFile, TranslationStatus] = join_dicts(
            *ProgressDialog(
                func=lambda pdisplay: self.__scanner.run_basic_scan(modfiles, pdisplay),
                parent=QApplication.activeModalWidget(),
            )
            .run()
            .values(),
        )
        self.__state_service.set_modfile_states(scan_result)

        if self.__app_config.auto_import_translations:
            ProgressDialog(
                func=lambda pdisplay: self.__scanner.import_installed_translations(
                    mods, pdisplay
                ),
                parent=QApplication.activeModalWidget(),
            ).run()

        self.__show_scan_result(list(scan_result.keys()))

    def __run_online_scan(self, only_selected: bool = False) -> None:
        """
        Runs an online scan over the currently checked mod files.

        Args:
            only_selected (bool, optional):
                Whether to scan only the currently selected mods and mod files.
                Defaults to False.
        """

        modfiles: dict[Mod, list[ModFile]]
        if not only_selected:
            modfiles = self.__modinstance_widget.get_checked_items()
        else:
            modfiles = self.__modinstance_widget.get_selected_modfiles()

        scan_result: dict[ModFile, TranslationStatus] = join_dicts(
            *ProgressDialog(
                lambda pdisplay: self.__scanner.run_online_scan(modfiles, pdisplay)
            )
            .run()
            .values()
        )
        self.__state_service.set_modfile_states(scan_result)

        self.__show_scan_result(list(scan_result.keys()))

    def __run_downloads(self, only_selected: bool = False) -> None:
        """
        Collects available translations for the currently checked mod files
        and opens a DownloadListDialog.

        Args:
            only_selected (bool, optional):
                Whether to download only for the currently selected mods and mod files.
                Defaults to False.
        """

        items: dict[Mod, list[ModFile]]
        if not only_selected:
            items = self.__modinstance_widget.get_checked_items()
        else:
            items = self.__modinstance_widget.get_selected_modfiles()

        download_entries: DownloadListEntries = ProgressDialog(
            lambda pdisplay: self.__download_manager.collect_available_downloads(
                items, pdisplay
            ),
        ).run()
        if download_entries:
            download_list_window = DownloadListWindow(download_entries, self.__provider)
            download_list_window.downloads_started.connect(
                lambda file_downloads, link_nxm: list(
                    map(
                        self.__download_manager.request_download,
                        cast(list[FileDownload], file_downloads),
                    )
                )
            )
            download_list_window.downloads_started.connect(
                lambda file_downloads, link_nxm: self.__download_manager.start()
            )
            WindowManager.get().show(download_list_window)
        else:
            QMessageBox.information(
                QApplication.activeModalWidget() or self,
                self.tr("No translation downloads available!"),
                self.tr("There are no translations available to download."),
            )

    def __build_output(self) -> None:
        """
        Builds the output mod at the configured location.
        """

        output_path: Path = ProgressDialog(
            func=lambda pdisplay: Exporter().build_output_mod(
                output_path=(
                    self.__app_config.output_path
                    or (get_current_path() / "SSE-AT Output")
                ),
                mod_instance=self.__mod_instance,
                translations=self.__user_data.database.user_translations,
                user_config=self.__user_data.user_config,
                pdisplay=pdisplay,
            ),
            parent=QApplication.activeModalWidget(),
        ).run()

        message_box = QMessageBox()
        message_box.setWindowTitle(self.tr("Success!"))
        message_box.setText(
            self.tr(
                "The output mod was successfully built at:\n{0}\n\nPlease drag this "
                "folder to your modlist in MO2 or Vortex and ensure that Dynamic String "
                "Distributor is installed and both mods are enabled!"
            ).format(str(output_path))
        )
        message_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
            | QMessageBox.StandardButton.Help
            | QMessageBox.StandardButton.Open
        )
        message_box.button(QMessageBox.StandardButton.Ok).setText(self.tr("Ok"))
        message_box.button(QMessageBox.StandardButton.Help).setText(
            self.tr("Open output mod in Explorer")
        )
        btn: QAbstractButton = message_box.button(QMessageBox.StandardButton.Open)
        btn.setText(self.tr("Open DSD modpage on Nexus Mods"))
        btn.clicked.disconnect()
        btn.clicked.connect(
            lambda: webbrowser.open(
                "https://www.nexusmods.com/skyrimspecialedition/mods/107676"
            )
        )

        choice: int = message_box.exec()

        if choice == QMessageBox.StandardButton.Help:
            os.startfile(output_path)

    def __run_string_search(self) -> None:
        """
        Similar to Database Search feature but for loaded modlist.
        """

        dialog = StringSearchDialog(QApplication.activeModalWidget(), translations=False)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            filter: SearchFilter = dialog.get_filter()

            search_result: dict[Path, StringList] = ProgressDialog(
                func=lambda pdisplay: self.__scanner.run_string_search(
                    self.__modinstance_widget.get_checked_items(), filter, pdisplay
                ),
                parent=QApplication.activeModalWidget(),
            ).run()

            if search_result:
                WindowManager.get().show(
                    StringListWindow(
                        name=self.tr("Search Results"),
                        strings=search_result,
                        translation_mode=False,
                    )
                )
            else:
                ErrorDialog(
                    parent=QApplication.activeModalWidget(),
                    title=self.tr("No strings found!"),
                    text=self.tr(
                        "Did not find any strings matching the given filter!\n"
                        'Click on "Show details" to view used filter.'
                    ),
                    details=str(filter),
                    yesno=False,
                ).show()

    def __export_modfile_states(self) -> None:
        """
        Exports the current modfile states to a JSON file.
        """

        fdialog = QFileDialog(
            QApplication.activeModalWidget(),
            caption=self.tr("Export mod file states..."),
        )
        fdialog.setFileMode(QFileDialog.FileMode.AnyFile)
        fdialog.setNameFilter(self.tr("JSON files") + " (*.json)")
        fdialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        fdialog.selectFile("modfile_states.json")

        if fdialog.exec() == QFileDialog.DialogCode.Accepted:
            file_path = Path(fdialog.selectedFiles()[0])

            self.__state_service.export_states_to_json_file(
                file_path,
                check_states={
                    modfile: self.__modinstance_widget.is_modfile_checked(modfile, mod)
                    for mod in self.__user_data.mod_instance.mods
                    for modfile in mod.modfiles
                },
            )

            QMessageBox.information(
                QApplication.activeModalWidget(),
                self.tr("Export successful!"),
                self.tr("Successfully exported mod file states to:") + f"\n{file_path}",
                buttons=QMessageBox.StandardButton.Ok,
            )

    @override
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        self.__splitter.setSizes(
            [int(0.5 * self.__splitter.width()), int(0.5 * self.__splitter.width())]
        )
        WidgetStateManager.get().register_state("main_splitter", self.__splitter)

    def save_state(self) -> None:
        """
        Saves the state of the widget to the cache.
        """

        self.__state_service.save_states_to_cache(
            {
                modfile: self.__modinstance_widget.is_modfile_checked(modfile, mod)
                for mod in self.__user_data.mod_instance.mods
                for modfile in mod.modfiles
            }
        )
