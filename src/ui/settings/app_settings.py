"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path
from typing import override

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.filesystem import get_folder_size
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.core.utilities.scale import scale_value
from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.widgets.browse_edit import BrowseLineEdit
from cutleast_core_lib.ui.widgets.color_edit import ColorLineEdit
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown
from PySide6.QtCore import QLocale
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.utilities.localisation import Language


class AppSettings(SettingsPage[AppConfig]):
    """
    Page for application settings.
    """

    cache: Cache

    __vlayout: QVBoxLayout

    __logs_num_box: QSpinBox
    __log_level_box: EnumDropdown[Logger.Level]
    __app_lang_box: EnumDropdown[Language]
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

    def __init__(self, initial_config: AppConfig, cache: Cache) -> None:
        self.cache = cache

        super().__init__(initial_config)

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
        self.__logs_num_box.valueChanged.connect(lambda _: self.changed_signal.emit())
        self.__logs_num_box.valueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        basic_flayout.addRow(
            "*" + self.tr("Number of newest log files to keep"), self.__logs_num_box
        )

        self.__log_level_box = EnumDropdown(
            Logger.Level, self._initial_config.log_level
        )
        self.__log_level_box.installEventFilter(self)
        self.__log_level_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__log_level_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        basic_flayout.addRow("*" + self.tr("Log Level"), self.__log_level_box)

        self.__app_lang_box = EnumDropdown(Language, self._initial_config.language)
        self.__app_lang_box.installEventFilter(self)
        self.__app_lang_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__app_lang_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        basic_flayout.addRow("*" + self.tr("App language"), self.__app_lang_box)

        self.__accent_color_entry = ColorLineEdit(
            [AppConfig.get_default_value("accent_color", str)]
        )
        self.__accent_color_entry.installEventFilter(self)
        self.__accent_color_entry.setText(self._initial_config.accent_color)
        self.__accent_color_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__accent_color_entry.textChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        basic_flayout.addRow("*" + self.tr("Accent Color"), self.__accent_color_entry)

        self.__clear_cache_button = QPushButton(
            self.tr(
                "Clear Cache (This will reset all mod file states "
                "and delete cached API requests!)"
            )
        )
        self.__clear_cache_button.clicked.connect(self.__clear_cache)
        self.__clear_cache_button.setEnabled(self.cache.path.is_dir())
        if self.cache.path.is_dir():
            self.__clear_cache_button.setText(
                self.__clear_cache_button.text()
                + f" ({scale_value(get_folder_size(self.cache.path))})"
            )
        basic_flayout.addRow(self.__clear_cache_button)

    def __init_path_settings(self) -> None:
        cur_path: Path = get_current_path()

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
        self.__output_path_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
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
        self.__temp_path_entry.textChanged.connect(lambda _: self.changed_signal.emit())
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
        self.__downloads_path_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
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
        self.__confidence_box.valueChanged.connect(lambda _: self.changed_signal.emit())
        self.__confidence_box.valueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
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
        self.__bind_nxm_checkbox.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__bind_nxm_checkbox.stateChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        behavior_flayout.addRow(self.__bind_nxm_checkbox)

        self.__use_spell_check_checkbox = QCheckBox(
            self.tr(
                "Enable Spell Checking in Translation Editor (Warning: could be slow)"
            )
        )
        self.__use_spell_check_checkbox.setChecked(self._initial_config.use_spell_check)
        self.__use_spell_check_checkbox.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        behavior_flayout.addRow(self.__use_spell_check_checkbox)

        self.__auto_import_checkbox = QCheckBox(
            self.tr("Automatically import installed translations into the database")
        )
        self.__auto_import_checkbox.setChecked(
            self._initial_config.auto_import_translations
        )
        self.__auto_import_checkbox.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
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
            lambda _: self.changed_signal.emit()
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
        self.__double_click_strings.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        behavior_flayout.addRow(self.__double_click_strings)

    def __clear_cache(self) -> None:
        self.cache.clear_caches()
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
        config.log_level = self.__log_level_box.getCurrentValue()
        config.language = self.__app_lang_box.getCurrentValue()
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
