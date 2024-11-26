"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.translation_provider.provider import Provider
from core.utilities.constants import SUPPORTED_LANGS
from ui.widgets.api_setup import ApiSetup
from ui.widgets.completion_box import CompletionBox

from .startup_dialog import StartupDialog


class SetupPage(QWidget):
    """
    Second page. For setting up game language and API Key.
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

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("transparent")
        vlayout.addWidget(self.scroll_area, 1)
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.scroll_area.setWidget(scroll_widget)
        slayout = QVBoxLayout()
        scroll_widget.setLayout(slayout)

        # Title label
        title_label = QLabel(self.mloc.setup_title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("title_label")
        slayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        slayout.addSpacing(25)

        # Help label
        help_label = QLabel(self.mloc.setup_help)
        help_label.setWordWrap(True)
        slayout.addWidget(help_label)

        slayout.addSpacing(25)

        # Language
        hlayout = QHBoxLayout()
        slayout.addLayout(hlayout)

        lang_label = QLabel(self.mloc.choose_lang)
        hlayout.addWidget(lang_label)
        self.lang_box = CompletionBox()
        self.lang_box.installEventFilter(self)
        self.lang_box.setPlaceholderText(self.loc.main.please_select)
        lang_items = [lang[0].capitalize() for lang in SUPPORTED_LANGS]
        self.lang_box.addItems(lang_items)
        hlayout.addWidget(self.lang_box)

        slayout.addSpacing(10)

        # Source
        hlayout = QHBoxLayout()
        slayout.addLayout(hlayout)

        source_label = QLabel(self.loc.main.source)
        source_label.setDisabled(True)
        hlayout.addWidget(source_label)
        self.source_dropdown = QComboBox()
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
                    Provider.Preference.PreferNexusMods.name
                )
            else:
                self.source_dropdown.setCurrentText(
                    Provider.Preference.OnlyNexusMods.name
                )

        self.lang_box.currentTextChanged.connect(on_lang_change)
        hlayout.addWidget(self.source_dropdown)

        # Masterlist
        self.masterlist_box = QCheckBox(self.loc.settings.use_masterlist)
        self.masterlist_box.setChecked(True)
        slayout.addWidget(self.masterlist_box)

        slayout.addSpacing(5)

        # Enabled File Types
        filetypes_groupbox = QGroupBox(self.loc.settings.enabled_file_types)
        slayout.addWidget(filetypes_groupbox)
        filetypes_vlayout = QVBoxLayout()
        filetypes_groupbox.setLayout(filetypes_vlayout)

        self.enable_interface_files_box = QCheckBox(
            self.loc.settings.enable_interface_files
        )
        self.enable_interface_files_box.setChecked(True)
        filetypes_vlayout.addWidget(self.enable_interface_files_box)

        self.enable_scripts_box = QCheckBox(
            self.loc.settings.enable_scripts + " [EXPERIMENTAL]"
        )
        self.enable_scripts_box.setChecked(False)
        filetypes_vlayout.addWidget(self.enable_scripts_box)

        self.enable_textures_box = QCheckBox(
            self.loc.settings.enable_textures + " [EXPERIMENTAL]"
        )
        self.enable_textures_box.setChecked(False)
        filetypes_vlayout.addWidget(self.enable_textures_box)

        self.enable_sound_files_box = QCheckBox(
            self.loc.settings.enable_sound_files + " [EXPERIMENTAL]"
        )
        self.enable_sound_files_box.setChecked(False)
        filetypes_vlayout.addWidget(self.enable_sound_files_box)

        slayout.addSpacing(5)

        # API Setup Widget
        api_groupbox = QGroupBox(self.loc.settings.nm_api_key)
        slayout.addWidget(api_groupbox)
        api_vlayout = QVBoxLayout()
        api_groupbox.setLayout(api_vlayout)
        self.api_setup = ApiSetup(self.startup_dialog.app)
        api_vlayout.addWidget(self.api_setup)

        # Back and Next Button
        vlayout.addStretch()
        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon("fa5s.chevron-left", color="#ffffff"))
        self.back_button.setText(self.loc.main.back)
        self.back_button.clicked.connect(self.startup_dialog.page_widget.slideInPrev)
        hlayout.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)

        hlayout.addStretch()

        self.next_button = QPushButton()
        self.next_button.setDisabled(True)
        self.next_button.setIcon(qta.icon("fa5s.chevron-right", color="#ffffff"))
        self.next_button.setText(self.loc.main.next)
        self.next_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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
    
    def eventFilter(self, source: QObject, event: QEvent):
        if event.type() == QEvent.Type.Wheel and isinstance(source, QComboBox):
            self.scroll_area.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
