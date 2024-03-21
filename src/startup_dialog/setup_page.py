"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

from utilities import LangDetector, Language
from widgets import ApiSetup, CompletionBox

from .startup_dialog import StartupDialog


class SetupPage(qtw.QWidget):
    """
    Second page. For setting up game language and API Key.
    """

    def __init__(self, startup_dialog: StartupDialog):
        super().__init__()

        self.startup_dialog = startup_dialog
        self.loc = startup_dialog.loc
        self.mloc = startup_dialog.mloc

        self.setObjectName("primary")

        vlayout = qtw.QVBoxLayout()
        vlayout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(vlayout)

        # Title label
        title_label = qtw.QLabel(self.mloc.setup_title)
        title_label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label, 0, qtc.Qt.AlignmentFlag.AlignHCenter)
        vlayout.addSpacing(25)

        # Help label
        help_label = qtw.QLabel(self.mloc.setup_help)
        help_label.setWordWrap(True)
        vlayout.addWidget(help_label)

        vlayout.addSpacing(25)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        # Language
        lang_label = qtw.QLabel(self.mloc.choose_lang)
        hlayout.addWidget(lang_label)
        self.lang_box = CompletionBox()
        self.lang_box.setPlaceholderText(self.loc.main.please_select)
        lang_items = [
            str(lang).removeprefix("Language.").capitalize()
            for lang in LangDetector.get_available_langs()
            if lang != Language.ENGLISH
        ]
        self.lang_box.addItems(lang_items)
        hlayout.addWidget(self.lang_box)

        vlayout.addSpacing(10)

        # Masterlist
        self.masterlist_box = qtw.QCheckBox(self.loc.settings.use_masterlist)
        self.masterlist_box.setChecked(True)
        vlayout.addWidget(self.masterlist_box)

        vlayout.addSpacing(10)

        # API Setup Widget
        self.api_setup = ApiSetup(self.startup_dialog.app)
        vlayout.addWidget(self.api_setup)

        # Back and Next Button
        vlayout.addStretch()
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.back_button = qtw.QPushButton()
        self.back_button.setIcon(qta.icon("fa5s.chevron-left", color="#ffffff"))
        self.back_button.setText(self.loc.main.back)
        self.back_button.clicked.connect(self.startup_dialog.page_widget.slideInPrev)
        hlayout.addWidget(self.back_button, 0, qtc.Qt.AlignmentFlag.AlignLeft)

        hlayout.addStretch()

        self.next_button = qtw.QPushButton()
        self.next_button.setDisabled(True)
        self.next_button.setIcon(qta.icon("fa5s.chevron-right", color="#ffffff"))
        self.next_button.setText(self.loc.main.next)
        self.next_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.next_button.clicked.connect(self.startup_dialog.page_widget.slideInNext)
        hlayout.addWidget(self.next_button)

        def validate():
            self.next_button.setEnabled(
                self.lang_box.currentText() != self.loc.main.please_select
                and self.lang_box.currentText() in lang_items
                and self.api_setup.is_valid
            )

        self.lang_box.currentTextChanged.connect(lambda _: validate())
        self.api_setup.valid_signal.connect(lambda _: validate())
