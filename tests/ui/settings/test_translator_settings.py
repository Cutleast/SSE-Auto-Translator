"""
Copyright (c) Cutleast
"""

from typing import Any

import pytest
from PySide6.QtWidgets import QCheckBox, QComboBox

from app import App
from core.config.translator_config import TranslatorConfig
from tests.app_test import AppTest
from tests.utils import Utils
from ui.settings.translator_settings import TranslatorSettings
from ui.widgets.key_entry import KeyEntry

from ..ui_test import UiTest


class TestTranslatorSettings(UiTest, AppTest):
    """
    Tests `ui.settings.translator_settings.TranslatorSettings`.
    """

    TRANSLATOR_BOX: tuple[str, type[QComboBox]] = "translator_box", QComboBox
    API_KEY_ENTRY: tuple[str, type[KeyEntry]] = "api_key_entry", KeyEntry

    SHOW_CONFIRMATIONS_BOX: tuple[str, type[QCheckBox]] = (
        "show_confirmations_box",
        QCheckBox,
    )

    @pytest.fixture
    def translator_settings(self, app_context: App) -> TranslatorSettings:
        """
        Returns a new `TranslatorSettings` instance for the given `App` instance.
        """

        return TranslatorSettings(app_context.translator_config)

    def test_initial(
        self, translator_settings: TranslatorSettings, app_context: App
    ) -> None:
        """
        Tests the initial state of the `TranslatorSettings` instance.
        """

        # given
        translator_config: TranslatorConfig = app_context.translator_config

        translator_box: QComboBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.TRANSLATOR_BOX
        )
        api_key_entry: KeyEntry = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.API_KEY_ENTRY
        )

        show_confirmations_box: QCheckBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.SHOW_CONFIRMATIONS_BOX
        )

        # then
        assert translator_box.currentText() == translator_config.translator.name
        assert api_key_entry.isEnabled() == (
            translator_config.translator.name == "DeepL"
        )
        assert api_key_entry.text() == translator_config.api_key

        assert (
            show_confirmations_box.isChecked()
            == translator_config.show_confirmation_dialogs
        )

    def test_apply(
        self, translator_settings: TranslatorSettings, app_context: App
    ) -> None:
        """
        Tests the `apply` method of the `AppSettings` instance.
        """

        # given
        translator_config: TranslatorConfig = app_context.translator_config
        old_config: dict[str, Any] = translator_config._settings.copy()  # type: ignore

        # when
        translator_settings.apply(translator_config)

        # then
        assert translator_config._settings == old_config  # type: ignore
