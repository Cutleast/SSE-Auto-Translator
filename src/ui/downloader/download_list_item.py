"""
Copyright (c) Cutleast
"""

import webbrowser
from typing import Optional

from cutleast_core_lib.ui.widgets.dropdown import Dropdown
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QCheckBox, QComboBox, QPushButton, QTreeWidgetItem

from core.downloader.file_download import FileDownload
from core.downloader.translation_download import TranslationDownload
from core.translation_provider.mod_details import ModDetails
from core.translation_provider.provider import Provider
from ui.utilities.icon_provider import IconProvider, ResourceIcon


class DownloadListItem(QTreeWidgetItem, QObject):  # pyright: ignore[reportIncompatibleMethodOverride]
    """
    Class for the download item of a mod file for the download list.
    """

    toggled = Signal(bool, object)
    """
    Signal emitted when the checkbox of this item is toggled.

    Args:
        bool: Whether the checkbox is checked.
        DownloadListItem: This item.
    """

    provider: Provider

    __translation_downloads: list[TranslationDownload]

    __checkbox: QCheckBox
    __translations_combobox: QComboBox
    __open_translation_button: QPushButton
    __files_combobox: QComboBox

    def __init__(self) -> None:
        super().__init__()
        QObject.__init__(self)

    def post_init(
        self, translation_downloads: list[TranslationDownload], provider: Provider
    ) -> None:
        """
        **Must be called after adding this item to the tree widget!**

        Initializes the item's widgets and their functionality.

        Args:
            translation_downloads (list[TranslationDownload]):
                Available translations for the mod file.
            provider (Provider): Translation provider.
        """

        self.provider = provider
        self.__translation_downloads = translation_downloads

        self.__init_ui()

        self.__checkbox.stateChanged.connect(self.__on_checked_changed)
        self.__translations_combobox.currentIndexChanged.connect(
            self.__on_translation_changed
        )
        self.__open_translation_button.clicked.connect(self.__open_translation_modpage)

        for d, download in enumerate(translation_downloads):
            self.__translations_combobox.addItem(download.mod_info.display_name)
            icon: Optional[QIcon] = download.mod_info.source.get_icon()
            if icon is not None:
                self.__translations_combobox.setItemIcon(d, icon)

        self.__translations_combobox.setEnabled(
            self.__translations_combobox.count() > 1
        )
        self.__files_combobox.setEnabled(self.__files_combobox.count() > 1)

    def __init_ui(self) -> None:
        self.__checkbox = QCheckBox()
        self.__checkbox.setChecked(True)
        self.__checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.treeWidget().setItemWidget(self, 0, self.__checkbox)

        self.__translations_combobox = Dropdown()
        self.__translations_combobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.treeWidget().setItemWidget(self, 2, self.__translations_combobox)

        self.__open_translation_button = QPushButton(
            IconProvider.get_res_icon(ResourceIcon.OpenInBrowser), ""
        )
        self.__open_translation_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.__open_translation_button.setObjectName("transparent")
        self.treeWidget().setItemWidget(self, 3, self.__open_translation_button)

        self.__files_combobox = Dropdown()
        self.__files_combobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.treeWidget().setItemWidget(self, 4, self.__files_combobox)

    def __on_checked_changed(self, checked: bool) -> None:
        if checked:
            self.__translations_combobox.setEnabled(
                self.__translations_combobox.count() > 1
            )
            self.__files_combobox.setEnabled(self.__files_combobox.count() > 1)
        else:
            self.__translations_combobox.setEnabled(False)
            self.__files_combobox.setEnabled(False)
        self.__open_translation_button.setEnabled(checked)

        self.toggled.emit(checked, self)

    def __on_translation_changed(self, new_index: int) -> None:
        new_translation_download: TranslationDownload = self.__translation_downloads[
            new_index
        ]

        self.__files_combobox.clear()
        self.__files_combobox.addItems(
            [
                self.__create_file_display_name(download)
                for download in new_translation_download.available_downloads
            ]
        )
        self.__files_combobox.setEnabled(self.__files_combobox.count() > 1)

    def __create_file_display_name(self, download: FileDownload) -> str:
        details: ModDetails = download.mod_details
        return f"{details.display_name} [{details.version}] ({details.mod_id.file_id})"

    def __open_translation_modpage(self) -> None:
        current_translation_download: TranslationDownload = (
            self.__translation_downloads[self.__translations_combobox.currentIndex()]
        )

        if current_translation_download.mod_info.mod_id is not None:
            url: str = self.provider.get_modpage_url(
                mod_id=current_translation_download.mod_info.mod_id,
                source=current_translation_download.mod_info.source,
            )
            webbrowser.open(url)

    def set_checked(self, checked: bool) -> None:
        """
        Sets the checked state of this item.

        Args:
            checked (bool): Whether the item should be checked.
        """

        self.__checkbox.setChecked(checked)

    def is_checked(self) -> bool:
        """
        Returns:
            bool: Whether this item is checked.
        """

        return self.__checkbox.isChecked()

    def get_current_file_download(self) -> FileDownload:
        """
        Returns:
            FileDownload: The currently selected file download.
        """

        current_translation_download: TranslationDownload = (
            self.__translation_downloads[self.__translations_combobox.currentIndex()]
        )

        return current_translation_download.available_downloads[
            self.__files_combobox.currentIndex()
        ]

    def has_selection_options(self) -> bool:
        """
        Returns:
            bool: Whether this item has selection options (more than one translation or file).
        """

        return (
            self.__translations_combobox.count() > 1
            or self.__files_combobox.count() > 1
        )
