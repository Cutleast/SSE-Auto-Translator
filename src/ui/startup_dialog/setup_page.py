"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, override

from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.translation_provider.provider import Provider
from core.utilities.constants import SUPPORTED_LANGS
from core.utilities.localisation import LocalisationUtils
from ui.startup_dialog.page import Page
from ui.widgets.api_setup import ApiSetup
from ui.widgets.completion_box import CompletionBox
from ui.widgets.smooth_scroll_area import SmoothScrollArea


class SetupPage(Page):
    """
    Second page. For setting up game language and API Key.
    """

    __lang_dropdown: CompletionBox
    __source_label: QLabel
    __source_dropdown: QComboBox
    __masterlist_box: QCheckBox
    __api_setup: ApiSetup

    __interface_files_box: QCheckBox
    __scripts_box: QCheckBox
    __textures_box: QCheckBox
    __sound_files_box: QCheckBox

    @override
    def _init_form(self) -> None:
        # TODO: Move the scroll area to the Page class
        self.__scroll_area = SmoothScrollArea()
        self.__scroll_area.setObjectName("transparent")
        self._vlayout.addWidget(self.__scroll_area, 1)
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.__scroll_area.setWidget(scroll_widget)

        vlayout = QVBoxLayout()
        scroll_widget.setLayout(vlayout)

        # Language
        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        lang_label = QLabel(self.tr("Choose Game Language:"))
        hlayout.addWidget(lang_label)
        self.__lang_dropdown = CompletionBox()
        self.__lang_dropdown.installEventFilter(self)
        self.__lang_dropdown.setPlaceholderText(self.tr("Please select..."))
        lang_items = [lang[0].capitalize() for lang in SUPPORTED_LANGS]
        self.__lang_dropdown.addItems(lang_items)
        hlayout.addWidget(self.__lang_dropdown)

        vlayout.addSpacing(10)

        # Source
        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.__source_label = QLabel(self.tr("Source"))
        self.__source_label.setDisabled(True)
        hlayout.addWidget(self.__source_label)
        self.__source_dropdown = QComboBox()
        self.__source_dropdown.installEventFilter(self)
        self.__source_dropdown.setDisabled(True)
        self.__source_dropdown.setEditable(False)
        self.__source_dropdown.addItems(Provider.Preference._member_names_)
        self.__source_dropdown.setCurrentText(Provider.Preference.OnlyNexusMods.name)
        self.__lang_dropdown.currentTextChanged.connect(self.__on_lang_change)
        hlayout.addWidget(self.__source_dropdown)

        # Masterlist
        self.__masterlist_box = QCheckBox(
            self.tr("Use global Masterlist from GitHub Repository (recommended)")
        )
        self.__masterlist_box.setChecked(True)
        vlayout.addWidget(self.__masterlist_box)

        vlayout.addSpacing(5)

        # Enabled File Types
        filetypes_groupbox = QGroupBox(self.tr("Enabled File Types"))
        vlayout.addWidget(filetypes_groupbox)
        filetypes_vlayout = QVBoxLayout()
        filetypes_groupbox.setLayout(filetypes_vlayout)

        self.__interface_files_box = QCheckBox(
            self.tr("Enable Interface Files (Data/Interface/*.txt)")
        )
        self.__interface_files_box.setChecked(True)
        filetypes_vlayout.addWidget(self.__interface_files_box)

        self.__scripts_box = QCheckBox(
            self.tr("Enable Papyrus Scripts (Data/Scripts/*.pex)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.__scripts_box.setChecked(False)
        filetypes_vlayout.addWidget(self.__scripts_box)

        self.__textures_box = QCheckBox(
            self.tr("Enable Textures (Data/Textures/*)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.__textures_box.setChecked(False)
        filetypes_vlayout.addWidget(self.__textures_box)

        self.__sound_files_box = QCheckBox(
            self.tr("Enable Sound Files (Data/Sound/*)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.__sound_files_box.setChecked(False)
        filetypes_vlayout.addWidget(self.__sound_files_box)

        vlayout.addSpacing(5)

        # API Setup Widget
        api_groupbox = QGroupBox(self.tr("Nexus Mods API Key"))
        vlayout.addWidget(api_groupbox)
        api_vlayout = QVBoxLayout()
        api_groupbox.setLayout(api_vlayout)
        self.__api_setup = ApiSetup()
        api_vlayout.addWidget(self.__api_setup)

        self.__lang_dropdown.currentTextChanged.connect(lambda _: self._validate())
        self.__api_setup.valid_signal.connect(lambda _: self._validate())

        # Preselect system language if supported
        system_lang: Optional[str] = LocalisationUtils.detect_preferred_lang()
        if system_lang is not None:
            self.__lang_dropdown.setCurrentText(system_lang.capitalize())

    @override
    def _get_title(self) -> str:
        return self.tr("Initial Setup")

    @override
    def _get_description(self) -> str:
        return self.tr("On this page you setup basic settings.")

    def __on_lang_change(self, lang: str) -> None:
        self.__source_label.setEnabled(lang == "French")
        self.__source_dropdown.setEnabled(lang == "French")

        if lang == "French":
            self.__source_dropdown.setCurrentText(
                Provider.Preference.PreferNexusMods.name
            )
        else:
            self.__source_dropdown.setCurrentText(
                Provider.Preference.OnlyNexusMods.name
            )

    @override
    def _validate(self) -> None:
        lang_items: list[str] = [lang[0].capitalize() for lang in SUPPORTED_LANGS]

        self.valid_signal.emit(
            self.__lang_dropdown.currentIndex() != 0
            and self.__lang_dropdown.currentText() in lang_items
            and self.__api_setup.is_valid
        )

    @override
    def get_values(self) -> tuple[str, str, str, bool, bool, bool, bool, bool]:
        return (
            self.__lang_dropdown.currentText(),
            self.__source_dropdown.currentText(),
            self.__api_setup.api_key or "",
            self.__masterlist_box.isChecked(),
            self.__interface_files_box.isChecked(),
            self.__scripts_box.isChecked(),
            self.__textures_box.isChecked(),
            self.__sound_files_box.isChecked(),
        )

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and isinstance(source, QComboBox)
            and isinstance(event, QWheelEvent)
        ):
            self.__scroll_area.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
