"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from PySide6.QtWidgets import QTabWidget

from app import MainApp

from .downloads_widget import DownloadsWidget
from .translations_widget import TranslationsWidget


class DatabaseWidget(QTabWidget):
    """
    Widget for translation database and download list.
    """

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.tabBar().setDocumentMode(True)

        self.translations_widget = TranslationsWidget(app)
        self.translations_widget.load_translations()
        self.addTab(self.translations_widget, self.mloc.translations)

        self.downloads_widget = DownloadsWidget(app)
        self.addTab(self.downloads_widget, self.mloc.downloads)

        self.downloads_widget.download_finished.connect(
            self.translations_widget.load_translations
        )
