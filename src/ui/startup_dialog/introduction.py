"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.core.utilities.path_limit_fixer import PathLimitFixer
from cutleast_core_lib.ui.utilities.rotated_icon import rotated_icon
from cutleast_core_lib.ui.widgets.link_button import LinkButton
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.config.user_config import UserConfig
from core.utilities.constants import DOCS_URL
from ui.utilities.icon_provider import IconProvider

from .page import Page


class IntroductionPage(Page):
    """
    First page. Informs user about further steps
    and usage of this application.
    """

    BASIC_USAGE_URL: str = DOCS_URL + "/quick_start.html"
    """URL to the basic usage documentation page."""

    @override
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._back_button.setText(self.tr("Exit"))
        IconProvider.bind_custom_icon(
            self._back_button,
            self._back_button.setIcon,
            lambda: rotated_icon(IconProvider.get_icon("exit"), angle=180),
        )
        self.valid_signal.emit(True)

        self.__init_header()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._vlayout.insertLayout(0, hlayout)

        icon_label = QLabel()
        icon_label.setPixmap(QApplication.windowIcon().pixmap(96, 96))
        hlayout.addWidget(icon_label)

        title_label = QLabel("SSE Auto Translator".upper())
        title_label.setProperty("title", True)
        hlayout.addWidget(title_label)

        self._title_label.hide()
        self._description_label.hide()

    @override
    def _get_title(self) -> str:
        return ""

    @override
    def _get_description(self) -> str:
        return ""

    @override
    def _init_form(self) -> None:
        from app import App

        # Welcome box
        welcome_groupbox = QGroupBox(self.tr("Welcome"))
        self._vlayout.addWidget(welcome_groupbox)
        welcome_vlayout = QVBoxLayout()
        welcome_groupbox.setLayout(welcome_vlayout)

        introduction_label = QLabel(
            self.tr("This guide will help you setting up this tool for your modlist.")
        )
        introduction_label.setWordWrap(True)
        welcome_vlayout.addWidget(introduction_label)

        documentation_button = LinkButton(
            IntroductionPage.BASIC_USAGE_URL, self.tr("Open documentation")
        )
        IconProvider.bind_qta_icon(
            documentation_button, documentation_button.setIcon, "mdi6.file-document"
        )
        documentation_button.setAutoDefault(False)
        welcome_vlayout.addWidget(documentation_button)

        # Path Limit
        path_limit_groupbox = QGroupBox(self.tr("Windows path limit"))
        self._vlayout.addWidget(path_limit_groupbox)
        path_limit_vlayout = QVBoxLayout()
        path_limit_groupbox.setLayout(path_limit_vlayout)

        path_limit_label = QLabel(
            self.tr(
                "Windows has a length limit of 255 characters for paths. "
                "Click below, grant admin rights and reboot to disable it."
            )
        )
        path_limit_label.setWordWrap(True)
        path_limit_vlayout.addWidget(path_limit_label)

        fix_button = QPushButton(self.tr("Fix Windows path limit"))
        fix_button.clicked.connect(
            lambda: PathLimitFixer.disable_path_limit(App.get().res_path)
        )
        fix_button.setAutoDefault(False)
        path_limit_vlayout.addWidget(fix_button)

        if not PathLimitFixer.is_path_limit_enabled():
            fix_button.setDisabled(True)
            fixed_label = QLabel(self.tr("The path limit is already disabled."))
            fixed_label.setProperty("state", "success")
            path_limit_vlayout.addWidget(
                fixed_label, alignment=Qt.AlignmentFlag.AlignHCenter
            )

        self._vlayout.addStretch()

    @override
    def _validate(self) -> None:
        return None

    @override
    def apply(self, config: UserConfig) -> None:
        return None
