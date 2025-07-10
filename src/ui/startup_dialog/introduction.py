"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from app_context import AppContext
from core.cache.cache import Cache
from core.config.user_config import UserConfig
from core.utilities.path_limit_fixer import PathLimitFixer
from ui.startup_dialog.page import Page


class IntroductionPage(Page):
    """
    First page. Informs user about further steps
    and usage of this application.
    """

    def __init__(self, cache: Cache, parent: Optional[QWidget] = None) -> None:
        super().__init__(cache, parent)

        self._back_button.setText("Exit")
        self.valid_signal.emit(True)

    @override
    def _get_title(self) -> str:
        return self.tr("Welcome!")

    @override
    def _get_description(self) -> str:
        return self.tr(
            "This Guide will help you setting up this Tool for your modlist."
        )

    @override
    def _init_form(self) -> None:
        documentation_button = QPushButton(self.tr("Open Documentation"))
        documentation_button.clicked.connect(AppContext.get_app().open_documentation)
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
        fix_button.clicked.connect(
            lambda: PathLimitFixer.disable_path_limit(AppContext.get_app().res_path)
        )
        self._vlayout.addWidget(fix_button)

        if not PathLimitFixer.is_path_limit_enabled():
            fix_button.setDisabled(True)
            self._vlayout.addWidget(
                QLabel(self.tr("Path Limit is already disabled.")),
                alignment=Qt.AlignmentFlag.AlignHCenter,
            )

        self._vlayout.addStretch()

    @override
    def _validate(self) -> None:
        return None

    @override
    def apply(self, config: UserConfig) -> None:
        return None
