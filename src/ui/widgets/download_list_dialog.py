"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.

# TODO: Move this and DownloadListItem to their own module in ui.downloader
"""

import logging
from typing import Optional, override

import qtawesome as qta
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QIcon, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)
from qtpy.QtWidgets import QMessageBox

from app_context import AppContext
from core.database.database import TranslationDatabase
from core.downloader.download_manager import DownloadManager
from core.downloader.file_download import FileDownload
from core.downloader.translation_download import TranslationDownload
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.utilities.container_utils import unique

from .download_list_item import DownloadListItem
from .loading_dialog import LoadingDialog


class DownloadListDialog(QDialog):
    """
    Dialog for download list for users that
    don't have Nexus Mods Premium.
    """

    log: logging.Logger = logging.getLogger("DownloadList")

    download_items: list[DownloadListItem]

    provider: Provider
    database: TranslationDatabase
    download_manager: DownloadManager

    def __init__(
        self,
        translation_downloads: dict[str, list[TranslationDownload]],
        updates: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.provider = AppContext.get_app().provider
        self.database = AppContext.get_app().database
        self.download_manager = AppContext.get_app().download_manager

        self.translation_downloads = translation_downloads
        self.updates = updates

        self.setObjectName("root")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setModal(False)
        self.setWindowTitle(self.tr("Translation Downloads"))
        self.setMinimumSize(1400, 800)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        title_label = QLabel(self.tr("Translation Downloads"))
        title_label.setObjectName("subtitle_label")
        vlayout.addWidget(title_label)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        help_label = QLabel(
            self.tr(
                "Below are the Translations that are required and available online. "
                "Choose desired translations where appropiate and click "
                'on "Download all".\n'
                "If you don't have Nexus Mods Premium, make sure that SSE-AT "
                "is linked to Mod Manager Downloads "
                "(link button is in Translations panel)"
            )
        )
        help_label.setWordWrap(True)
        hlayout.addWidget(help_label, stretch=1)

        self.download_all_button = QPushButton(self.tr("Start all downloads"))
        self.download_all_button.setIcon(
            qta.icon("mdi.download-multiple", color="#000000")
        )
        self.download_all_button.setObjectName("accent_button")
        self.download_all_button.clicked.connect(self.__download_all)
        hlayout.addWidget(self.download_all_button)

        self.list_widget = QTreeWidget()
        self.list_widget.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.list_widget.setObjectName("download_list")
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.header().setSectionsMovable(False)
        vlayout.addWidget(self.list_widget)

        self.list_widget.setHeaderLabels(
            [
                "",  # Modpage button for original mod
                self.tr("Original"),
                self.tr("Choose translation"),
                "",  # Modpage button for translation mod
                self.tr("Choose translation file"),
            ]
        )
        self.list_widget.setIndentation(0)

        self.__load_downloads()

        self.list_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.list_widget.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.list_widget.header().resizeSection(2, 400)
        self.list_widget.header().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.list_widget.header().resizeSection(4, 400)
        self.list_widget.header().setStretchLastSection(False)

    def __load_downloads(self) -> None:
        """
        Displays downloads in list with comboboxes.
        """

        self.download_items = []

        for label, translation_download in self.translation_downloads.items():
            item = DownloadListItem(label, translation_download)
            self.list_widget.addTopLevelItem(item)

            # TODO: Move this part to DownloadListItem
            original_modpage_button = QPushButton()
            original_modpage_button.setIcon(QIcon(":/icons/nexus_mods.svg"))
            original_modpage_button.setToolTip(
                self.tr("Open mod page on Nexus Mods...")
            )
            self.list_widget.setItemWidget(item, 0, original_modpage_button)

            translation_combobox = QComboBox()
            translation_combobox.installEventFilter(self)
            translation_combobox.setEditable(False)
            self.list_widget.setItemWidget(item, 2, translation_combobox)

            translation_modpage_button = QPushButton()
            translation_modpage_button.setIcon(
                qta.icon("fa5s.external-link-alt", color="#ffffff")
            )
            translation_modpage_button.setToolTip(
                self.tr("Open translation on Nexus Mods...")
            )
            self.list_widget.setItemWidget(item, 3, translation_modpage_button)

            files_combobox = QComboBox()
            files_combobox.installEventFilter(self)
            files_combobox.setEditable(False)
            self.list_widget.setItemWidget(item, 4, files_combobox)

            item.open_original_button = original_modpage_button
            item.translations_combobox = translation_combobox
            item.open_translation_button = translation_modpage_button
            item.files_combobox = files_combobox

            item.init_widgets()
            self.download_items.append(item)

        self.list_widget.header().setStretchLastSection(False)
        self.list_widget.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.list_widget.resizeColumnToContents(1)
        self.list_widget.resizeColumnToContents(2)
        self.list_widget.resizeColumnToContents(4)

    def __download_all(self) -> None:
        """
        Closes dialog and starts all downloads.
        """

        _downloads: list[FileDownload] = []

        def process(ldialog: LoadingDialog) -> None:
            ldialog.updateProgress(text1=self.tr("Starting downloads..."))

            for d, download_item in enumerate(self.download_items):
                try:
                    translation_download = download_item.translation_downloads[
                        download_item.translations_combobox.currentIndex()
                    ]
                    download = translation_download.available_downloads[
                        download_item.files_combobox.currentIndex()
                    ]

                    ldialog.updateProgress(
                        text1=f"{self.tr('Starting downloads...')} {d}/{len(self.download_items)}",
                        value1=d,
                        max1=len(self.download_items),
                        show2=True,
                        text2=download.display_name,
                    )

                    _downloads.append(download)

                    if self.updates:
                        old_translation = self.database.get_translation_by_modfile_name(
                            translation_download.modfile_name
                        )
                        if old_translation is not None:
                            self.database.delete_translation(old_translation)
                            self.log.info("Deleted old Translation from Database.")
                        else:
                            self.log.warning(
                                "Old Translation could not be found in Database!"
                            )
                except Exception as ex:
                    self.log.error(
                        "Failed to start "
                        f"{download_item.translations_combobox.currentText()!r} > "
                        f"{download_item.files_combobox.currentText()!r}: {ex}",
                        exc_info=ex,
                    )

        LoadingDialog.run_callable(self, process)

        for download in unique(_downloads):
            self.download_manager.request_download(download)

        self.download_manager.start()
        self.close()

        nxm_handler: NXMHandler = AppContext.get_app().nxm_listener
        if not self.provider.direct_downloads_possible() and not nxm_handler.is_bound():
            messagebox = QMessageBox(QApplication.activeModalWidget())
            messagebox.setWindowTitle(self.tr("Link to Mod Manager downloads?"))
            messagebox.setText(
                self.tr(
                    "You don't have Nexus Mods Premium and direct downloads are "
                    'not possible. Do you want to link to the "Mod Manager Download"'
                    "buttons on Nexus Mods now?"
                )
            )
            messagebox.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            messagebox.setDefaultButton(QMessageBox.StandardButton.Yes)
            messagebox.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            messagebox.button(QMessageBox.StandardButton.Yes).setObjectName(
                "accent_button"
            )
            messagebox.button(QMessageBox.StandardButton.No).setText(self.tr("No"))

            if messagebox.exec() == QMessageBox.StandardButton.Yes:
                nxm_handler.bind()

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and isinstance(source, QComboBox)
            and isinstance(event, QWheelEvent)
        ):
            self.list_widget.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
