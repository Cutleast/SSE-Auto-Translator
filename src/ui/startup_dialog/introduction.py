"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, override

from cutleast_core_lib.core.utilities.path_limit_fixer import PathLimitFixer
from cutleast_core_lib.ui.utilities.rotated_icon import rotated_icon
from cutleast_core_lib.ui.widgets.link_button import LinkButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget

from core.config.user_config import UserConfig
from core.utilities.constants import DOCS_URL
from ui.startup_dialog.page import Page
from ui.utilities.icon_provider import IconProvider


class IntroductionPage(Page):
    """
    First page. Informs user about further steps
    and usage of this application.
    """

    BASIC_USAGE_URL: str = DOCS_URL + "/quick_start.html"
    """URL to the basic usage documentation page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._back_button.setText(self.tr("Exit"))
        self._back_button.setIcon(
            rotated_icon(IconProvider.get_icon("exit"), angle=180)
        )
        self.valid_signal.emit(True)

        self.__init_header()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self._vlayout.insertLayout(0, hlayout)

        hlayout.addStretch()

        icon_label = QLabel()
        icon_label.setPixmap(QApplication.windowIcon().pixmap(96, 96))
        hlayout.addWidget(icon_label)

        hlayout.addSpacing(15)

        title_label = QLabel("SSE Auto Translator".upper())
        font = title_label.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10)
        title_label.setFont(font)
        title_label.setObjectName("h1")
        hlayout.addWidget(title_label)

        hlayout.addStretch()

        self._vlayout.insertSpacing(0, 25)
        self._title_label.setObjectName("h2")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._vlayout.insertWidget(
            2, self._title_label, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self._vlayout.insertSpacing(2, 25)

    @override
    def _get_title(self) -> str:
        return self.tr("Welcome!")

    @override
    def _get_description(self) -> str:
        return self.tr(
            "This guide will help you setting up this tool for your modlist."
        )

    @override
    def _init_form(self) -> None:
        from app import App

        documentation_button = LinkButton(
            url=IntroductionPage.BASIC_USAGE_URL,
            display_text=self.tr("Open documentation"),
            icon=IconProvider.get_qta_icon("mdi6.file-document"),
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

        fix_button = QPushButton(self.tr("Fix Windows path limit"))
        fix_button.clicked.connect(
            lambda: PathLimitFixer.disable_path_limit(App.get().res_path)
        )
        self._vlayout.addWidget(fix_button)

        if not PathLimitFixer.is_path_limit_enabled():
            fix_button.setDisabled(True)
            self._vlayout.addWidget(
                QLabel(self.tr("The path limit is already disabled.")),
                alignment=Qt.AlignmentFlag.AlignHCenter,
            )

        self._vlayout.addStretch()

    @override
    def _validate(self) -> None:
        return None

    @override
    def apply(self, config: UserConfig) -> None:
        return None
