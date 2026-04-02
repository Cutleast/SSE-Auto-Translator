"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.widgets.enum_radiobutton_widget import EnumRadiobuttonsWidget
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from core.config.translator_config import TranslatorConfig
from core.translator_api.lm_studio import LMStudioTranslator
from core.translator_api.translator_api import TranslatorApi
from ui.utilities.icon_provider import IconProvider
from ui.widgets.completion_box import CompletionBox


class TranslatorSettings(SettingsPage[TranslatorConfig]):
    """
    Widget for translator API settings.
    """

    __flayout: QFormLayout

    __api_selector: EnumRadiobuttonsWidget[TranslatorApi]
    __api_key_label: QLabel
    __api_key_entry: KeyLineEdit
    __lm_studio_base_url_label: QLabel
    __lm_studio_base_url_entry: QLineEdit
    __lm_studio_model_label: QLabel
    __lm_studio_model_entry: CompletionBox
    __lm_studio_reload_models_button: QPushButton
    __lm_studio_use_server_prompt_box: QCheckBox

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
            self.__on_translator_changed
        )
        self.__flayout.addRow(self.tr("Translator API"), self.__api_selector)

        self.__api_key_label = QLabel(self.tr("Translator API key"))
        self.__api_key_entry = KeyLineEdit()
        if self._initial_config.api_key:
            self.__api_key_entry.setText(self._initial_config.api_key)
        self.__api_key_entry.textChanged.connect(lambda _: self.changed_signal.emit())
        self.__flayout.addRow(self.__api_key_label, self.__api_key_entry)

        self.__lm_studio_base_url_label = QLabel(self.tr("LM Studio base URL"))
        self.__lm_studio_base_url_entry = QLineEdit()
        self.__lm_studio_base_url_entry.setText(
            self._initial_config.lm_studio_base_url
        )
        self.__lm_studio_base_url_entry.setPlaceholderText("http://127.0.0.1:1234")
        self.__lm_studio_base_url_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__lm_studio_base_url_entry.editingFinished.connect(
            self.__reload_lm_studio_models_silent
        )
        self.__flayout.addRow(
            self.__lm_studio_base_url_label, self.__lm_studio_base_url_entry
        )

        self.__lm_studio_model_label = QLabel(self.tr("LM Studio model"))
        self.__lm_studio_model_entry = CompletionBox()
        self.__lm_studio_model_entry.setPlaceholderText(
            self.tr("Optional: first loaded model is used automatically")
        )
        self.__lm_studio_model_entry.setCurrentText(
            self._initial_config.lm_studio_model or ""
        )
        self.__lm_studio_model_entry.currentTextChanged.connect(
            lambda _: self.changed_signal.emit()
        )

        model_widget = QWidget()
        model_layout = QHBoxLayout()
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_widget.setLayout(model_layout)
        model_layout.addWidget(self.__lm_studio_model_entry)

        self.__lm_studio_reload_models_button = QPushButton(
            IconProvider.get_qta_icon("mdi6.refresh"), self.tr("Reload")
        )
        self.__lm_studio_reload_models_button.clicked.connect(
            self.__reload_lm_studio_models
        )
        model_layout.addWidget(self.__lm_studio_reload_models_button)

        self.__flayout.addRow(self.__lm_studio_model_label, model_widget)

        self.__lm_studio_use_server_prompt_box = QCheckBox(
            self.tr("Use the prompt configured in LM Studio")
        )
        self.__lm_studio_use_server_prompt_box.setChecked(
            self._initial_config.lm_studio_use_server_prompt
        )
        self.__lm_studio_use_server_prompt_box.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__flayout.addRow(self.__lm_studio_use_server_prompt_box)

        self.__update_translator_fields(self._initial_config.translator)

    def __on_translator_changed(self, translator_api: TranslatorApi) -> None:
        self.__update_translator_fields(translator_api)
        self.changed_signal.emit()

    def __update_translator_fields(self, translator_api: TranslatorApi) -> None:
        is_deepl = translator_api == TranslatorApi.DeepL
        is_lm_studio = translator_api == TranslatorApi.LMStudio

        self.__api_key_label.setEnabled(is_deepl)
        self.__api_key_entry.setEnabled(is_deepl)

        self.__lm_studio_base_url_label.setEnabled(is_lm_studio)
        self.__lm_studio_base_url_entry.setEnabled(is_lm_studio)
        self.__lm_studio_model_label.setEnabled(is_lm_studio)
        self.__lm_studio_model_entry.setEnabled(is_lm_studio)
        self.__lm_studio_reload_models_button.setEnabled(is_lm_studio)
        self.__lm_studio_use_server_prompt_box.setEnabled(is_lm_studio)

        if is_lm_studio:
            self.__reload_lm_studio_models_silent()

    def __reload_lm_studio_models(self) -> None:
        self.__load_lm_studio_models(show_errors=True)

    def __reload_lm_studio_models_silent(self) -> None:
        self.__load_lm_studio_models(show_errors=False)

    def __load_lm_studio_models(self, show_errors: bool) -> None:
        base_url = LMStudioTranslator.normalize_base_url(
            self.__lm_studio_base_url_entry.text()
        )
        current_model = self.__lm_studio_model_entry.currentText().strip()

        self.__lm_studio_model_entry.clear()
        self.__lm_studio_model_entry.setPlaceholderText(
            self.tr("Optional: first loaded model is used automatically")
        )

        if not base_url:
            self.__lm_studio_model_entry.setCurrentText(current_model)
            return

        try:
            models = LMStudioTranslator.list_models(base_url)
        except (ConnectionError, ValueError) as exc:
            self.__lm_studio_model_entry.setCurrentText(current_model)
            self.__lm_studio_model_entry.setPlaceholderText(
                self.tr("Could not load models. You can still enter one manually.")
            )
            if show_errors:
                QMessageBox.warning(
                    self,
                    self.tr("LM Studio Models"),
                    self.tr("Failed to load LM Studio models:\n%1").replace(
                        "%1", str(exc)
                    ),
                )
            return

        self.__lm_studio_model_entry.addItems(models)

        if current_model:
            self.__lm_studio_model_entry.setCurrentText(current_model)
        elif models:
            self.__lm_studio_model_entry.setCurrentText(models[0])

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
    def apply(self, config: TranslatorConfig) -> None:
        config.translator = self.__api_selector.getCurrentValue()
        config.api_key = self.__api_key_entry.text().strip() or None
        config.lm_studio_base_url = (
            self.__lm_studio_base_url_entry.text().strip() or "http://127.0.0.1:1234"
        )
        config.lm_studio_model = (
            self.__lm_studio_model_entry.currentText().strip() or None
        )
        config.lm_studio_use_server_prompt = (
            self.__lm_studio_use_server_prompt_box.isChecked()
        )
        config.show_confirmation_dialogs = self.__show_confirmations_box.isChecked()
