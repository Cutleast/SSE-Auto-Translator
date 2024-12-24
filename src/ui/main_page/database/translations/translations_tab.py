"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.database.database import TranslationDatabase
from core.database.search_filter import SearchFilter
from core.database.string import String
from core.database.translation import Translation
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from ui.widgets.error_dialog import ErrorDialog
from ui.widgets.lcd_number import LCDNumber
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.string_list_dialog import StringListDialog
from ui.widgets.string_search_dialog import StringSearchDialog

from .translations_toolbar import TranslationsToolbar
from .translations_widget import TranslationsWidget


class TranslationsTab(QWidget):
    """
    Tab for Translations Database.
    """

    database: TranslationDatabase
    provider: Provider
    nxm_listener: NXMHandler

    __vlayout: QVBoxLayout
    __toolbar: TranslationsToolbar
    __translations_num_label: LCDNumber
    __translations_widget: TranslationsWidget

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        AppContext.get_app().ready_signal.connect(self.__post_init)

    def __post_init(self) -> None:
        self.database = AppContext.get_app().database
        self.provider = AppContext.get_app().provider
        self.nxm_listener = AppContext.get_app().nxm_listener

        # Highlight NXM button if the user has no Premium
        if not self.provider.direct_downloads_possible():
            self.__toolbar.handle_nxm_action.setObjectName("accent_button")

        AppContext.get_app().timer_signal.connect(self.__check_nxm_link)
        self.__update()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_translations_widget()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__toolbar = TranslationsToolbar(self)
        hlayout.addWidget(self.__toolbar)

        hlayout.addStretch()

        translations_num_label = QLabel(self.tr("Translations:"))
        translations_num_label.setObjectName("relevant_label")
        hlayout.addWidget(translations_num_label)

        self.__translations_num_label = LCDNumber()
        self.__translations_num_label.setDigitCount(4)
        hlayout.addWidget(self.__translations_num_label)

    def __init_translations_widget(self) -> None:
        self.__translations_widget = TranslationsWidget()
        self.__vlayout.addWidget(self.__translations_widget)

    def show_vanilla_strings(self) -> None:
        """
        Displays the vanilla strings in a StringListDialog.
        """

        StringListDialog(
            self.tr("Base Game + AE CC Content"),
            self.database.vanilla_translation.strings,
            show_translation=True,
        ).show()

    def search_database(self) -> None:
        """
        Shows a string search dialog to search the database.
        """

        dialog = StringSearchDialog(QApplication.activeModalWidget())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            filter: SearchFilter = dialog.get_filter()

            search_result: dict[str, list[String]] = self.database.search_database(
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
                        'Click on "Show Details" to view used filter.'
                    ),
                    details=str(filter),
                    yesno=False,
                ).exec()

    def import_local_translation(self, files: Optional[list[Path]] = None) -> None:
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
                    self.tr("Mod Archive (*.7z *.rar *.zip)"),
                    # TODO: Reimplement this
                    # self.tr("Bethesda Plugin (*.esp *.esm *.esl)"),
                ]
            )
            fdialog.setWindowTitle(self.tr("Import Translation..."))

            if fdialog.exec() == QDialog.DialogCode.Rejected:
                return

            files = [Path(file) for file in fdialog.selectedFiles()]

        for file in files:
            if file.suffix.lower() in [".7z", ".rar", ".zip"]:
                strings: dict[str, list[String]] = LoadingDialog.run_callable(
                    QApplication.activeModalWidget(),
                    lambda ldialog: self.database.importer.extract_strings_from_archive(
                        file, ldialog
                    ),
                )

                if strings:
                    translation: Translation = self.database.create_blank_translation(
                        file.stem, strings
                    )
                    translation.save_translation()
                    self.database.add_translation(translation)

    def check_for_updates(self) -> None: ...

    def download_updates(self) -> None: ...

    def toggle_nxm(self) -> None: ...

    def __update(self) -> None:
        self.__update_translations_num()

    def __check_nxm_link(self) -> None:
        self.__toolbar.handle_nxm_action.setChecked(self.nxm_listener.is_bound())

    def __update_translations_num(self) -> None:
        self.__translations_num_label.display(len(self.database.user_translations))

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.__translations_widget.set_name_filter(name_filter)
