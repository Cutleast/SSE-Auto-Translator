"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

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

    def __init__(self, app: MainApp, downloads: list[utils.Download]):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.downloads = downloads

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
        self.download_all_button.setIcon(qta.icon("mdi.download-multiple", color="#ffffff"))
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
                self.mloc.original,
                self.mloc.choose_translation,
                self.mloc.choose_file,
                self.mloc.download,
            ]
        )
        self.list_widget.header().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.Stretch
        )
        self.list_widget.header().resizeSection(1, 200)
        self.list_widget.header().setStretchLastSection(False)

        self.load_downloads()

        self.show()

    def load_downloads(self):
        """
        Displays downloads in list with comboboxes.
        """

        for download in self.downloads:
            item = qtw.QTreeWidgetItem(
                [
                    f"{download.original_mod_name} > {download.original_plugin_name}",
                    "",  # Translation Combobox
                    "",  # File Combobox
                    "",  # Download Button
                ]
            )
            self.list_widget.addTopLevelItem(item)

            translation_combobox = qtw.QComboBox()
            translation_combobox.setEditable(False)
            translations = [
                f"{self.app.api.get_modname_of_id('skyrimspecialedition', mod_id)} ({mod_id})"
                for mod_id in download.available_translations
            ]
            translation_combobox.addItems(translations)
            translation_combobox.setDisabled(len(translations) == 1)
            self.list_widget.setItemWidget(item, 1, translation_combobox)

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

            self.list_widget.setItemWidget(item, 2, files_combobox)

            download_button = qtw.QPushButton(self.mloc.download + "  ")
            download_button.setObjectName("download_button")
            download_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
            download_button.setFixedWidth(150)

            def get_func(tcb, fcb, btn):
                translation_combobox = tcb
                files_combobox = fcb
                download_button = btn

                def start_download():
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
                )
            )

            self.list_widget.setItemWidget(item, 3, download_button)

        self.list_widget.header().setStretchLastSection(False)
        self.list_widget.header().setSectionResizeMode(0, qtw.QHeaderView.ResizeMode.Stretch)
        self.list_widget.resizeColumnToContents(0)
        self.list_widget.resizeColumnToContents(1)
        self.list_widget.resizeColumnToContents(2)
        self.list_widget.resizeColumnToContents(3)
        # self.list_widget.header().setSectionResizeMode(4, qtw.QHeaderView.ResizeMode.Fixed)
        # self.list_widget.header().resizeSection(4, self.download_all_button.width())

    def download_all(self):
        """
        Closes dialog and starts all downloads.
        """

        from database import Translation

        for rindex in range(self.list_widget.topLevelItemCount()):
            item = self.list_widget.itemFromIndex(
                self.list_widget.model().index(rindex, 0)
            )

            translation_combobox: qtw.QComboBox = self.list_widget.itemWidget(item, 1)
            files_combobox: qtw.QComboBox = self.list_widget.itemWidget(item, 2)

            mod_id = int(translation_combobox.currentText().rsplit("(", 1)[1][:-1])
            file_id = int(files_combobox.currentText().rsplit("(", 1)[1][:-1])

            translation_name = files_combobox.currentText().rsplit("(", 1)[0].strip()

            translation = Translation(
                translation_name,
                mod_id,
                file_id,
                self.app.api.get_mod_details("skyrimspecialedition", mod_id)["version"],
                original_mod_id=0,
                original_file_id=0,
                original_version="0",
                path=self.app.database.userdb_path
                / self.app.database.language
                / translation_name,
            )

            item = qtw.QTreeWidgetItem(
                [
                    translation_name,
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

        if self.list_widget.topLevelItemCount():
            self.app.mainpage_widget.database_widget.downloads_widget.queue_finished.connect(
                self.app.mainpage_widget.database_widget.downloads_widget.all_finished
            )

        self.close()
