"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp
from translation_provider import FileDownload, TranslationDownload

from .download_list_item import DownloadListItem


class DownloadListDialog(qtw.QDialog):
    """
    Dialog for download list for users that
    don't have Nexus Mods Premium.
    """

    download_items: list[DownloadListItem] = None
    
    log = logging.getLogger("DownloadList")

    def __init__(
        self,
        app: MainApp,
        translation_downloads: dict[str, list[TranslationDownload]],
        updates: bool = False,
    ):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.translation_downloads = translation_downloads
        self.updates = updates

        self.setObjectName("root")
        # self.setWindowFlags(qtc.Qt.WindowType.Window)
        self.setWindowTitle(self.mloc.download_list_title)
        self.setMinimumSize(1400, 800)
        utils.apply_dark_title_bar(self)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        title_label = qtw.QLabel(self.mloc.download_list_title)
        title_label.setObjectName("subtitle_label")
        vlayout.addWidget(title_label)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        help_label = qtw.QLabel(self.mloc.download_list_text)
        help_label.setWordWrap(True)
        hlayout.addWidget(help_label, stretch=1)

        self.download_all_button = qtw.QPushButton(self.mloc.download_all)
        self.download_all_button.setIcon(
            qta.icon("mdi.download-multiple", color="#000000")
        )
        self.download_all_button.setObjectName("accent_button")
        self.download_all_button.setDisabled(
            not app.provider.direct_downloads_possible()
        )
        self.download_all_button.clicked.connect(self.download_all)
        hlayout.addWidget(self.download_all_button)

        self.list_widget = qtw.QTreeWidget()
        self.list_widget.setSelectionMode(qtw.QTreeWidget.SelectionMode.NoSelection)
        self.list_widget.setObjectName("download_list")
        self.list_widget.setAlternatingRowColors(True)
        vlayout.addWidget(self.list_widget)

        self.list_widget.setHeaderLabels(
            [
                "",  # Modpage button for original mod
                self.mloc.original,
                self.mloc.choose_translation,
                "",  # Modpage button for translation mod
                self.mloc.choose_file,
                self.mloc.free_download,
            ]
        )
        self.list_widget.setIndentation(0)
        self.list_widget.header().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.ResizeToContents
        )
        self.list_widget.header().setSectionResizeMode(
            1, qtw.QHeaderView.ResizeMode.Stretch
        )
        self.list_widget.header().setSectionResizeMode(
            3, qtw.QHeaderView.ResizeMode.ResizeToContents
        )
        self.list_widget.header().resizeSection(5, 150)
        self.list_widget.header().setStretchLastSection(False)

        self.load_downloads()

        self.exec()

    def load_downloads(self):
        """
        Displays downloads in list with comboboxes.
        """

        self.download_items = []

        for label, translation_downloads in self.translation_downloads.items():
            item = DownloadListItem(self.app, label, translation_downloads)
            self.list_widget.addTopLevelItem(item)

            original_modpage_button = qtw.QPushButton()
            original_modpage_button.setIcon(
                qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
            )
            original_modpage_button.setToolTip(self.loc.main.open_on_nexusmods)
            self.list_widget.setItemWidget(item, 0, original_modpage_button)

            translation_combobox = qtw.QComboBox()
            translation_combobox.setEditable(False)
            self.list_widget.setItemWidget(item, 2, translation_combobox)

            translation_modpage_button = qtw.QPushButton()
            translation_modpage_button.setIcon(qta.icon("fa5s.external-link-alt", color="#ffffff"))
            translation_modpage_button.setToolTip(self.loc.main.open_modpage)
            self.list_widget.setItemWidget(item, 3, translation_modpage_button)

            files_combobox = qtw.QComboBox()
            files_combobox.setEditable(False)
            self.list_widget.setItemWidget(item, 4, files_combobox)

            download_button = qtw.QPushButton(self.mloc.download + "  ")
            download_button.setObjectName("download_button")
            download_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
            download_button.setFixedWidth(150)
            self.list_widget.setItemWidget(item, 5, download_button)

            item.open_original_button = original_modpage_button
            item.translations_combobox = translation_combobox
            item.open_translation_button = translation_modpage_button
            item.files_combobox = files_combobox
            item.download_button = download_button

            item.init_widgets()
            self.download_items.append(item)

        self.list_widget.header().setStretchLastSection(False)
        self.list_widget.header().setSectionResizeMode(
            1, qtw.QHeaderView.ResizeMode.Stretch
        )
        self.list_widget.resizeColumnToContents(1)
        self.list_widget.resizeColumnToContents(2)
        self.list_widget.resizeColumnToContents(4)

    def download_all(self):
        """
        Closes dialog and starts all downloads.
        """

        _queue: set[FileDownload] = set()

        for download_item in self.download_items:
            translation_download = download_item.translation_downloads[
                download_item.translations_combobox.currentIndex()
            ]
            download = translation_download.available_downloads[
                download_item.files_combobox.currentIndex()
            ]

            if download in _queue:
                continue

            download.direct_url = self.app.provider.get_direct_download_url(
                download.mod_id, download.file_id, source=translation_download.source
            )

            # if self.updates:
            #     old_translation = self.app.database.get_translation_by_id(
            #         mod_id,
            #         int(self.translation_downloads[rindex].original_plugin_name),
            #     )
            #     if old_translation is not None:
            #         self.app.database.delete_translation(old_translation)
            #         self.log.info("Deleted old Translation from Database.")
            #     else:
            #         self.log.warning(
            #             "Old Translation could not be found in Database!"
            #         )

            item = qtw.QTreeWidgetItem(
                [
                    download.name,
                    self.app.loc.main.waiting_for_download,
                ]
            )
            item.setFont(1, qtg.QFont("Consolas"))
            download.tree_item = item
            self.app.mainpage_widget.database_widget.downloads_widget.downloads_widget.addTopLevelItem(
                item
            )
            self.app.mainpage_widget.database_widget.downloads_widget.queue.put(
                download
            )
            _queue.add(download)

        self.app.mainpage_widget.update_modlist()

        if self.list_widget.topLevelItemCount():
            self.app.mainpage_widget.database_widget.downloads_widget.queue_finished.connect(
                self.app.mainpage_widget.database_widget.downloads_widget.all_finished
            )

        self.close()
