"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from app import MainApp
from core.utilities import apply_dark_title_bar
from core.utilities.updater import Updater


class UpdaterDialog(QDialog):
    """
    Class for updater dialog.
    """

    def __init__(self, app: MainApp, updater: Updater):
        super().__init__(app.root)

        self.app = app
        self.updater = updater

        self.loc = app.loc
        self.mloc = app.loc.updater
        self.log = updater.log

        apply_dark_title_bar(self)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        title_label = QLabel(self.mloc.update_available)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        version_label = QLabel(
            f"\
{self.mloc.installed_version}: {updater.installed_version} \
{self.mloc.latest_version}: {updater.latest_version}"
        )
        version_label.setObjectName("relevant_label")
        vlayout.addWidget(version_label)

        changelog_box = QTextBrowser()
        changelog_box.setMarkdown(updater.get_changelog())
        changelog_box.setCurrentFont(QFont("Arial"))
        vlayout.addWidget(changelog_box, 1)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.cancel_button = QPushButton(self.mloc.ignore_update)
        self.cancel_button.clicked.connect(self.accept)
        hlayout.addWidget(self.cancel_button)

        hlayout.addStretch()

        download_button = QPushButton(self.mloc.download_update)
        download_button.clicked.connect(
            lambda: (
                os.startfile(updater.download_url),
                self.accept(),
            )
        )
        hlayout.addWidget(download_button)

        self.show()
        self.resize(700, 400)
        self.exec()
