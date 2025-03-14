"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLabel, QWidget

from core.config.translator_config import TranslatorConfig
from core.translator_api import AVAILABLE_APIS
from core.translator_api.translator import Translator
from ui.widgets.key_entry import KeyEntry

from .settings_page import SettingsPage


class TranslatorSettings(SettingsPage[TranslatorConfig]):
    """
    Widget for translator API settings.
    """

    __flayout: QFormLayout

    __translator_box: QComboBox
    __api_key_entry: KeyEntry

    __show_confirmations_box: QCheckBox

    @override
    def _init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        self.__flayout = QFormLayout()
        scroll_widget.setLayout(self.__flayout)

        self.__init_api_settings()
        self.__init_confirmation_box()

    def __init_api_settings(self) -> None:
        self.__translator_box = QComboBox()
        self.__translator_box.setEditable(False)
        self.__translator_box.addItems(
            [translator.name for translator in AVAILABLE_APIS]
        )
        self.__translator_box.setCurrentText(self._initial_config.translator.name)
        self.__translator_box.currentTextChanged.connect(self._on_change)
        self.__flayout.addRow(self.tr("Translator API"), self.__translator_box)

        api_key_label = QLabel(self.tr("Translator API Key"))
        self.__api_key_entry = KeyEntry()
        if self._initial_config.api_key:
            self.__api_key_entry.setText(self._initial_config.api_key)
        api_key_label.setEnabled(bool(self._initial_config.api_key))
        self.__api_key_entry.setEnabled(bool(self._initial_config.api_key))
        self.__api_key_entry.textChanged.connect(self._on_change)
        self.__flayout.addRow(api_key_label, self.__api_key_entry)

        # TODO: Make this dynamic depending on the selected translator
        self.__translator_box.currentTextChanged.connect(
            lambda text: (
                self.__api_key_entry.setEnabled(text == "DeepL"),
                api_key_label.setEnabled(text == "DeepL"),
            )
        )

    def __init_confirmation_box(self) -> None:
        self.__show_confirmations_box = QCheckBox(
            self.tr("Ask for confirmation before starting a batch machine translation")
        )
        self.__show_confirmations_box.setChecked(
            self._initial_config.show_confirmation_dialogs
        )
        self.__show_confirmations_box.stateChanged.connect(self._on_change)
        self.__flayout.addRow(self.__show_confirmations_box)

    @override
    def apply(self, config: TranslatorConfig) -> None:
        translators: dict[str, type[Translator]] = {
            translator.name: translator for translator in AVAILABLE_APIS
        }

        config.translator = translators[self.__translator_box.currentText()]
        config.api_key = self.__api_key_entry.text()
        config.show_confirmation_dialogs = self.__show_confirmations_box.isChecked()
