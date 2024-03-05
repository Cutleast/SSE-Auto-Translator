"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os

import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp

from .updater import Updater


class UpdaterDialog(qtw.QDialog):
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

        utils.apply_dark_title_bar(self)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        title_label = qtw.QLabel(self.mloc.update_available)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        version_label = qtw.QLabel(
            f"\
{self.mloc.installed_version}: {updater.installed_version} \
{self.mloc.latest_version}: {updater.latest_version}"
        )
        version_label.setObjectName("relevant_label")
        vlayout.addWidget(version_label)

        changelog_box = qtw.QTextBrowser()
        changelog_box.setMarkdown(updater.get_changelog())
        changelog_box.setCurrentFont(qtg.QFont("Arial"))
        vlayout.addWidget(changelog_box, 1)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.cancel_button = qtw.QPushButton(self.mloc.ignore_update)
        self.cancel_button.clicked.connect(self.accept)
        hlayout.addWidget(self.cancel_button)

        hlayout.addStretch()

        download_button = qtw.QPushButton(self.mloc.download_update)
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
