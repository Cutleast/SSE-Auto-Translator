"""
Copyright (c) Cutleast
"""

from typing import cast, override

from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.widgets.enum_radiobutton_widget import EnumRadiobuttonsWidget
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from cutleast_core_lib.ui.widgets.spin_box import SpinBox
from cutleast_core_lib.ui.widgets.tree_widget_editor import TreeWidgetEditor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.config.translator_config import TranslatorConfig
from core.translator.apis import TranslatorApi

from .glossary_term import GlossaryTerm
from .glossary_term_dialog import GlossaryTermDialog


class TranslatorSettings(SettingsPage[TranslatorConfig]):
    """
    Widget for translator API settings.
    """

    __vlayout: QVBoxLayout

    __api_selector: EnumRadiobuttonsWidget[TranslatorApi]
    __deepl_group: QGroupBox
    __deepl_api_key_entry: KeyLineEdit

    __show_confirmations_box: QCheckBox
    __max_requests_box: SpinBox
    __glossary_editor: TreeWidgetEditor[GlossaryTerm]

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

        self.__api_selector.currentValueChanged.connect(self.__on_api_changed)
        self.__on_api_changed(self._config.translator)

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
        self.__api_selector.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        api_glayout.addWidget(self.__api_selector, 0, 1)

        self.__show_confirmations_box = QCheckBox(
            self.tr("Ask for confirmation before starting a batch machine translation")
        )
        self.__show_confirmations_box.setChecked(self._config.show_confirmation_dialogs)
        self.__show_confirmations_box.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
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
        self.__max_requests_box.valueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
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
        self.__glossary_editor.changed.connect(self.changed_signal.emit)
        self.__glossary_editor.onAdd.connect(self.__add_glossary_term)
        self.__glossary_editor.onEdit.connect(self.__edit_glossary_term)
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

    def __on_api_changed(self, translator_api: TranslatorApi) -> None:
        self.__deepl_group.setVisible(translator_api == TranslatorApi.DeepL)

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

        match self.__api_selector.getCurrentValue():
            case TranslatorApi.DeepL if not self.__deepl_api_key_entry.text().strip():
                raise ConfigValidationError(
                    self.tr("An API key is required for DeepL translator!")
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
