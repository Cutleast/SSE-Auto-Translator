"""
Copyright (c) Cutleast
"""

from copy import copy

import pytest
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QPushButton, QSpinBox

from app import App
from core.config.app_config import AppConfig
from core.utilities.localisation import Language
from core.utilities.logger import Logger
from tests.app_test import AppTest
from tests.utils import Utils
from ui.settings.app_settings import AppSettings
from ui.widgets.browse_edit import BrowseLineEdit
from ui.widgets.color_entry import ColorLineEdit
from ui.widgets.enum_dropdown import EnumDropdown

from ..ui_test import UiTest


class TestAppSettings(UiTest, AppTest):
    """
    Tests `ui.settings.app_settings.AppSettings`.
    """

    LOGS_NUM_BOX: tuple[str, type[QSpinBox]] = "logs_num_box", QSpinBox
    LOG_LEVEL_BOX: tuple[str, type[EnumDropdown[Logger.Level]]] = (
        "log_level_box",
        EnumDropdown[Logger.Level],
    )
    APP_LANG_BOX: tuple[str, type[EnumDropdown[Language]]] = (
        "app_lang_box",
        EnumDropdown[Language],
    )
    ACCENT_COLOR_ENTRY: tuple[str, type[ColorLineEdit]] = (
        "accent_color_entry",
        ColorLineEdit,
    )
    CLEAR_CACHE_BUTTON: tuple[str, type[QPushButton]] = (
        "clear_cache_button",
        QPushButton,
    )

    OUTPUT_PATH_ENTRY: tuple[str, type[BrowseLineEdit]] = (
        "output_path_entry",
        BrowseLineEdit,
    )
    TEMP_PATH_ENTRY: tuple[str, type[BrowseLineEdit]] = (
        "temp_path_entry",
        BrowseLineEdit,
    )
    DOWNLOADS_PATH_ENTRY: tuple[str, type[BrowseLineEdit]] = (
        "downloads_path_entry",
        BrowseLineEdit,
    )

    CONFIDENCE_BOX: tuple[str, type[QDoubleSpinBox]] = "confidence_box", QDoubleSpinBox
    BIND_NXM_CHECKBOX: tuple[str, type[QCheckBox]] = "bind_nxm_checkbox", QCheckBox
    USE_SPELL_CHECK_CHECKBOX: tuple[str, type[QCheckBox]] = (
        "use_spell_check_checkbox",
        QCheckBox,
    )
    AUTO_IMPORT_CHECKBOX: tuple[str, type[QCheckBox]] = (
        "auto_import_checkbox",
        QCheckBox,
    )
    AUTO_CREATE_DB_TRANSLATIONS_CHECKBOX: tuple[str, type[QCheckBox]] = (
        "auto_create_db_translations_checkbox",
        QCheckBox,
    )
    DOUBLE_CLICK_STRINGS: tuple[str, type[QCheckBox]] = (
        "double_click_strings",
        QCheckBox,
    )

    @pytest.fixture
    def app_settings(self, app_context: App) -> AppSettings:
        """
        Returns a new `AppSettings` instance for the given `App` instance.
        """

        return AppSettings(app_context.app_config)

    def test_initial(self, app_settings: AppSettings, app_context: App) -> None:
        """
        Tests the initial state of the `AppSettings` instance.
        """

        # given
        app_config: AppConfig = app_context.app_config

        logs_num_box: QSpinBox = Utils.get_private_field(
            app_settings, *TestAppSettings.LOGS_NUM_BOX
        )
        log_level_box: EnumDropdown[Logger.Level] = Utils.get_private_field(
            app_settings, *TestAppSettings.LOG_LEVEL_BOX
        )
        app_lang_box: EnumDropdown[Language] = Utils.get_private_field(
            app_settings, *TestAppSettings.APP_LANG_BOX
        )
        accent_color_entry: ColorLineEdit = Utils.get_private_field(
            app_settings, *TestAppSettings.ACCENT_COLOR_ENTRY
        )
        clear_cache_button: QPushButton = Utils.get_private_field(
            app_settings, *TestAppSettings.CLEAR_CACHE_BUTTON
        )

        output_path_entry: BrowseLineEdit = Utils.get_private_field(
            app_settings, *TestAppSettings.OUTPUT_PATH_ENTRY
        )
        temp_path_entry: BrowseLineEdit = Utils.get_private_field(
            app_settings, *TestAppSettings.TEMP_PATH_ENTRY
        )
        downloads_path_entry: BrowseLineEdit = Utils.get_private_field(
            app_settings, *TestAppSettings.DOWNLOADS_PATH_ENTRY
        )

        confidence_box: QDoubleSpinBox = Utils.get_private_field(
            app_settings, *TestAppSettings.CONFIDENCE_BOX
        )
        bind_nxm_checkbox: QCheckBox = Utils.get_private_field(
            app_settings, *TestAppSettings.BIND_NXM_CHECKBOX
        )
        use_spell_check_checkbox: QCheckBox = Utils.get_private_field(
            app_settings, *TestAppSettings.USE_SPELL_CHECK_CHECKBOX
        )
        auto_import_checkbox: QCheckBox = Utils.get_private_field(
            app_settings, *TestAppSettings.AUTO_IMPORT_CHECKBOX
        )
        auto_create_db_translations_checkbox: QCheckBox = Utils.get_private_field(
            app_settings, *TestAppSettings.AUTO_CREATE_DB_TRANSLATIONS_CHECKBOX
        )
        double_click_strings: QCheckBox = Utils.get_private_field(
            app_settings, *TestAppSettings.DOUBLE_CLICK_STRINGS
        )

        # then
        assert logs_num_box.value() == app_config.log_num_of_files
        assert log_level_box.getCurrentValue() == app_config.log_level
        assert app_lang_box.getCurrentValue() == app_config.language
        assert accent_color_entry.text() == app_config.accent_color
        assert clear_cache_button.isEnabled() == app_context.cache.path.is_dir()

        assert output_path_entry.text() == str(app_config.output_path or "")
        assert temp_path_entry.text() == str(app_config.temp_path or "")
        assert downloads_path_entry.text() == str(app_config.downloads_path or "")

        assert confidence_box.value() == app_config.detector_confidence
        assert bind_nxm_checkbox.isChecked() == app_config.auto_bind_nxm
        assert use_spell_check_checkbox.isChecked() == app_config.use_spell_check
        assert auto_import_checkbox.isChecked() == app_config.auto_import_translations
        assert (
            auto_create_db_translations_checkbox.isChecked()
            == app_config.auto_create_database_translations
        )
        assert (
            double_click_strings.isChecked() == app_config.show_strings_on_double_click
        )

    def test_apply(self, app_settings: AppSettings, app_context: App) -> None:
        """
        Tests the `apply` method of the `AppSettings` instance.
        """

        # given
        app_config: AppConfig = app_context.app_config
        old_config: AppConfig = copy(app_config)

        # when
        app_settings.apply(app_config)

        # then
        assert app_config == old_config
