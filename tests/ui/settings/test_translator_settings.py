"""
Copyright (c) Cutleast
"""

from copy import copy

import pytest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.enum_selector import EnumSelector
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from PySide6.QtWidgets import QCheckBox, QLineEdit, QPushButton
from pytestqt.qtbot import QtBot

from core.config.translator_config import TranslatorConfig
from core.translator_api.lm_studio import LMStudioTranslator
from core.translator_api.translator_api import TranslatorApi
from core.user_data.user_data import UserData
from tests.base_test import BaseTest
from ui.settings.translator_settings import TranslatorSettings
from ui.widgets.completion_box import CompletionBox


class TestTranslatorSettings(BaseTest):
    """
    Tests `ui.settings.translator_settings.TranslatorSettings`.
    """

    API_SELECTOR: tuple[str, type[EnumSelector[TranslatorApi]]] = (
        "api_selector",
        EnumSelector[TranslatorApi],
    )
    API_KEY_ENTRY: tuple[str, type[KeyLineEdit]] = "api_key_entry", KeyLineEdit
    LM_STUDIO_BASE_URL_ENTRY: tuple[str, type[QLineEdit]] = (
        "lm_studio_base_url_entry",
        QLineEdit,
    )
    LM_STUDIO_MODEL_ENTRY: tuple[str, type[CompletionBox]] = (
        "lm_studio_model_entry",
        CompletionBox,
    )
    LM_STUDIO_RELOAD_MODELS_BUTTON: tuple[str, type[QPushButton]] = (
        "lm_studio_reload_models_button",
        QPushButton,
    )
    LM_STUDIO_USE_SERVER_PROMPT_BOX: tuple[str, type[QCheckBox]] = (
        "lm_studio_use_server_prompt_box",
        QCheckBox,
    )

    SHOW_CONFIRMATIONS_BOX: tuple[str, type[QCheckBox]] = (
        "show_confirmations_box",
        QCheckBox,
    )

    @pytest.fixture
    def translator_settings(
        self, user_data: UserData, qtbot: QtBot
    ) -> TranslatorSettings:
        """
        Returns a new `TranslatorSettings` instance for tests.
        """

        return TranslatorSettings(user_data.translator_config)

    def test_initial(
        self, translator_settings: TranslatorSettings, user_data: UserData
    ) -> None:
        """
        Tests the initial state of the `TranslatorSettings` instance.
        """

        # given
        translator_config: TranslatorConfig = user_data.translator_config

        api_selector: EnumSelector[TranslatorApi] = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.API_SELECTOR
        )
        api_key_entry: KeyLineEdit = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.API_KEY_ENTRY
        )
        lm_studio_base_url_entry: QLineEdit = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.LM_STUDIO_BASE_URL_ENTRY
        )
        lm_studio_model_entry: CompletionBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.LM_STUDIO_MODEL_ENTRY
        )
        lm_studio_reload_models_button: QPushButton = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.LM_STUDIO_RELOAD_MODELS_BUTTON
        )
        lm_studio_use_server_prompt_box: QCheckBox = Utils.get_private_field(
            translator_settings,
            *TestTranslatorSettings.LM_STUDIO_USE_SERVER_PROMPT_BOX,
        )

        show_confirmations_box: QCheckBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.SHOW_CONFIRMATIONS_BOX
        )

        # then
        assert api_selector.getCurrentValue() == translator_config.translator
        assert api_key_entry.isEnabled() == (
            translator_config.translator == TranslatorApi.DeepL
        )
        assert (api_key_entry.text().strip() or None) == translator_config.api_key
        assert lm_studio_base_url_entry.isEnabled() == (
            translator_config.translator == TranslatorApi.LMStudio
        )
        assert lm_studio_base_url_entry.text() == translator_config.lm_studio_base_url
        assert (
            lm_studio_model_entry.currentText().strip() or None
        ) == translator_config.lm_studio_model
        assert lm_studio_reload_models_button.isEnabled() == (
            translator_config.translator == TranslatorApi.LMStudio
        )
        assert lm_studio_use_server_prompt_box.isEnabled() == (
            translator_config.translator == TranslatorApi.LMStudio
        )
        assert (
            lm_studio_use_server_prompt_box.isChecked()
            == translator_config.lm_studio_use_server_prompt
        )

        assert (
            show_confirmations_box.isChecked()
            == translator_config.show_confirmation_dialogs
        )

    def test_apply(
        self, translator_settings: TranslatorSettings, user_data: UserData
    ) -> None:
        """
        Tests the `apply` method of the `AppSettings` instance.
        """

        # given
        translator_config: TranslatorConfig = user_data.translator_config
        old_config: TranslatorConfig = copy(translator_config)

        # when
        translator_settings.apply(translator_config)

        # then
        assert translator_config == old_config

    def test_loads_lm_studio_models(
        self, translator_settings: TranslatorSettings, mocker
    ) -> None:
        """
        Tests that LM Studio models are loaded into the dropdown.
        """

        mocker.patch.object(
            LMStudioTranslator,
            "list_models",
            return_value=["qwen-3-8b", "mistral-small-3.1"],
        )

        api_selector: EnumSelector[TranslatorApi] = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.API_SELECTOR
        )
        lm_studio_model_entry: CompletionBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.LM_STUDIO_MODEL_ENTRY
        )

        api_selector.setCurrentValue(TranslatorApi.LMStudio)

        assert lm_studio_model_entry.count() == 2
        assert lm_studio_model_entry.itemText(0) == "qwen-3-8b"
        assert lm_studio_model_entry.itemText(1) == "mistral-small-3.1"
