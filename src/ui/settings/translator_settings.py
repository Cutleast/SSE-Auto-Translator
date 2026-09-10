"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.widgets.enum_radiobutton_widget import EnumRadiobuttonsWidget
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFormLayout, QLabel, QPlainTextEdit, QWidget

from core.config.translator_config import TranslatorConfig
from core.translator.apis import TranslatorApi


class TranslatorSettings(SettingsPage[TranslatorConfig]):
    """
    Widget for translator API settings.
    """

    __flayout: QFormLayout

    __api_selector: EnumRadiobuttonsWidget[TranslatorApi]
    __api_key_label: QLabel
    __api_key_entry: KeyLineEdit
    __gemini_prompt_label: QLabel
    __gemini_prompt_entry: QPlainTextEdit

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
        self.__api_selector = EnumRadiobuttonsWidget(
            TranslatorApi,
            self._initial_config.translator,
            orientation=Qt.Orientation.Horizontal,
        )
        self.__api_selector.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__flayout.addRow(self.tr("Translator API"), self.__api_selector)

        self.__api_key_label = QLabel(self.tr("Translator API key"))
        self.__api_key_entry = KeyLineEdit()
        if self._initial_config.api_key:
            self.__api_key_entry.setText(self._initial_config.api_key)
        api_key_required = self.__requires_api_key(self._initial_config.translator)
        self.__api_key_label.setEnabled(api_key_required)
        self.__api_key_entry.setEnabled(api_key_required)
        self.__api_key_entry.textChanged.connect(lambda _: self.changed_signal.emit())
        self.__flayout.addRow(self.__api_key_label, self.__api_key_entry)

        self.__gemini_prompt_label = QLabel(self.tr("Gemini system prompt"))
        self.__gemini_prompt_entry = QPlainTextEdit()
        self.__gemini_prompt_entry.setPlainText(self._initial_config.gemini_prompt)
        self.__gemini_prompt_entry.setMinimumHeight(120)
        self.__gemini_prompt_entry.setToolTip(
            self.tr("The selected target language is appended automatically.")
        )
        self.__gemini_prompt_entry.textChanged.connect(
            lambda: self.changed_signal.emit()
        )
        self.__flayout.addRow(self.__gemini_prompt_label, self.__gemini_prompt_entry)

        self.__api_selector.currentValueChanged.connect(
            self.__set_translator_fields_enabled
        )
        self.__set_translator_fields_enabled(self._initial_config.translator)

    @staticmethod
    def __requires_api_key(translator_api: TranslatorApi) -> bool:
        """Returns whether the selected translator requires an API key."""

        return translator_api in (TranslatorApi.DeepL, TranslatorApi.Gemini)

    def __set_translator_fields_enabled(self, translator_api: TranslatorApi) -> None:
        """Updates API-specific settings when the selected translator changes."""

        api_key_required = self.__requires_api_key(translator_api)
        self.__api_key_label.setEnabled(api_key_required)
        self.__api_key_entry.setEnabled(api_key_required)

        gemini_selected = translator_api == TranslatorApi.Gemini
        self.__gemini_prompt_label.setEnabled(gemini_selected)
        self.__gemini_prompt_entry.setEnabled(gemini_selected)

    def __init_confirmation_box(self) -> None:
        self.__show_confirmations_box = QCheckBox(
            self.tr("Ask for confirmation before starting a batch machine translation")
        )
        self.__show_confirmations_box.setChecked(
            self._initial_config.show_confirmation_dialogs
        )
        self.__show_confirmations_box.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__flayout.addRow(self.__show_confirmations_box)

    @override
    def validate(self) -> None:
        translator_api: TranslatorApi = self.__api_selector.getCurrentValue()
        if (
            translator_api == TranslatorApi.DeepL
            and not self.__api_key_entry.text().strip()
        ):
            raise ConfigValidationError(
                self.tr("An API key is required for DeepL translator!")
            )
        if (
            translator_api == TranslatorApi.Gemini
            and not self.__api_key_entry.text().strip()
        ):
            raise ConfigValidationError(
                self.tr("An API key is required for Gemini translator!")
            )
        if (
            translator_api == TranslatorApi.Gemini
            and not self.__gemini_prompt_entry.toPlainText().strip()
        ):
            raise ConfigValidationError(
                self.tr("A system prompt is required for Gemini translator!")
            )

    @override
    def apply(self, config: TranslatorConfig) -> None:
        config.translator = self.__api_selector.getCurrentValue()
        config.api_key = self.__api_key_entry.text().strip() or None
        config.gemini_prompt = self.__gemini_prompt_entry.toPlainText().strip()
        config.show_confirmation_dialogs = self.__show_confirmations_box.isChecked()
