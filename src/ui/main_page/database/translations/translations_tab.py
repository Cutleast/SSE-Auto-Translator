"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.ui.progress.dialog import ProgressDialog
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from cutleast_core_lib.ui.widgets.error_dialog import ErrorDialog
from cutleast_core_lib.ui.widgets.lcd_number import LCDNumber
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
from core.database.database_updater import DatabaseUpdater
from core.database.translation import Translation
from core.downloader.download_manager import DownloadManager
from core.mod_file.mod_file import ModFile
from core.mod_file.mod_file_service import ModFileService
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.string.search_filter import SearchFilter
from core.string.string_extractor import StringExtractor
from core.string.types import StringList
from core.translation_provider.provider import TranslationProvider
from core.utilities.constants import SUPPORTED_ARCHIVE_TYPES
from core.utilities.exceptions import NoOriginalModFound
from core.utilities.filesystem import relative_data_path
from ui.widgets.string_list.string_list_dialog import StringListWindow
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

    __database: TranslationDatabase
    __provider: TranslationProvider
    __mod_instance: ModInstance
    __app_config: AppConfig
    __scanner: Scanner
    __download_manager: DownloadManager
    __state_service: StateService
    __database_updater: DatabaseUpdater

    __vlayout: QVBoxLayout
    __toolbar: TranslationsToolbar
    __translations_num_label: LCDNumber
    __translations_widget: TranslationsWidget

    def __init__(
        self,
        database: TranslationDatabase,
        provider: TranslationProvider,
        mod_instance: ModInstance,
        app_config: AppConfig,
        scanner: Scanner,
        download_manager: DownloadManager,
        state_service: StateService,
    ) -> None:
        """
        Args:
            database (TranslationDatabase): The translation database.
            provider (TranslationProvider): The translation provider.
            mod_instance (ModInstance): The loaded mod instance.
            app_config (AppConfig): The application configuration.
            scanner (Scanner): The scanner instance.
            download_manager (DownloadManager): The download manager instance.
            state_service (StateService): The state service instance.
        """

        super().__init__()

        self.__database = database
        self.__provider = provider
        self.__mod_instance = mod_instance
        self.__app_config = app_config
        self.__scanner = scanner
        self.__download_manager = download_manager
        self.__state_service = state_service
        self.__database_updater = DatabaseUpdater(database, mod_instance)

        self.__init_ui()

        self.__toolbar.show_vanilla_strings_requested.connect(
            self.__show_vanilla_strings
        )
        self.__toolbar.search_database_requested.connect(self.__search_database)
        self.__toolbar.local_import_requested.connect(self.__import_local_translation)
        self.__toolbar.update_translations_requested.connect(
            self.__update_translation_database
        )

        self.__translations_widget.edit_translation_requested.connect(
            self.edit_translation_requested.emit
        )
        self.__translations_widget.files_dropped.connect(self.__import_local_translation)

        self.__database.update_signal.connect(self.__update)
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
            self.__database, self.__provider, self.__mod_instance, self.__app_config
        )
        self.__vlayout.addWidget(self.__translations_widget)

    def __show_vanilla_strings(self) -> None:
        """
        Displays the vanilla strings in a StringListDialog.
        """

        WindowManager.get().show(
            StringListWindow(
                self.tr("Base Game + AE CC Content"),
                self.__database.vanilla_translation.strings,
                translation_mode=True,
            )
        )

    def __search_database(self) -> None:
        """
        Shows a string search dialog to search the database.
        """

        dialog = StringSearchDialog(QApplication.activeModalWidget())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            filter: SearchFilter = dialog.get_filter()

            search_result: dict[Path, StringList] = self.__database.search_database(
                filter
            )

            if search_result:
                WindowManager.get().show(
                    StringListWindow(
                        self.tr("Search Results"),
                        search_result,
                        translation_mode=True,
                    )
                )
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
            fdialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            fdialog.setNameFilters(
                [self.tr("Mod archive") + " (*.7z *.rar *.zip)"]
                # TODO: Add support for loose files
                # + [file_type.get_file_dialog_filter() for file_type in FileType]
            )
            fdialog.setWindowTitle(self.tr("Import Translation..."))

            if fdialog.exec() == QDialog.DialogCode.Rejected:
                return

            files = [Path(file) for file in fdialog.selectedFiles()]

        translation: Translation
        strings: dict[Path, StringList]
        for file in files:
            if file.suffix.lower() in SUPPORTED_ARCHIVE_TYPES:
                strings = ProgressDialog(
                    lambda pdisplay, f=file: StringExtractor().extract_strings(
                        input=f,
                        mod_instance=self.__mod_instance,
                        language=self.__database.language,
                        max_workers=self.__app_config.worker_thread_num,
                        pdisplay=pdisplay,
                    )
                ).run()

                if strings:
                    translation = DatabaseService.create_blank_translation(
                        file.stem, strings, self.__database
                    )
                    translation.save()
                    DatabaseService.add_translation(translation, self.__database)

            else:
                file_type_cls: type[ModFile] = ModFileService.get_modfiletype_for_suffix(
                    file.suffix
                )
                original_modfile: Optional[ModFile] = self.__mod_instance.get_modfile(
                    Path(relative_data_path(str(file))),
                    ignore_states=[
                        TranslationStatus.IsTranslated,
                        TranslationStatus.TranslationInstalled,
                    ],
                )

                if original_modfile is not None:
                    strings = {
                        original_modfile.path: StringExtractor.map_translation_strings(
                            file_type_cls(file.name, file), original_modfile
                        )
                    }

                    if strings:
                        translation = DatabaseService.create_blank_translation(
                            f"{file.name} - {self.__database.language.name}",
                            strings,
                            self.__database,
                        )
                        translation.save()
                        DatabaseService.add_translation(translation, self.__database)

                else:
                    raise NoOriginalModFound

    def __update_translation_database(self) -> None:
        """
        Updates the translation database by updating existing translations and adding
        missing mod files to existing translations.
        """

        thread_num: Optional[int] = (
            self.__app_config.worker_thread_num
            if self.__app_config.worker_thread_num > 0
            else None
        )

        scan_result: dict[ModFile, TranslationStatus] = ProgressDialog(
            lambda pdisplay: self.__database_updater.update_database_translations(
                keep_deleted=self.__app_config.keep_deleted_strings,
                add_missing_files=self.__app_config.add_missing_modfiles,
                thread_num=thread_num,
                pdisplay=pdisplay,
            )
        ).run()
        self.__state_service.set_modfile_states(scan_result)

        if scan_result:
            QMessageBox.information(
                QApplication.activeModalWidget(),
                self.tr("Database update complete"),
                self.tr(
                    "Successfully updated translations for {num} mod file(s)."
                ).format(num=len(scan_result)),
                buttons=QMessageBox.StandardButton.Ok,
            )
        else:
            QMessageBox.information(
                QApplication.activeModalWidget(),
                self.tr("Database update complete"),
                self.tr("All translations are up-to-date."),
                buttons=QMessageBox.StandardButton.Ok,
            )

    def __update(self) -> None:
        self.__update_translations_num()

    def __update_translations_num(self) -> None:
        self.__translations_num_label.display(len(self.__database.user_translations))

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
