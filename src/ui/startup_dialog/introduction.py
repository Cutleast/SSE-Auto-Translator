"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path

from PySide6.QtWidgets import QLabel, QPushButton

from app_context import AppContext
from ui.startup_dialog.page import Page


class IntroductionPage(Page):
    """
    First page. Informs user about further steps
    and usage of this application.
    """

    def __init__(self) -> None:
        super().__init__()

        self._back_button.setText("Exit")
        self.valid_signal.emit(True)

    def _get_title(self) -> str:
        return self.tr("Welcome!")

    def _get_description(self) -> str:
        return self.tr(
            "This Guide will help you setting up this Tool for your modlist."
        )

    def _init_form(self) -> None:
        documentation_button = QPushButton(self.tr("Open Documentation (Offline)"))
        documentation_button.clicked.connect(self.__show_documentation)
        self._vlayout.addWidget(documentation_button)

        documentation_button = QPushButton(self.tr("Open Documentation (Browser)"))
        documentation_button.clicked.connect(
            lambda: os.startfile(
                "https://github.com/Cutleast/SSE-Auto-Translator/blob/master/doc/Instructions_en_US.md"
            )
        )
        self._vlayout.addWidget(documentation_button)

        self._vlayout.addSpacing(50)

        # Path Limit
        path_limit_label = QLabel(
            self.tr(
                "Windows has a length limit of 255 characters for paths. "
                "Click below, grant admin rights and reboot to disable it."
            )
        )
        path_limit_label.setWordWrap(True)
        self._vlayout.addWidget(path_limit_label)

        fix_button = QPushButton(self.tr("Fix Windows Path Limit"))
        fix_button.clicked.connect(self.__fix_path_limit)
        self._vlayout.addWidget(fix_button)

        self._vlayout.addStretch()

    def _validate(self) -> None:
        return None

    def get_values(self) -> None:
        return None

    def __show_documentation(self) -> None:
        exe_path: str = AppContext.get_app().executable
        os.startfile(exe_path, arguments="--show-docs")

    def __fix_path_limit(self) -> None:
        res_path: Path = AppContext.get_app().res_path

        try:
            os.startfile(res_path / "path_limit.reg")
        except OSError:
            pass
