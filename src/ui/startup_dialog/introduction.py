"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .startup_dialog import StartupDialog


class IntroductionPage(QWidget):
    """
    First page. Informs user about further steps
    and usage of this application.
    """

    def __init__(self, startup_dialog: StartupDialog):
        super().__init__()

        self.startup_dialog = startup_dialog
        self.loc = startup_dialog.loc
        self.mloc = startup_dialog.mloc

        self.setObjectName("primary")

        vlayout = QVBoxLayout()
        vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(vlayout)

        # Title label
        title_label = QLabel(self.mloc.startup)
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        vlayout.addSpacing(50)

        # Info label
        info_label = QLabel(self.mloc.introduction)
        vlayout.addWidget(info_label)

        # Documentation button
        documentation_button = QPushButton(
            self.loc.main.show_documentation + " (Offline)"
        )
        documentation_button.clicked.connect(self.startup_dialog.app.show_documentation)
        vlayout.addWidget(documentation_button)

        documentation_button = QPushButton(
            self.loc.main.show_documentation + " (Browser)"
        )
        documentation_button.clicked.connect(
            lambda: os.startfile(
                "https://github.com/Cutleast/SSE-Auto-Translator/blob/master/doc/Instructions_en_US.md"
            )
        )
        vlayout.addWidget(documentation_button)

        vlayout.addSpacing(50)

        # Path Limit
        path_limit_label = QLabel(self.mloc.path_limit)
        path_limit_label.setWordWrap(True)
        vlayout.addWidget(path_limit_label)

        fix_button = QPushButton(self.loc.main.fix_path_limit)

        def fix_path_limit():
            try:
                os.startfile(self.startup_dialog.app.res_path / "path_limit.reg")
            except OSError:
                pass

        fix_button.clicked.connect(fix_path_limit)
        vlayout.addWidget(fix_button)

        vlayout.addStretch()

        # Exit and Next Button
        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.exit_button = QPushButton()
        self.exit_button.setIcon(qta.icon("fa.close", color="#ffffff"))
        self.exit_button.setText(self.loc.main.exit)
        self.exit_button.clicked.connect(
            lambda: (self.startup_dialog.close(), self.startup_dialog.app.exit())
        )
        hlayout.addWidget(self.exit_button, 0, Qt.AlignmentFlag.AlignLeft)

        hlayout.addStretch()

        self.next_button = QPushButton()
        self.next_button.setIcon(qta.icon("fa5s.chevron-right", color="#ffffff"))
        self.next_button.setText(self.loc.main.next)
        self.next_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.next_button.clicked.connect(self.startup_dialog.page_widget.slideInNext)
        hlayout.addWidget(self.next_button)
