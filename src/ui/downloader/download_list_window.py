"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.ui.theme.manager import ThemeManager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from core.downloader.download_manager import DownloadListEntries
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import TranslationProvider

from .download_list_widget import DownloadListWidget


class DownloadListWindow(DownloadListWidget):
    """
    Window wrapper of the download list widget with added event handling.
    """

    @override
    def __init__(
        self,
        entries: DownloadListEntries,
        provider: TranslationProvider,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(entries, provider, parent)

        self.setObjectName("root")
        self.setWindowTitle(self.tr("Available downloads"))
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.resize(1400, 800)

    @override
    def _on_start_button_clicked(self) -> None:
        super()._on_start_button_clicked()

        self.close()

        if self._link_nxm_checkbox.isChecked():
            NXMHandler.get().bind()

        if (
            not self._provider.direct_downloads_possible()
            and not NXMHandler.get().is_bound()
        ):
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
            messagebox.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            ThemeManager.update_widget_styles(messagebox)

            if messagebox.exec() == QMessageBox.StandardButton.Yes:
                NXMHandler.get().bind()
