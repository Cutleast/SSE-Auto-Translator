"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp


class DownloadListDialog(qtw.QWidget):
    """
    Dialog for download list for users that
    don't have Nexus Mods Premium.
    """

    log = logging.getLogger("DownloadList")

    def __init__(
        self, app: MainApp, downloads: list[utils.Download], updates: bool = False
    ):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.downloads = downloads
        self.updates = updates

        self.setObjectName("root")
        self.setWindowFlags(qtc.Qt.WindowType.Window)
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
        self.download_all_button.setDisabled(not app.api.premium)
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

        self.show()

    def load_downloads(self):
        """
        Displays downloads in list with comboboxes.
        """

        for download in self.downloads:
            if self.updates:
                original_label = download.original_mod_name
            else:
                original_label = (
                    f"{download.original_mod_name} > {download.original_plugin_name}"
                )

            item = qtw.QTreeWidgetItem(
                [
                    "",  # Modpage button for original mod
                    original_label,
                    "",  # Translation Combobox
                    "",  # Modpage button for translation
                    "",  # File Combobox
                    "",  # Download Button
                ]
            )
            self.list_widget.addTopLevelItem(item)

            modpage_button = qtw.QPushButton()
            modpage_button.setIcon(
                qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
            )
            modpage_button.setToolTip(self.loc.main.open_on_nexusmods)

            def get_func(mod_id):
                def open_modpage():
                    url = utils.create_nexus_mods_url("skyrimspecialedition", mod_id)
                    url += "?tab=files"
                    os.startfile(url)

                return open_modpage

            modpage_button.clicked.connect(get_func(download.original_mod_id))
            self.list_widget.setItemWidget(item, 0, modpage_button)

            translation_combobox = qtw.QComboBox()
            translation_combobox.setEditable(False)
            translations = [
                f"{self.app.api.get_modname_of_id('skyrimspecialedition', mod_id)} ({mod_id})"
                for mod_id in download.available_translations
            ]
            translation_combobox.addItems(translations)
            translation_combobox.setDisabled(len(translations) == 1)
            self.list_widget.setItemWidget(item, 2, translation_combobox)

            modpage_button = qtw.QPushButton()
            modpage_button.setIcon(
                qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
            )
            modpage_button.setToolTip(self.loc.main.open_on_nexusmods)

            def get_func(tcb):
                translation_combobox = tcb

                def open_modpage():
                    translation_name = translation_combobox.currentText()
                    translation_id = int(translation_name.rsplit("(", 1)[1][:-1])
                    url = utils.create_nexus_mods_url(
                        "skyrimspecialedition", translation_id
                    )
                    url += "?tab=files"
                    os.startfile(url)

                return open_modpage

            modpage_button.clicked.connect(get_func(translation_combobox))
            self.list_widget.setItemWidget(item, 3, modpage_button)

            files_combobox = qtw.QComboBox()
            files_combobox.setEditable(False)

            def get_func(tcb, fcb, dl):
                translation_combobox = tcb
                files_combobox = fcb
                download = dl

                def on_translation_select(*args):
                    translation_name = translation_combobox.currentText()
                    translation_id = int(translation_name.rsplit("(", 1)[1][:-1])

                    filenames = [
                        f"{self.app.api.get_filename_of_id('skyrimspecialedition', translation_id, file_id)} ({file_id})"
                        for file_id in download.available_translation_files[
                            translation_id
                        ]
                    ]
                    files_combobox.clear()
                    files_combobox.addItems(filenames)
                    files_combobox.setCurrentIndex(
                        download.available_translation_files[translation_id].index(
                            max(  # Preselect translation file with newest upload timestamp
                                download.available_translation_files[translation_id],
                                key=lambda file_id: self.app.api.get_timestamp_of_file(
                                    "skyrimspecialedition", translation_id, file_id
                                ),
                            )
                        )
                    )

                    files_combobox.setDisabled(len(filenames) == 1)

                return on_translation_select

            translation_combobox.currentIndexChanged.connect(
                get_func(translation_combobox, files_combobox, download)
            )
            translation_combobox.currentTextChanged.connect(
                get_func(translation_combobox, files_combobox, download)
            )
            translation_combobox.setCurrentIndex(
                download.available_translations.index(
                    max(  # Preselect translation with newest update timestamp
                        download.available_translations,
                        key=lambda mod_id: self.app.api.get_mod_details(
                            "skyrimspecialedition", mod_id
                        )["updated_timestamp"],
                    )
                )
            )
            get_func(translation_combobox, files_combobox, download)()

            self.list_widget.setItemWidget(item, 4, files_combobox)

            download_button = qtw.QPushButton(self.mloc.download + "  ")
            download_button.setObjectName("download_button")
            download_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
            download_button.setFixedWidth(150)

            def get_func(tcb, fcb, btn, dl):
                translation_combobox = tcb
                files_combobox = fcb
                download_button = btn
                download = dl

                def start_download():
                    if self.updates:
                        old_translation = self.app.database.get_translation_by_id(
                            mod_id, int(download.original_plugin_name)
                        )
                        if old_translation is not None:
                            self.app.database.delete_translation(old_translation)
                            self.app.log.info("Deleted old Translation from Database.")
                        else:
                            self.app.log.warning(
                                "Old Translation could not be found in Database!"
                            )

                        self.app.mainpage_widget.update_modlist()

                    mod_id = int(
                        translation_combobox.currentText().rsplit("(", 1)[1][:-1]
                    )
                    file_id = int(files_combobox.currentText().rsplit("(", 1)[1][:-1])

                    url = utils.create_nexus_mods_url(
                        "skyrimspecialedition",
                        mod_id,
                        file_id,
                        mod_manager=True,
                    )

                    os.startfile(url)
                    download_button.setIcon(qta.icon("fa5s.check", color="#ffffff"))

                return start_download

            download_button.clicked.connect(
                get_func(
                    translation_combobox,
                    files_combobox,
                    download_button,
                    download,
                )
            )
            download_button.setDisabled(self.app.api.premium)

            self.list_widget.setItemWidget(item, 5, download_button)

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

        from database import Translation

        download_files: list[tuple[int, int]] = []

        download_translations: list[Translation] = []

        for rindex in range(self.list_widget.topLevelItemCount()):
            item = self.list_widget.itemFromIndex(
                self.list_widget.model().index(rindex, 0)
            )

            translation_combobox: qtw.QComboBox = self.list_widget.itemWidget(item, 2)
            files_combobox: qtw.QComboBox = self.list_widget.itemWidget(item, 4)

            mod_id = int(translation_combobox.currentText().rsplit("(", 1)[1][:-1])
            file_id = int(files_combobox.currentText().rsplit("(", 1)[1][:-1])

            if (mod_id, file_id) not in download_files:
                translation_name = (
                    files_combobox.currentText().rsplit("(", 1)[0].strip()
                )

                if self.updates:
                    old_translation = self.app.database.get_translation_by_id(
                        mod_id, int(self.downloads[rindex].original_plugin_name)
                    )
                    if old_translation is not None:
                        self.app.database.delete_translation(old_translation)
                        self.log.info("Deleted old Translation from Database.")
                    else:
                        self.log.warning(
                            "Old Translation could not be found in Database!"
                        )

                translation = Translation(
                    translation_name,
                    mod_id,
                    file_id,
                    self.app.api.get_mod_details("skyrimspecialedition", mod_id)[
                        "version"
                    ],
                    original_mod_id=0,
                    original_file_id=0,
                    original_version="0",
                    path=self.app.database.userdb_path
                    / self.app.database.language
                    / translation_name,
                )
                download_translations.append(translation)

        self.app.mainpage_widget.update_modlist()

        for translation in download_translations:
            item = qtw.QTreeWidgetItem(
                [
                    translation.name,
                    self.app.loc.main.waiting_for_download,
                ]
            )
            translation.tree_item = item
            self.app.mainpage_widget.database_widget.downloads_widget.downloads_widget.addTopLevelItem(
                item
            )
            self.app.mainpage_widget.database_widget.downloads_widget.queue.put(
                translation
            )

            download_files.append((mod_id, file_id))

        if self.list_widget.topLevelItemCount():
            self.app.mainpage_widget.database_widget.downloads_widget.queue_finished.connect(
                self.app.mainpage_widget.database_widget.downloads_widget.all_finished
            )

        self.close()
