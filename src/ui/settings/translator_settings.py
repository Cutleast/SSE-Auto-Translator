"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QPushButton, QWidget

from app_context import AppContext
from core.config.translator_config import TranslatorConfig
from core.translator_api import AVAILABLE_APIS
from core.translator_api.translator import Translator
from ui.widgets.key_entry import KeyEntry


class TranslatorSettings(QWidget):
    """
    Widget for translator API settings.
    """

    on_change_signal = Signal()
    """
    This signal gets emitted every time
    the user changes some setting.
    """

    translator_config: TranslatorConfig

    def __init__(self) -> None:
        super().__init__()

        self.translator_config = AppContext.get_app().translator_config

        self.setObjectName("transparent")

        # TODO: Refactor this

        flayout = QFormLayout()
        self.setLayout(flayout)

        # Translator
        self.translator_box = QComboBox()
        self.translator_box.setEditable(False)
        self.translator_box.addItems([translator.name for translator in AVAILABLE_APIS])
        self.translator_box.setCurrentText(self.translator_config.translator.name)
        self.translator_box.currentTextChanged.connect(self.on_change)
        flayout.addRow(self.tr("Translator API"), self.translator_box)

        # API Key
        api_key_label = QLabel(self.tr("Translator API Key"))
        self.api_key_entry = KeyEntry()
        self.api_key_entry.setDisabled(True)
        self.api_key_entry.textChanged.connect(self.on_change)
        if self.translator_config.api_key:
            self.api_key_entry.setText(self.translator_config.api_key)
            self.api_key_entry.setDisabled(False)
        flayout.addRow(api_key_label, self.api_key_entry)

        # TODO: Make this dynamic depending on the selected translator
        self.translator_box.currentTextChanged.connect(
            lambda text: (
                self.api_key_entry.setEnabled(text == "DeepL"),
                api_key_label.setEnabled(text == "DeepL"),
            )
        )

        # Reset Confirmation Dialogs
        reset_confirmations_button = QPushButton(
            self.tr("Show Confirmation Dialogs again")
        )
        reset_confirmations_button.setDisabled(
            self.translator_config.show_confirmation_dialogs
        )

        def reset_confirmations() -> None:
            self.translator_config.show_confirmation_dialogs = True
            self.translator_config.save()

            reset_confirmations_button.setDisabled(True)

        reset_confirmations_button.clicked.connect(reset_confirmations)
        flayout.addRow(reset_confirmations_button)

    def on_change(self, *args: Any) -> None:
        """
        This emits change signal without passing parameters.
        """

        self.on_change_signal.emit()

    def save_settings(self) -> None:
        translators: dict[str, type[Translator]] = {
            translator.name: translator for translator in AVAILABLE_APIS
        }

        self.translator_config.translator = translators[
            self.translator_box.currentText()
        ]
        self.translator_config.api_key = self.api_key_entry.text()

        self.translator_config.save()
