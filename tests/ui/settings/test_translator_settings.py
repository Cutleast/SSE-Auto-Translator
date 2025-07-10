"""
Copyright (c) Cutleast
"""

from copy import copy

import pytest
from PySide6.QtWidgets import QCheckBox

from app import App
from core.config.translator_config import TranslatorConfig
from core.translator_api.translator_api import TranslatorApi
from tests.app_test import AppTest
from tests.utils import Utils
from ui.settings.translator_settings import TranslatorSettings
from ui.widgets.enum_dropdown import EnumDropdown
from ui.widgets.key_entry import KeyEntry

from ..ui_test import UiTest


class TestTranslatorSettings(UiTest, AppTest):
    """
    Tests `ui.settings.translator_settings.TranslatorSettings`.
    """

    TRANSLATOR_BOX: tuple[str, type[EnumDropdown[TranslatorApi]]] = (
        "translator_box",
        EnumDropdown[TranslatorApi],
    )
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

        return TranslatorSettings(app_context.translator_config, self.cache())

    def test_initial(
        self, translator_settings: TranslatorSettings, app_context: App
    ) -> None:
        """
        Tests the initial state of the `TranslatorSettings` instance.
        """

        # given
        translator_config: TranslatorConfig = app_context.translator_config

        translator_box: EnumDropdown[TranslatorApi] = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.TRANSLATOR_BOX
        )
        api_key_entry: KeyEntry = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.API_KEY_ENTRY
        )

        show_confirmations_box: QCheckBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.SHOW_CONFIRMATIONS_BOX
        )

        # then
        assert translator_box.getCurrentValue() == translator_config.translator
        assert api_key_entry.isEnabled() == (
            translator_config.translator == TranslatorApi.DeepL
        )
        assert (api_key_entry.text().strip() or None) == translator_config.api_key

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
        old_config: TranslatorConfig = copy(translator_config)

        # when
        translator_settings.apply(translator_config)

        # then
        assert translator_config == old_config
