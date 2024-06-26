"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

import utilities as utils
from translation_provider import Provider
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

        self.scroll_area = qtw.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("transparent")
        vlayout.addWidget(self.scroll_area, 1)
        scroll_widget = qtw.QWidget()
        scroll_widget.setObjectName("transparent")
        self.scroll_area.setWidget(scroll_widget)
        slayout = qtw.QVBoxLayout()
        scroll_widget.setLayout(slayout)

        # Title label
        title_label = qtw.QLabel(self.mloc.setup_title)
        title_label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("title_label")
        slayout.addWidget(title_label, 0, qtc.Qt.AlignmentFlag.AlignHCenter)
        slayout.addSpacing(25)

        # Help label
        help_label = qtw.QLabel(self.mloc.setup_help)
        help_label.setWordWrap(True)
        slayout.addWidget(help_label)

        slayout.addSpacing(25)

        # Language
        hlayout = qtw.QHBoxLayout()
        slayout.addLayout(hlayout)

        lang_label = qtw.QLabel(self.mloc.choose_lang)
        hlayout.addWidget(lang_label)
        self.lang_box = CompletionBox()
        self.lang_box.installEventFilter(self)
        self.lang_box.setPlaceholderText(self.loc.main.please_select)
        lang_items = [lang[0].capitalize() for lang in utils.SUPPORTED_LANGS]
        self.lang_box.addItems(lang_items)
        hlayout.addWidget(self.lang_box)

        slayout.addSpacing(10)

        # Source
        hlayout = qtw.QHBoxLayout()
        slayout.addLayout(hlayout)

        source_label = qtw.QLabel(self.loc.main.source)
        source_label.setDisabled(True)
        hlayout.addWidget(source_label)
        self.source_dropdown = qtw.QComboBox()
        self.source_dropdown.installEventFilter(self)
        self.source_dropdown.setDisabled(True)
        self.source_dropdown.setEditable(False)
        self.source_dropdown.addItems(Provider.Preference._member_names_)
        self.source_dropdown.setCurrentText(Provider.Preference.OnlyNexusMods.name)

        def on_lang_change(lang: str):
            source_label.setEnabled(lang == "French")
            self.source_dropdown.setEnabled(lang == "French")

            if lang == "French":
                self.source_dropdown.setCurrentText(
                    Provider.Preference.PreferConfrerie.name
                )
            else:
                self.source_dropdown.setCurrentText(
                    Provider.Preference.OnlyNexusMods.name
                )

        self.lang_box.currentTextChanged.connect(on_lang_change)
        hlayout.addWidget(self.source_dropdown)

        # Masterlist
        self.masterlist_box = qtw.QCheckBox(self.loc.settings.use_masterlist)
        self.masterlist_box.setChecked(True)
        slayout.addWidget(self.masterlist_box)

        slayout.addSpacing(5)

        # Enabled File Types
        filetypes_label = qtw.QLabel(self.loc.settings.enabled_file_types)
        filetypes_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        filetypes_label.setObjectName("relevant_label")
        slayout.addWidget(filetypes_label, 0, qtc.Qt.AlignmentFlag.AlignLeft)

        self.enable_interface_files_box = qtw.QCheckBox(
            self.loc.settings.enable_interface_files
        )
        self.enable_interface_files_box.setChecked(True)
        slayout.addWidget(self.enable_interface_files_box)

        self.enable_scripts_box = qtw.QCheckBox(
            self.loc.settings.enable_scripts + " [EXPERIMENTAL]"
        )
        self.enable_scripts_box.setChecked(True)
        slayout.addWidget(self.enable_scripts_box)

        self.enable_textures_box = qtw.QCheckBox(
            self.loc.settings.enable_textures + " [EXPERIMENTAL]"
        )
        self.enable_textures_box.setChecked(False)
        slayout.addWidget(self.enable_textures_box)

        self.enable_sound_files_box = qtw.QCheckBox(
            self.loc.settings.enable_sound_files + " [EXPERIMENTAL]"
        )
        self.enable_sound_files_box.setChecked(False)
        slayout.addWidget(self.enable_sound_files_box)

        slayout.addSpacing(5)

        # API Setup Widget
        self.api_setup = ApiSetup(self.startup_dialog.app)
        slayout.addWidget(self.api_setup)

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
    
    def eventFilter(self, source: qtc.QObject, event: qtc.QEvent):
        if event.type() == qtc.QEvent.Type.Wheel and isinstance(source, qtw.QComboBox):
            self.scroll_area.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
