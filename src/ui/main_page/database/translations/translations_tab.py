"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.ui.widgets.error_dialog import ErrorDialog
from cutleast_core_lib.ui.widgets.lcd_number import LCDNumber
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from cutleast_core_lib.ui.widgets.progress_dialog import ProgressDialog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.translation import Translation
from core.downloader.download_manager import DownloadListEntries, DownloadManager
from core.mod_file.mod_file import ModFile
from core.mod_file.plugin_file import PluginFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.scanner.scanner import Scanner
from core.string import StringList
from core.string.search_filter import SearchFilter
from core.string.string_extractor import StringExtractor
from core.translation_provider.provider import Provider
from ui.downloader.download_list_window import DownloadListWindow
from ui.widgets.string_list.string_list_dialog import StringListDialog
from ui.widgets.string_search_dialog import StringSearchDialog

from .translations_toolbar import TranslationsToolbar
from .translations_widget import TranslationsWidget


class TranslationsTab(QWidget):
    """
    Tab for Translations Database.
    """

    edit_translation_requested = Signal(Translation)
    """
    Signal emitted when the user requests to edit a translation.

    Args:
        Translation: Translation to edit.
    """

    log: logging.Logger = logging.getLogger("TranslationsTab")

    database: TranslationDatabase
    provider: Provider
    mod_instance: ModInstance
    app_config: AppConfig
    scanner: Scanner
    download_manager: DownloadManager

    __vlayout: QVBoxLayout
    __toolbar: TranslationsToolbar
    __translations_num_label: LCDNumber
    __translations_widget: TranslationsWidget

    def __init__(
        self,
        database: TranslationDatabase,
        provider: Provider,
        mod_instance: ModInstance,
        app_config: AppConfig,
        scanner: Scanner,
        download_manager: DownloadManager,
    ) -> None:
        super().__init__()

        self.database = database
        self.provider = provider
        self.mod_instance = mod_instance
        self.app_config = app_config
        self.scanner = scanner
        self.download_manager = download_manager

        self.__init_ui()

        self.__toolbar.show_vanilla_strings_requested.connect(
            self.__show_vanilla_strings
        )
        self.__toolbar.search_database_requested.connect(self.__search_database)
        self.__toolbar.local_import_requested.connect(self.__import_local_translation)
        self.__toolbar.update_check_requested.connect(self.__check_for_updates)
        self.__toolbar.download_updates_requested.connect(self.__download_updates)

        self.__translations_widget.edit_translation_requested.connect(
            self.edit_translation_requested.emit
        )
        self.__translations_widget.files_dropped.connect(
            self.__import_local_translation
        )

        self.database.update_signal.connect(self.__update)
        self.__update()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_translations_widget()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__toolbar = TranslationsToolbar()
        hlayout.addWidget(self.__toolbar)

        hlayout.addStretch()

        translations_num_label = QLabel(self.tr("Translations:"))
        translations_num_label.setObjectName("h3")
        hlayout.addWidget(translations_num_label)

        self.__translations_num_label = LCDNumber()
        self.__translations_num_label.setDigitCount(4)
        hlayout.addWidget(self.__translations_num_label)

    def __init_translations_widget(self) -> None:
        self.__translations_widget = TranslationsWidget(
            self.database, self.provider, self.mod_instance, self.app_config
        )
        self.__vlayout.addWidget(self.__translations_widget)

    def __show_vanilla_strings(self) -> None:
        """
        Displays the vanilla strings in a StringListDialog.
        """

        StringListDialog(
            self.tr("Base Game + AE CC Content"),
            self.database.vanilla_translation.strings,
            show_translation=True,
        ).show()

    def __search_database(self) -> None:
        """
        Shows a string search dialog to search the database.
        """

        dialog = StringSearchDialog(QApplication.activeModalWidget())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            filter: SearchFilter = dialog.get_filter()

            search_result: dict[Path, StringList] = self.database.search_database(
                filter
            )

            if search_result:
                StringListDialog(
                    self.tr("Search Results"),
                    search_result,
                    show_translation=True,
                ).show()
            else:
                ErrorDialog(
                    QApplication.activeModalWidget(),
                    title=self.tr("No strings found!"),
                    text=self.tr(
                        "Did not find any strings matching the given filter!\n"
                        'Click on "Show details" to view used filter.'
                    ),
                    details=str(filter),
                    yesno=False,
                ).exec()

    def __import_local_translation(self, files: Optional[list[Path]] = None) -> None:
        """
        Imports a translation from local disk.
        Shows a file dialog if no files are specified.

        Args:
            files (Optional[list[Path]], optional):
                The files to import. Defaults to None.
        """

        if files is None:
            fdialog = QFileDialog()
            fdialog.setFileMode(fdialog.FileMode.ExistingFiles)
            fdialog.setNameFilters(
                [
                    self.tr("Mod archive") + " (*.7z *.rar *.zip)",
                    self.tr("Skyrim SE plugin") + " (*.esp *.esm *.esl)",
                ]
            )
            fdialog.setWindowTitle(self.tr("Import Translation..."))

            if fdialog.exec() == QDialog.DialogCode.Rejected:
                return

            files = [Path(file) for file in fdialog.selectedFiles()]

        translation: Translation
        strings: dict[Path, StringList]
        for file in files:
            if file.suffix.lower() in [".7z", ".rar", ".zip"]:
                strings = ProgressDialog(
                    lambda pdialog: StringExtractor().extract_strings(
                        file,
                        mod_instance=self.mod_instance,
                        language=self.database.language,
                        pdialog=pdialog,
                    )
                ).run()

                if strings:
                    translation = DatabaseService.create_blank_translation(
                        file.stem, strings, self.database
                    )
                    translation.save()
                    DatabaseService.add_translation(translation, self.database)

            elif file.suffix.lower() in [".esp", ".esm", ".esl"]:
                original_plugin: Optional[ModFile] = self.mod_instance.get_modfile(
                    Path(file.name),
                    ignore_states=[
                        TranslationStatus.IsTranslated,
                        TranslationStatus.TranslationInstalled,
                    ],
                )

                if original_plugin is not None:
                    strings = {
                        original_plugin.path: StringExtractor.map_translation_strings(
                            PluginFile(file.name, file), original_plugin
                        )
                    }

                    if strings:
                        translation = DatabaseService.create_blank_translation(
                            f"{file.name} - {self.database.language.name}",
                            strings,
                            self.database,
                        )
                        translation.save()
                        DatabaseService.add_translation(translation, self.database)

    def __check_for_updates(self) -> None:
        """
        Checks for updates for all installed translations and updates their status.
        """

        scan_result: dict[Translation, bool] = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.scanner.check_for_translation_updates
        )

        for translation, update_available in scan_result.items():
            if update_available:
                translation.status = Translation.Status.UpdateAvailable

        self.__translations_widget.update_translations()

        available_updates_count: int = sum(scan_result.values())
        messagebox = QMessageBox(QApplication.activeModalWidget())
        messagebox.setWindowTitle(self.tr("Update check complete!"))
        messagebox.setText(
            self.tr(
                "Found updates for %n translations.",
                "Found an update for one translation.",
                available_updates_count,
            )
        )
        messagebox.exec()

        self.__toolbar.set_download_updates_enabled(available_updates_count > 0)

    def __download_updates(self) -> None:
        translations: dict[Translation, Mod] = {}
        for translation in filter(
            lambda t: t.status == Translation.Status.UpdateAvailable,
            self.database.user_translations,
        ):
            if translation.original_mod_id is None:
                self.log.warning(
                    f"Original mod for translation '{translation.name}' is unknown!"
                )
                continue

            original_mod: Optional[Mod] = self.mod_instance.get_mod(
                translation.original_mod_id
            )

            if original_mod is None:
                self.log.warning(
                    f"Original mod for translation {translation.name!r} not installed!"
                )
                continue

            translations[translation] = original_mod

        download_entries: DownloadListEntries = LoadingDialog.run_callable(
            QApplication.activeModalWidget(),
            lambda ldialog: self.download_manager.collect_available_updates(
                translations, ldialog
            ),
        )
        if download_entries:
            download_list_window = DownloadListWindow(download_entries, self.provider)
            download_list_window.downloads_started.connect(
                lambda downloads, link_nxm: list(
                    map(self.download_manager.request_download, downloads)
                )
            )
            download_list_window.downloads_started.connect(
                lambda file_downloads, link_nxm: self.download_manager.start()
            )
            download_list_window.show()
        else:
            QMessageBox.warning(
                QApplication.activeModalWidget() or self,
                self.tr("No updates available!"),
                self.tr(
                    "There are no updates available for translations with installed "
                    "original mods."
                ),
            )

    def __update(self) -> None:
        self.__update_translations_num()

    def __update_translations_num(self) -> None:
        self.__translations_num_label.display(len(self.database.user_translations))

    def set_name_filter(self, name_filter: str, case_sensitive: bool) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (str): The name to filter by.
            case_sensitive (bool): Case sensitivity.
        """

        self.__translations_widget.set_name_filter(name_filter, case_sensitive)

    def highlight_translation(self, translation: Translation) -> None:
        """
        Highlights the specified translation by selecting it in the translations tree
        widget.

        Args:
            translation (Translation): Translation to highlight.
        """

        self.__translations_widget.highlight_translation(translation)
