"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from core.utilities.updater import Updater


class UpdaterDialog(QDialog):
    """
    Class for updater dialog.
    """

    def __init__(self, updater: Updater):
        super().__init__(QApplication.activeModalWidget())

        self.updater = updater

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        title_label = QLabel(self.tr("An Update is available to download!"))
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        version_label = QLabel(
            f"\
{self.tr("Installed Version")}: {updater.installed_version} \
{self.tr("Latest Version")}: {updater.latest_version}"
        )
        version_label.setObjectName("relevant_label")
        vlayout.addWidget(version_label)

        changelog_box = QTextBrowser()
        changelog_box.setMarkdown(updater.get_changelog())
        changelog_box.setCurrentFont(QFont("Arial"))
        vlayout.addWidget(changelog_box, 1)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.cancel_button = QPushButton(self.tr("Ignore Update"))
        self.cancel_button.clicked.connect(self.accept)
        hlayout.addWidget(self.cancel_button)

        hlayout.addStretch()

        download_button = QPushButton(self.tr("Download Update"))
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
