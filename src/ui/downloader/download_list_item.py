"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import webbrowser
from typing import Any, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox, QPushButton, QTreeWidgetItem

from core.downloader.translation_download import TranslationDownload
from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.mod_id import ModId
from core.translation_provider.provider import Provider
from core.translation_provider.source import Source


class DownloadListItem(QTreeWidgetItem):
    """
    Class for download items for DownloadListDialog.
    """

    original_mod_id: ModId
    open_original_button: QPushButton
    translations_combobox: QComboBox
    open_translation_button: QPushButton
    files_combobox: QComboBox
    download_button: QPushButton

    provider: Provider

    def __init__(
        self,
        name: str,
        original_mod_id: ModId,
        translation_downloads: list[TranslationDownload],
        provider: Provider,
    ) -> None:
        super().__init__(["", name, "", "", ""])

        self.original_mod_id = original_mod_id
        self.translation_downloads = translation_downloads
        self.provider = provider

    def init_widgets(self) -> None:
        """
        Must be called after setting widgets.
        """

        self.open_original_button.clicked.connect(self.__open_original)
        self.open_translation_button.clicked.connect(self.__open_translation)

        for translation_download in self.translation_downloads:
            if translation_download.source == Source.NexusMods:
                text = f"{translation_download.name} ({translation_download.mod_id.mod_id})"
            else:
                text = translation_download.name

            icon: Optional[QIcon] = translation_download.source.get_icon()
            if icon is not None:
                self.translations_combobox.addItem(icon, text)
            else:
                self.translations_combobox.addItem(text)

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
        try:
            modpage_url: str = self.provider.get_modpage_url(
                self.original_mod_id, source=Source.NexusMods
            )
            modpage_url += "?tab=files"
            webbrowser.open(modpage_url)
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
            webbrowser.open(modpage_url)
        except ModNotFoundError:
            pass
