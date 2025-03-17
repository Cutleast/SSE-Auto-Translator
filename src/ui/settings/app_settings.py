"""
Copyright (c) Cutleast
"""

import os
from typing import override

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.cache.cache import Cache
from core.config.app_config import AppConfig
from core.utilities.filesystem import get_folder_size
from core.utilities.logger import Logger
from core.utilities.path import Path
from core.utilities.scale import scale_value
from ui.widgets.browse_edit import BrowseLineEdit
from ui.widgets.color_entry import ColorLineEdit

from .settings_page import SettingsPage


class AppSettings(SettingsPage[AppConfig]):
    """
    Page for application settings.
    """

    __vlayout: QVBoxLayout

    __logs_num_box: QSpinBox
    __log_level_box: QComboBox
    __app_lang_box: QComboBox
    __accent_color_entry: ColorLineEdit
    __clear_cache_button: QPushButton

    __output_path_entry: BrowseLineEdit
    __temp_path_entry: BrowseLineEdit
    __downloads_path_entry: BrowseLineEdit

    __confidence_box: QDoubleSpinBox
    __bind_nxm_checkbox: QCheckBox
    __use_spell_check_checkbox: QCheckBox
    __auto_import_checkbox: QCheckBox
    __auto_create_db_translations_checkbox: QCheckBox
    __double_click_strings: QCheckBox

    @override
    def _init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        self.__vlayout = QVBoxLayout()
        scroll_widget.setLayout(self.__vlayout)

        self.__init_basic_settings()
        self.__init_path_settings()
        self.__init_behavior_settings()

    def __init_basic_settings(self) -> None:
        basic_group = QGroupBox(self.tr("Basic App Settings"))
        self.__vlayout.addWidget(basic_group)
        basic_flayout = QFormLayout()
        basic_group.setLayout(basic_flayout)

        self.__logs_num_box = QSpinBox()
        self.__logs_num_box.installEventFilter(self)
        self.__logs_num_box.setRange(-1, 100)
        self.__logs_num_box.setValue(self._initial_config.log_num_of_files)
        self.__logs_num_box.valueChanged.connect(self._on_change)
        self.__logs_num_box.valueChanged.connect(self._on_restart_required)
        basic_flayout.addRow(
            "*" + self.tr("Number of newest log files to keep"), self.__logs_num_box
        )

        self.__log_level_box = QComboBox()
        self.__log_level_box.installEventFilter(self)
        self.__log_level_box.addItems(
            [loglevel.name.capitalize() for loglevel in Logger.LogLevel]
        )
        self.__log_level_box.setCurrentText(
            self._initial_config.log_level.name.capitalize()
        )
        self.__log_level_box.currentTextChanged.connect(self._on_change)
        self.__log_level_box.currentTextChanged.connect(self._on_restart_required)
        basic_flayout.addRow("*" + self.tr("Log Level"), self.__log_level_box)

        self.__app_lang_box = QComboBox()
        self.__app_lang_box.installEventFilter(self)
        self.__app_lang_box.addItem("System")
        # TODO: Make this dynamic
        self.__app_lang_box.addItems(["de_DE", "en_US", "ru_RU", "zh_CN"])
        self.__app_lang_box.setCurrentText(self._initial_config.language)
        self.__app_lang_box.currentTextChanged.connect(self._on_change)
        self.__app_lang_box.currentTextChanged.connect(self._on_restart_required)
        basic_flayout.addRow("*" + self.tr("App language"), self.__app_lang_box)

        self.__accent_color_entry = ColorLineEdit(
            [self._initial_config.get_default_value("accent_color")]
        )
        self.__accent_color_entry.installEventFilter(self)
        self.__accent_color_entry.setText(self._initial_config.accent_color)
        self.__accent_color_entry.textChanged.connect(self._on_change)
        self.__accent_color_entry.textChanged.connect(self._on_restart_required)
        basic_flayout.addRow("*" + self.tr("Accent Color"), self.__accent_color_entry)

        self.__clear_cache_button = QPushButton(
            self.tr(
                "Clear Cache (This will reset all mod file states "
                "and delete cached API requests!)"
            )
        )
        self.__clear_cache_button.clicked.connect(self.__clear_cache)
        cache: Cache = AppContext.get_app().cache
        self.__clear_cache_button.setEnabled(cache.path.is_dir())
        if cache.path.is_dir():
            self.__clear_cache_button.setText(
                self.__clear_cache_button.text()
                + f" ({scale_value(get_folder_size(cache.path))})"
            )
        basic_flayout.addRow(self.__clear_cache_button)

    def __init_path_settings(self) -> None:
        cur_path: Path = AppContext.get_app().cur_path

        path_group = QGroupBox(self.tr("Path Settings"))
        self.__vlayout.addWidget(path_group)
        path_flayout = QFormLayout()
        path_group.setLayout(path_flayout)

        # Output path
        self.__output_path_entry = BrowseLineEdit()
        self.__output_path_entry.setPlaceholderText(
            self.tr("Default: ") + str(cur_path / "SSE-AT Output")
        )
        self.__output_path_entry.setText(str(self._initial_config.output_path or ""))
        self.__output_path_entry.textChanged.connect(self._on_change)
        self.__output_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        path_flayout.addRow(
            self.tr("Path for Output Mod") + self.tr(" (No Restart Required)"),
            self.__output_path_entry,
        )

        # Temp path
        self.__temp_path_entry = BrowseLineEdit()
        self.__temp_path_entry.setPlaceholderText(
            self.tr("Default: ") + (os.getenv("TEMP") or "")
        )
        self.__temp_path_entry.setText(str(self._initial_config.temp_path or ""))
        self.__temp_path_entry.textChanged.connect(self._on_change)
        self.__temp_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        path_flayout.addRow(
            self.tr("Path for Temporary Folder")
            + "\n"
            + self.tr("(for temporary files, will be wiped after exit!)"),
            self.__temp_path_entry,
        )

        # Downloads path
        self.__downloads_path_entry = BrowseLineEdit()
        self.__downloads_path_entry.setPlaceholderText(
            self.tr("Defaults to Temporary Folder configured above")
        )
        self.__downloads_path_entry.setText(
            str(self._initial_config.downloads_path or "")
        )
        self.__downloads_path_entry.textChanged.connect(self._on_change)
        self.__downloads_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        path_flayout.addRow(self.tr("Downloads Path"), self.__downloads_path_entry)

    def __init_behavior_settings(self) -> None:
        behavior_group = QGroupBox(self.tr("Behavior Settings"))
        self.__vlayout.addWidget(behavior_group)
        behavior_flayout = QFormLayout()
        behavior_group.setLayout(behavior_flayout)

        self.__confidence_box = QDoubleSpinBox()
        self.__confidence_box.installEventFilter(self)
        self.__confidence_box.setLocale(QLocale.Language.English)
        self.__confidence_box.setRange(0, 1)
        self.__confidence_box.setSingleStep(0.05)
        self.__confidence_box.setValue(self._initial_config.detector_confidence)
        self.__confidence_box.valueChanged.connect(self._on_change)
        self.__confidence_box.valueChanged.connect(self._on_restart_required)
        behavior_flayout.addRow(
            "*" + self.tr("Language Detector Confidence"), self.__confidence_box
        )

        self.__bind_nxm_checkbox = QCheckBox(
            "*"
            + self.tr(
                'Automatically bind to "Mod Manager Download" '
                "Buttons on Nexus Mods on Startup"
            )
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.__bind_nxm_checkbox.setToolTip(
            self.tr(
                "This will automatically bind to Mod Manager downloads and unbind "
                "when SSE-AT is closed.\nThis feature is considered experimental because "
                "a crash might prevent it from unbinding properly."
            )
        )
        self.__bind_nxm_checkbox.setChecked(self._initial_config.auto_bind_nxm)
        self.__bind_nxm_checkbox.stateChanged.connect(self._on_change)
        self.__bind_nxm_checkbox.stateChanged.connect(self._on_restart_required)
        behavior_flayout.addRow(self.__bind_nxm_checkbox)

        self.__use_spell_check_checkbox = QCheckBox(
            self.tr("Enable Spell Checking in Translation Editor")
        )
        self.__use_spell_check_checkbox.setChecked(self._initial_config.use_spell_check)
        self.__use_spell_check_checkbox.stateChanged.connect(self._on_change)
        behavior_flayout.addRow(self.__use_spell_check_checkbox)

        self.__auto_import_checkbox = QCheckBox(
            self.tr("Automatically import installed translations into the database")
        )
        self.__auto_import_checkbox.setChecked(
            self._initial_config.auto_import_translations
        )
        self.__auto_import_checkbox.stateChanged.connect(self._on_change)
        behavior_flayout.addRow(self.__auto_import_checkbox)

        self.__auto_create_db_translations_checkbox = QCheckBox(
            self.tr(
                "Automatically create translations for mod files that are entirely "
                "covered by installed translations"
            )
        )
        self.__auto_create_db_translations_checkbox.setChecked(
            self._initial_config.auto_create_database_translations
        )
        self.__auto_create_db_translations_checkbox.stateChanged.connect(
            self._on_change
        )
        behavior_flayout.addRow(self.__auto_create_db_translations_checkbox)

        self.__double_click_strings = QCheckBox(
            self.tr(
                "Show strings when double clicking a mod or mod file "
                'in the modlist or a translation in the "Translations" tab'
            )
        )
        self.__double_click_strings.setChecked(
            self._initial_config.show_strings_on_double_click
        )
        self.__double_click_strings.stateChanged.connect(self._on_change)
        behavior_flayout.addRow(self.__double_click_strings)

    def __clear_cache(self) -> None:
        cache: Cache = AppContext.get_app().cache
        cache.clear_caches()
        self.__clear_cache_button.setText(
            self.tr(
                "Clear Cache (This will reset all mod file states "
                "and delete cached API requests!)"
            )
        )
        self.__clear_cache_button.setEnabled(False)

    @override
    def apply(self, config: AppConfig) -> None:
        config.log_num_of_files = self.__logs_num_box.value()
        config.log_level = Logger.LogLevel[self.__log_level_box.currentText().upper()]
        config.language = self.__app_lang_box.currentText()
        config.accent_color = self.__accent_color_entry.text()
        config.detector_confidence = self.__confidence_box.value()
        config.auto_bind_nxm = self.__bind_nxm_checkbox.isChecked()
        config.use_spell_check = self.__use_spell_check_checkbox.isChecked()
        config.auto_import_translations = self.__auto_import_checkbox.isChecked()
        config.auto_create_database_translations = (
            self.__auto_create_db_translations_checkbox.isChecked()
        )
        config.show_strings_on_double_click = self.__double_click_strings.isChecked()
        config.output_path = (
            Path(self.__output_path_entry.text().strip())
            if self.__output_path_entry.text().strip()
            else None
        )
        config.temp_path = (
            Path(self.__temp_path_entry.text().strip())
            if self.__temp_path_entry.text().strip()
            else None
        )
        config.downloads_path = (
            Path(self.__downloads_path_entry.text().strip())
            if self.__downloads_path_entry.text().strip()
            else None
        )
