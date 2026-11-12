"""
Copyright (c) Cutleast
"""

from typing import Optional, cast, override

from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.core.config.manager import ConfigManager
from cutleast_core_lib.core.utilities.thread import Thread
from cutleast_core_lib.core.utilities.typing_utils import coalesce
from cutleast_core_lib.ui.progress.spinner import SpinnerWidget
from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.widgets.double_spin_box import DoubleSpinBox
from cutleast_core_lib.ui.widgets.enum_placeholder_dropdown import (
    EnumPlaceholderDropdown,
)
from cutleast_core_lib.ui.widgets.enum_radiobutton_widget import EnumRadiobuttonsWidget
from cutleast_core_lib.ui.widgets.icon_button import IconButton
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from cutleast_core_lib.ui.widgets.spin_box import SpinBox
from cutleast_core_lib.ui.widgets.tree_widget_editor import TreeWidgetEditor
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.config.translator_config import TranslatorConfig
from core.translator.apis import TranslatorApi
from core.translator.llm import LlmTranslator
from ui.utilities.icon_provider import IconProvider

from .glossary_term import GlossaryTerm
from .glossary_term_dialog import GlossaryTermDialog


class TranslatorSettings(SettingsPage[TranslatorConfig]):
    """
    Widget for translator API settings.
    """

    __llm_model_thread: Optional[Thread[list[str]]]

    __vlayout: QVBoxLayout

    __api_selector: EnumRadiobuttonsWidget[TranslatorApi]
    __show_confirmations_box: QCheckBox
    __max_requests_box: SpinBox
    __glossary_editor: TreeWidgetEditor[GlossaryTerm]

    __deepl_group: QGroupBox
    __deepl_api_key_entry: KeyLineEdit

    __llm_group: QGroupBox
    __llm_base_url_entry: QLineEdit
    __llm_preset_box: EnumPlaceholderDropdown[LlmTranslator.ProviderPreset]
    __llm_api_key_entry: KeyLineEdit
    __llm_model_box: QComboBox
    __llm_model_spinner: SpinnerWidget
    __llm_load_models_button: QPushButton
    __llm_temperature_box: DoubleSpinBox
    __llm_system_prompt_edit: QPlainTextEdit
    __llm_reset_prompt_button: QPushButton

    @override
    def __init__(self, config_manager: ConfigManager[TranslatorConfig]) -> None:
        self.__llm_model_thread = None

        super().__init__(config_manager)

        self.__api_selector.currentValueChanged.connect(self.__on_api_changed)
        self.__show_confirmations_box.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__max_requests_box.valueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__glossary_editor.changed.connect(self.changed_signal.emit)
        self.__glossary_editor.onAdd.connect(self.__add_glossary_term)
        self.__glossary_editor.onEdit.connect(self.__edit_glossary_term)

        self.__llm_preset_box.currentValueChanged.connect(self.__on_llm_preset_selected)
        self.__llm_base_url_entry.textChanged.connect(self.__on_llm_url_changed)

        self.__llm_api_key_entry.textChanged.connect(
            lambda *_: self.changed_signal.emit()
        )
        self.__llm_model_box.currentTextChanged.connect(
            lambda *_: self.changed_signal.emit()
        )
        self.__llm_load_models_button.clicked.connect(self.__load_llm_models)
        self.__llm_temperature_box.valueChanged.connect(
            lambda *_: self.changed_signal.emit()
        )
        self.__llm_system_prompt_edit.textChanged.connect(
            lambda *_: self.changed_signal.emit()
        )
        self.__llm_reset_prompt_button.clicked.connect(self.__reset_llm_system_prompt)

        self.__on_api_changed(self._config.translator)
        self.__on_llm_url_changed(self._config.llm_base_url or "")

    @override
    def _init_ui(self) -> None:
        scroll_widget = QWidget()
        self.setWidget(scroll_widget)

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__vlayout.setContentsMargins(4, 0, 4, 0)
        scroll_widget.setLayout(self.__vlayout)

        self.__init_api_settings()
        self.__init_deepl_settings()
        self.__init_llm_settings()

    def __init_api_settings(self) -> None:
        api_group = QGroupBox(self.tr("Translator"))
        self.__vlayout.addWidget(api_group)
        api_glayout = QGridLayout()
        api_glayout.setColumnStretch(0, 1)
        api_glayout.setColumnStretch(1, 1)
        api_group.setLayout(api_glayout)

        api_label = QLabel(self.tr("Preferred translator API"))
        api_glayout.addWidget(api_label, 0, 0)

        self.__api_selector = EnumRadiobuttonsWidget(
            TranslatorApi,
            self._config.translator,
            orientation=Qt.Orientation.Horizontal,
        )
        cast(QHBoxLayout, self.__api_selector.layout()).setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )
        api_glayout.addWidget(self.__api_selector, 0, 1)

        self.__show_confirmations_box = QCheckBox(
            self.tr("Ask for confirmation before starting a batch machine translation")
        )
        self.__show_confirmations_box.setChecked(self._config.show_confirmation_dialogs)
        api_glayout.addWidget(self.__show_confirmations_box, 1, 0, 1, 2)

        max_requests_label = QLabel(
            self.tr(
                "Maximum number of parallel requests (if parallel requests are "
                "supported by the selected translator)"
            )
        )
        max_requests_label.setWordWrap(True)
        api_glayout.addWidget(max_requests_label, 2, 0)

        self.__max_requests_box = SpinBox()
        self.__max_requests_box.setRange(1, 32)
        self.__max_requests_box.setValue(self._config.max_parallel_requests)
        api_glayout.addWidget(self.__max_requests_box, 2, 1)

        glossary_widget = QWidget()
        glossary_vlayout = QVBoxLayout()
        glossary_vlayout.setContentsMargins(0, 0, 0, 0)
        glossary_widget.setLayout(glossary_vlayout)

        help_label = QLabel(
            self.tr(
                "The glossary is a dictionary of terms that tell the translator how to "
                "substitute an original term. The terms are matched case-insensitively "
                "and take precedence over names from other translations. They must "
                "match the game language. Add plurals as separate terms if their "
                "translation differs."
            )
        )
        help_label.setWordWrap(True)
        help_label.setProperty("secondary", True)
        glossary_vlayout.addWidget(help_label)

        self.__glossary_editor = TreeWidgetEditor(
            GlossaryTerm,
            [
                GlossaryTerm(original=original, translation=translation)
                for original, translation in self._config.glossary.items()
            ],
        )
        self.__glossary_editor.setMinimumHeight(200)
        glossary_vlayout.addWidget(self.__glossary_editor)

        label = QLabel(self.tr("Glossary"))
        label.setProperty("subtitle", True)

        section_widget = SectionAreaWidget(label, glossary_widget)
        api_glayout.addWidget(section_widget, 3, 0, 1, 2)

        WidgetStateManager.get().register_state(
            "translator_settings_glossary", section_widget
        )

    def __init_deepl_settings(self) -> None:
        self.__deepl_group = QGroupBox(self.tr("DeepL settings"))
        self.__vlayout.addWidget(self.__deepl_group)
        deepl_glayout = QGridLayout()
        deepl_glayout.setColumnStretch(0, 1)
        deepl_glayout.setColumnStretch(1, 1)
        self.__deepl_group.setLayout(deepl_glayout)

        help_label = QLabel(
            self.tr(
                "DeepL requires an API key and charges based on the number of "
                "characters translated. You can obtain a free API key that includes a "
                "monthly budget of 500k free translated characters here:"
            )
            + "<br/><a href='https://www.deepl.com/en/signup?cta=checkout&is_api=true&productId=api-developer'>"
            "https://www.deepl.com/en/signup?cta=checkout&is_api=true&productId=api-developer</a>"
        )
        help_label.setOpenExternalLinks(True)
        help_label.setTextFormat(Qt.TextFormat.RichText)
        help_label.setWordWrap(True)
        help_label.setProperty("secondary", True)
        deepl_glayout.addWidget(help_label, 0, 0, 1, 2)

        api_key_label = QLabel(self.tr("API key"))
        deepl_glayout.addWidget(api_key_label, 1, 0)

        self.__deepl_api_key_entry = KeyLineEdit()
        if self._config.deepl_api_key:
            self.__deepl_api_key_entry.setText(self._config.deepl_api_key)
        self.__deepl_api_key_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        deepl_glayout.addWidget(self.__deepl_api_key_entry, 1, 1)

    def __init_llm_settings(self) -> None:
        self.__llm_group = QGroupBox(self.tr("LLM settings"))
        self.__vlayout.addWidget(self.__llm_group)
        llm_glayout = QGridLayout()
        llm_glayout.setColumnStretch(0, 1)
        llm_glayout.setColumnStretch(1, 1)
        self.__llm_group.setLayout(llm_glayout)

        help_label = QLabel(
            self.tr(
                "An LLM provides the highest-quality machine translations but requires "
                "additional setup to work. You have the choice between a cloud provider "
                "like OpenAI, Anthropic or Google Gemini and a self-hosted LLM in LM "
                "Studio or Ollama. In short: Any OpenAI-compatible LLM provider can "
                "be setup here.<br/>For additional instructions see the documentation:"
            )
            + " <a href='https://moddingforge.com/docs/sse-at/editor#llm_translation'>"
            "https://moddingforge.com/docs/sse-at/editor#llm_translation</a>"
        )
        help_label.setOpenExternalLinks(True)
        help_label.setTextFormat(Qt.TextFormat.RichText)
        help_label.setWordWrap(True)
        help_label.setProperty("secondary", True)
        llm_glayout.addWidget(help_label, 0, 0, 1, 2)

        url_label = QLabel(self.tr("Base URL"))
        llm_glayout.addWidget(url_label, 1, 0)

        url_hlayout = QHBoxLayout()
        url_hlayout.setContentsMargins(0, 0, 0, 0)
        llm_glayout.addLayout(url_hlayout, 1, 1)

        self.__llm_preset_box = EnumPlaceholderDropdown(
            LlmTranslator.ProviderPreset, placeholder_text=self.tr("Custom")
        )
        url_hlayout.addWidget(self.__llm_preset_box)

        self.__llm_base_url_entry = QLineEdit()
        self.__llm_base_url_entry.setPlaceholderText("http://127.0.0.1/...")
        self.__llm_base_url_entry.setText(self._config.llm_base_url)
        url_hlayout.addWidget(self.__llm_base_url_entry, 1)

        api_key_label = QLabel(self.tr("API key"))
        llm_glayout.addWidget(api_key_label, 2, 0)

        self.__llm_api_key_entry = KeyLineEdit()
        self.__llm_api_key_entry.setPlaceholderText(
            self.tr("Not required for most local providers")
        )
        self.__llm_api_key_entry.setText(self._config.llm_api_key)
        llm_glayout.addWidget(self.__llm_api_key_entry, 2, 1)

        model_label = QLabel(self.tr("Model"))
        llm_glayout.addWidget(model_label, 3, 0)

        model_hlayout = QHBoxLayout()
        model_hlayout.setContentsMargins(0, 0, 0, 0)
        llm_glayout.addLayout(model_hlayout, 3, 1)

        self.__llm_model_box = QComboBox()
        self.__llm_model_box.installEventFilter(self)
        self.__llm_model_box.setEditable(True)
        self.__llm_model_box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.__llm_model_box.setCurrentText(self._config.llm_model or "")
        model_hlayout.addWidget(self.__llm_model_box, 1)

        self.__llm_load_models_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__llm_load_models_button,
            self.__llm_load_models_button.setIcon,
            "mdi6.reload",
        )
        self.__llm_load_models_button.setToolTip(self.tr("Fetch model list"))
        model_hlayout.addWidget(self.__llm_load_models_button)

        self.__llm_model_spinner = SpinnerWidget()
        self.__llm_model_spinner.setText(self.tr("Fetching model list..."))
        self.__llm_model_spinner.hide()
        llm_glayout.addWidget(self.__llm_model_spinner, 4, 1)

        temperature_label = QLabel(self.tr("Temperature (if supported by the provider)"))
        llm_glayout.addWidget(temperature_label, 5, 0)

        self.__llm_temperature_box = DoubleSpinBox()
        self.__llm_temperature_box.setRange(-0.1, 2.0)
        self.__llm_temperature_box.setSingleStep(0.1)
        self.__llm_temperature_box.setSpecialValueText(self.tr("Provider default"))
        self.__llm_temperature_box.setValue(coalesce(self._config.llm_temperature, -0.1))
        llm_glayout.addWidget(self.__llm_temperature_box, 5, 1)

        prompt_widget = QWidget()
        prompt_vlayout = QVBoxLayout()
        prompt_vlayout.setContentsMargins(0, 0, 0, 0)
        prompt_widget.setLayout(prompt_vlayout)

        help_label = QLabel(
            self.tr(
                "The system prompt represents the base instructions and is sent to the "
                "LLM with every translation request. Here you can append special "
                "instructions or guidelines for the LLM to follow when translating "
                'strings. "{language}" is replaced with the game language.<br/>'
                "Check out the documentation for some tips on how to tweak this:"
            )
            + " <a href='https://moddingforge.com/docs/sse-at/editor#llm-prompt-tips'>"
            "https://moddingforge.com/docs/sse-at/editor#llm-prompt-tips</a>"
        )
        help_label.setOpenExternalLinks(True)
        help_label.setTextFormat(Qt.TextFormat.RichText)
        help_label.setWordWrap(True)
        help_label.setProperty("secondary", True)
        prompt_vlayout.addWidget(help_label)

        self.__llm_system_prompt_edit = QPlainTextEdit()
        self.__llm_system_prompt_edit.setPlainText(self._config.llm_system_prompt)
        prompt_vlayout.addWidget(self.__llm_system_prompt_edit)

        self.__llm_reset_prompt_button = QPushButton(self.tr("Reset to default"))
        self.__llm_reset_prompt_button.setProperty("destructive", True)
        IconProvider.bind_qta_icon(
            self.__llm_reset_prompt_button,
            self.__llm_reset_prompt_button.setIcon,
            "mdi6.undo",
            color=IconProvider.Color.Destructive,
        )
        default_system_prompt: str = TranslatorConfig.get_default_value(
            "llm_system_prompt", str
        )
        self.__llm_reset_prompt_button.setEnabled(
            self.__llm_system_prompt_edit.toPlainText().strip() != default_system_prompt
        )
        prompt_vlayout.addWidget(
            self.__llm_reset_prompt_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        label = QLabel(self.tr("System prompt"))
        label.setProperty("subtitle", True)

        section_widget = SectionAreaWidget(label, prompt_widget)
        llm_glayout.addWidget(section_widget, 6, 0, 1, 2)

        WidgetStateManager.get().register_state(
            "translator_settings_system_prompt", section_widget
        )

    def __on_api_changed(self, translator_api: TranslatorApi) -> None:
        self.__deepl_group.setVisible(translator_api == TranslatorApi.DeepL)
        self.__llm_group.setVisible(translator_api == TranslatorApi.Llm)
        self.changed_signal.emit()

    def __on_llm_preset_selected(
        self, preset: Optional[LlmTranslator.ProviderPreset]
    ) -> None:
        if preset is not None:
            with QSignalBlocker(self.__llm_base_url_entry):
                self.__llm_base_url_entry.setText(preset.value)

        self.__llm_base_url_entry.setEnabled(preset is None)
        self.changed_signal.emit()

    def __on_llm_url_changed(self, url: str) -> None:
        preset: Optional[LlmTranslator.ProviderPreset] = (
            LlmTranslator.ProviderPreset.get_by_value(url)
        )
        with QSignalBlocker(self.__llm_preset_box):
            self.__llm_preset_box.setCurrentValue(preset)

        self.__llm_base_url_entry.setEnabled(preset is None)
        self.changed_signal.emit()

    def __load_llm_models(self) -> None:
        if self.__llm_model_thread is not None and self.__llm_model_thread.isRunning():
            return

        self.__llm_load_models_button.setDisabled(True)
        self.__llm_model_spinner.show()

        base_url: str = self.__llm_base_url_entry.text().strip()
        api_key: Optional[str] = self.__llm_api_key_entry.text().strip() or None
        self.__llm_model_thread = Thread(
            lambda: LlmTranslator.list_models(base_url, api_key)
        )
        self.__llm_model_thread.finished.connect(self.__on_llm_models_loaded)
        self.__llm_model_thread.start()

    def __on_llm_models_loaded(self) -> None:
        assert self.__llm_model_thread is not None

        self.__llm_model_box.clear()
        self.__llm_model_spinner.hide()
        self.__llm_load_models_button.setEnabled(True)

        result: list[str] | Exception = self.__llm_model_thread.get_result()
        self.__llm_model_thread = None

        if isinstance(result, Exception):
            raise result

        self.__llm_model_box.addItems(result)

    def __reset_llm_system_prompt(self) -> None:
        default_system_prompt: str = TranslatorConfig.get_default_value(
            "llm_system_prompt", str
        )
        self.__llm_system_prompt_edit.setPlainText(default_system_prompt)

    def __add_glossary_term(self) -> None:
        dialog = GlossaryTermDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.__glossary_editor.addItem(
                GlossaryTerm(original=dialog.original, translation=dialog.translation)
            )

    def __edit_glossary_term(self, term: GlossaryTerm) -> None:
        dialog = GlossaryTermDialog(self, term)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            term.original = dialog.original
            term.translation = dialog.translation
            self.__glossary_editor.updateItem(term)

    def __get_glossary(self) -> dict[str, str]:
        glossary: dict[str, str] = {}
        originals: set[str] = set()
        for term in self.__glossary_editor.getItems():
            if term.original.lower() in originals:
                raise ConfigValidationError(
                    self.tr("The glossary contains the term multiple times:")
                    + f" {term.original}"
                )

            originals.add(term.original.lower())
            glossary[term.original] = term.translation

        return glossary

    @override
    def validate(self) -> None:
        self.__get_glossary()

        self.__llm_load_models_button.setEnabled(
            bool(self.__llm_base_url_entry.text().strip())
        )
        default_system_prompt: str = TranslatorConfig.get_default_value(
            "llm_system_prompt", str
        )
        self.__llm_reset_prompt_button.setEnabled(
            self.__llm_system_prompt_edit.toPlainText().strip() != default_system_prompt
        )

        match self.__api_selector.getCurrentValue():
            case TranslatorApi.DeepL if not self.__deepl_api_key_entry.text().strip():
                raise ConfigValidationError(
                    self.tr("An API key is required for DeepL translator!")
                )

            case TranslatorApi.Llm if not self.__llm_base_url_entry.text().strip():
                raise ConfigValidationError(
                    self.tr("A base URL is required for the LLM translator!")
                )

            case TranslatorApi.Llm if not self.__llm_model_box.currentText().strip():
                raise ConfigValidationError(
                    self.tr("A model is required for the LLM translator!")
                )

    @override
    def apply(self) -> None:
        with self._config_manager.edit():
            self._config.translator = self.__api_selector.getCurrentValue()
            self._config.deepl_api_key = (
                self.__deepl_api_key_entry.text().strip() or None
            )
            self._config.show_confirmation_dialogs = (
                self.__show_confirmations_box.isChecked()
            )
            self._config.max_parallel_requests = self.__max_requests_box.value()
            self._config.glossary = self.__get_glossary()
            self._config.llm_base_url = self.__llm_base_url_entry.text().strip() or None
            self._config.llm_api_key = self.__llm_api_key_entry.text().strip() or None
            self._config.llm_model = self.__llm_model_box.currentText().strip() or None
            self._config.llm_temperature = (
                self.__llm_temperature_box.value()
                if self.__llm_temperature_box.value() >= 0
                else None
            )
            self._config.llm_system_prompt = (
                self.__llm_system_prompt_edit.toPlainText().strip()
            )
