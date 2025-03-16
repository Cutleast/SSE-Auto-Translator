"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from typing import Any, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox, QPushButton, QTreeWidgetItem

from app_context import AppContext
from core.downloader.translation_download import TranslationDownload
from core.mod_instance.mod import Mod
from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.provider import Provider
from core.translation_provider.source import Source


class DownloadListItem(QTreeWidgetItem):
    """
    Class for download items for DownloadListDialog.
    """

    open_original_button: QPushButton
    translations_combobox: QComboBox
    open_translation_button: QPushButton
    files_combobox: QComboBox
    download_button: QPushButton

    provider: Provider

    def __init__(self, name: str, translation_downloads: list[TranslationDownload]):
        super().__init__(["", name, "", "", ""])

        self.provider = AppContext.get_app().provider

        self.translation_downloads = translation_downloads

    def init_widgets(self) -> None:
        """
        Must be called after setting widgets.
        """

        self.open_original_button.clicked.connect(self.__open_original)
        self.open_translation_button.clicked.connect(self.__open_translation)

        for translation_download in self.translation_downloads:
            if translation_download.source == Source.NexusMods:
                text = f"{translation_download.name} ({translation_download.mod_id.mod_id})"
                icon = QIcon(":/icons/nexus_mods.svg")
            else:
                text = translation_download.name
                icon = QIcon(":/icons/cdt.svg")

            self.translations_combobox.addItem(icon, text)

        self.translations_combobox.setDisabled(len(self.translation_downloads) == 1)
        self.translations_combobox.currentIndexChanged.connect(
            self.__on_translation_selected
        )
        self.__on_translation_selected()

    def __on_translation_selected(self, *args: Any) -> None:
        translation_download = self.translation_downloads[
            self.translations_combobox.currentIndex()
        ]

        self.files_combobox.clear()

        for download in translation_download.available_downloads:
            if translation_download.source == Source.NexusMods:
                text = f"{download.display_name} ({download.mod_id.file_id})"
            else:
                text = download.display_name
            self.files_combobox.addItem(text)

        self.files_combobox.setDisabled(
            len(translation_download.available_downloads) == 1
        )

    def __open_original(self) -> None:
        translation_download = self.translation_downloads[
            self.translations_combobox.currentIndex()
        ]
        original_mod: Optional[Mod] = translation_download.original_mod
        if original_mod is None:
            return

        try:
            modpage_url: str = self.provider.get_modpage_url(
                original_mod.mod_id, source=Source.NexusMods
            )
            modpage_url += "?tab=files"
            os.startfile(modpage_url)
        except ModNotFoundError:
            pass

    def __open_translation(self) -> None:
        translation_download = self.translation_downloads[
            self.translations_combobox.currentIndex()
        ]

        try:
            modpage_url: str = self.provider.get_modpage_url(
                translation_download.mod_id, source=translation_download.source
            )
            os.startfile(modpage_url)
        except ModNotFoundError:
            pass
