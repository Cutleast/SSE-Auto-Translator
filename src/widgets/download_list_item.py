"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import webbrowser

import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

from main import MainApp
from translation_provider import TranslationDownload
from utilities import Source


class DownloadListItem(qtw.QTreeWidgetItem):
    """
    Class for download items for DownloadListDialog.
    """

    open_original_button: qtw.QPushButton = None
    translations_combobox: qtw.QComboBox = None
    open_translation_button: qtw.QPushButton = None
    files_combobox: qtw.QComboBox = None
    download_button: qtw.QPushButton = None

    def __init__(
        self, app: MainApp, name: str, translation_downloads: list[TranslationDownload]
    ):
        super().__init__(["", name, "", "", ""])

        self.app = app
        self.translation_downloads = translation_downloads

    def init_widgets(self):
        """
        Must be called after setting widgets.
        """

        self.open_original_button.clicked.connect(self.__open_original)
        self.open_translation_button.clicked.connect(self.__open_translation)

        for translation_download in self.translation_downloads:
            if translation_download.source == Source.NexusMods:
                text = f"{translation_download.name} ({translation_download.mod_id})"
                icon = qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
            else:
                text = translation_download.name
                icon = qtg.QIcon(str(self.app.data_path / "icons" / "cdt.svg"))

            self.translations_combobox.addItem(icon, text)

        self.translations_combobox.setDisabled(len(self.translation_downloads) == 1)
        self.translations_combobox.currentIndexChanged.connect(
            self.__on_translation_selected
        )
        self.__on_translation_selected()

    def __on_translation_selected(self, *args):
        translation_download = self.translation_downloads[
            self.translations_combobox.currentIndex()
        ]

        self.files_combobox.clear()

        for download in translation_download.available_downloads:
            if translation_download.source == Source.NexusMods:
                text = f"{download.name} ({download.file_id})"
            else:
                text = download.name
            self.files_combobox.addItem(text)

        self.files_combobox.setDisabled(
            len(translation_download.available_downloads) == 1
        )

    def __open_original(self):
        translation_download = self.translation_downloads[
            self.translations_combobox.currentIndex()
        ]
        modpage_url = self.app.provider.get_modpage_link(
            translation_download.original_mod.mod_id, source=Source.NexusMods
        )
        modpage_url += "?tab=files"
        webbrowser.open(modpage_url)

    def __open_translation(self):
        translation_download = self.translation_downloads[
            self.translations_combobox.currentIndex()
        ]

        modpage_url = self.app.provider.get_modpage_link(
            translation_download.mod_id, source=translation_download.source
        )
        webbrowser.open(modpage_url)
