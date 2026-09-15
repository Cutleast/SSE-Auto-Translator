"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path
from typing import override

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.core.config.validation_utils import ValidationUtils
from cutleast_core_lib.core.filesystem.scanner import DirectoryScanner
from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.core.utilities.scale import scale_value
from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.theme.ui_mode import UiMode
from cutleast_core_lib.ui.widgets.browse_edit import BrowseLineEdit
from cutleast_core_lib.ui.widgets.color_edit import ColorLineEdit
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown
from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
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

    __cache: Cache

    __vlayout: QVBoxLayout

    __logs_num_box: QSpinBox
    __log_level_box: EnumDropdown[Logger.Level]
    __app_lang_box: EnumDropdown[Language]
    __ui_mode_box: EnumDropdown[UiMode]
    __accent_color_entry: ColorLineEdit
    __clear_cache_button: QPushButton

    __output_path_entry: BrowseLineEdit
    __temp_path_entry: BrowseLineEdit
    __downloads_path_entry: BrowseLineEdit

    __confidence_box: QDoubleSpinBox
    __download_threads_box: QSpinBox
    __worker_threads_box: QSpinBox
    __bind_nxm_checkbox: QCheckBox
    __use_spell_check_checkbox: QCheckBox
    __auto_import_checkbox: QCheckBox
    __auto_create_db_translations_checkbox: QCheckBox
    __double_click_strings: QCheckBox

    def __init__(self, initial_config: AppConfig, cache: Cache) -> None:
        """
        Args:
            initial_config (AppConfig): Initial configuration to load.
            cache (Cache): Cache instance to manage application cache.
        """

        self.__cache = cache

        super().__init__(initial_config)

    @override
    def _init_ui(self) -> None:
        scroll_widget = QWidget()
        self.setWidget(scroll_widget)

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__vlayout.setContentsMargins(4, 0, 4, 0)
        scroll_widget.setLayout(self.__vlayout)

        self.__init_basic_settings()
        self.__init_path_settings()
        self.__init_behavior_settings()

    def __init_basic_settings(self) -> None:
        basic_group = QGroupBox(self.tr("General App Settings"))
        self.__vlayout.addWidget(basic_group)
        basic_glayout = QGridLayout()
        basic_glayout.setColumnStretch(0, 1)
        basic_glayout.setColumnStretch(1, 1)
        basic_group.setLayout(basic_glayout)

        logs_num_label = QLabel("*" + self.tr("Number of newest log files to keep"))
        basic_glayout.addWidget(logs_num_label, 0, 0)

        self.__logs_num_box = QSpinBox()
        self.__logs_num_box.installEventFilter(self)
        self.__logs_num_box.setRange(-1, 100)
        self.__logs_num_box.setValue(self._initial_config.log_num_of_files)
        self.__logs_num_box.valueChanged.connect(lambda _: self.changed_signal.emit())
        self.__logs_num_box.valueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        basic_glayout.addWidget(self.__logs_num_box, 0, 1)

        log_level_label = QLabel("*" + self.tr("Log level"))
        basic_glayout.addWidget(log_level_label, 1, 0)

        self.__log_level_box = EnumDropdown(Logger.Level, self._initial_config.log_level)
        self.__log_level_box.installEventFilter(self)
        self.__log_level_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__log_level_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        basic_glayout.addWidget(self.__log_level_box, 1, 1)

        app_lang_label = QLabel("*" + self.tr("App language"))
        basic_glayout.addWidget(app_lang_label, 2, 0)

        self.__app_lang_box = EnumDropdown(Language, self._initial_config.language)
        self.__app_lang_box.installEventFilter(self)
        self.__app_lang_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__app_lang_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        basic_glayout.addWidget(self.__app_lang_box, 2, 1)

        ui_mode_label = QLabel(self.tr("UI mode"))
        basic_glayout.addWidget(ui_mode_label, 3, 0)

        self.__ui_mode_box = EnumDropdown(UiMode, self._initial_config.ui_mode)
        self.__ui_mode_box.installEventFilter(self)
        self.__ui_mode_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__ui_mode_box.currentValueChanged.connect(
            lambda _: self.theme_update_required_signal.emit()
        )
        basic_glayout.addWidget(self.__ui_mode_box, 3, 1)

        accent_color_label = QLabel(self.tr("Accent color"))
        basic_glayout.addWidget(accent_color_label, 4, 0)

        self.__accent_color_entry = ColorLineEdit(
            [AppConfig.get_default_value("accent_color", str)]
        )
        self.__accent_color_entry.installEventFilter(self)
        self.__accent_color_entry.setText(self._initial_config.accent_color)
        self.__accent_color_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__accent_color_entry.textChanged.connect(
            lambda _: self.theme_update_required_signal.emit()
        )
        basic_glayout.addWidget(self.__accent_color_entry, 4, 1)

        self.__clear_cache_button = QPushButton(
            self.tr(
                "Clear cache (This will reset all mod file states and delete cached API "
                "requests and more temporary data!)"
            )
        )
        self.__clear_cache_button.setProperty("destructive", True)
        self.__clear_cache_button.clicked.connect(self.__clear_cache)
        self.__clear_cache_button.setEnabled(self.__cache.path.is_dir())
        if self.__cache.path.is_dir():
            self.__clear_cache_button.setText(
                self.__clear_cache_button.text()
                + f" ({scale_value(DirectoryScanner.get_folder_size(self.__cache.path))})"
            )
        basic_glayout.addWidget(self.__clear_cache_button, 5, 0, 1, 2)

    def __init_path_settings(self) -> None:
        cur_path: Path = get_current_path()

        path_group = QGroupBox(self.tr("Path Settings"))
        self.__vlayout.addWidget(path_group)
        path_glayout = QGridLayout()
        path_glayout.setColumnStretch(0, 1)
        path_glayout.setColumnStretch(1, 1)
        path_group.setLayout(path_glayout)

        # Output path
        output_path_label = QLabel(self.tr("Path for output mod"))
        path_glayout.addWidget(output_path_label, 0, 0)

        self.__output_path_entry = BrowseLineEdit()
        self.__output_path_entry.setPlaceholderText(
            self.tr("Default: ") + str(cur_path / "SSE-AT Output")
        )
        self.__output_path_entry.setText(str(self._initial_config.output_path or ""))
        self.__output_path_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__output_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        path_glayout.addWidget(self.__output_path_entry, 0, 1)

        # Temp path
        temp_path_label = QLabel(
            self.tr("Path for temporary folder")
            + "\n"
            + self.tr("(for temporary files, will be wiped after exit!)")
        )
        path_glayout.addWidget(temp_path_label, 1, 0)

        self.__temp_path_entry = BrowseLineEdit()
        self.__temp_path_entry.setPlaceholderText(
            self.tr("Default: ") + (os.getenv("TEMP") or "")
        )
        self.__temp_path_entry.setText(str(self._initial_config.temp_path or ""))
        self.__temp_path_entry.textChanged.connect(lambda _: self.changed_signal.emit())
        self.__temp_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        path_glayout.addWidget(self.__temp_path_entry, 1, 1)

        # Downloads path
        downloads_path_label = QLabel(self.tr("Downloads path"))
        path_glayout.addWidget(downloads_path_label, 2, 0)

        self.__downloads_path_entry = BrowseLineEdit()
        self.__downloads_path_entry.setPlaceholderText(
            self.tr("Defaults to temporary folder configured above")
        )
        self.__downloads_path_entry.setText(
            str(self._initial_config.downloads_path or "")
        )
        self.__downloads_path_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__downloads_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        path_glayout.addWidget(self.__downloads_path_entry, 2, 1)

    def __init_behavior_settings(self) -> None:
        behavior_group = QGroupBox(self.tr("Behavior Settings"))
        self.__vlayout.addWidget(behavior_group)
        behavior_glayout = QGridLayout()
        behavior_glayout.setColumnStretch(0, 1)
        behavior_glayout.setColumnStretch(1, 1)
        behavior_group.setLayout(behavior_glayout)

        confidence_label = QLabel("*" + self.tr("Language detector confidence"))
        behavior_glayout.addWidget(confidence_label, 0, 0)

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
        behavior_glayout.addWidget(self.__confidence_box, 0, 1)

        download_threads_label = QLabel(
            "*"
            + self.tr(
                "Number of concurrent downloads (only recommended to increase if you "
                "have Nexus Mods Premium)"
            )
        )
        download_threads_label.setWordWrap(True)
        behavior_glayout.addWidget(download_threads_label, 1, 0)

        self.__download_threads_box = QSpinBox()
        self.__download_threads_box.installEventFilter(self)
        self.__download_threads_box.setMinimum(1)
        self.__download_threads_box.setValue(self._initial_config.download_thread_num)
        self.__download_threads_box.valueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__download_threads_box.valueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        behavior_glayout.addWidget(self.__download_threads_box, 1, 1)

        worker_threads_label = QLabel(
            "*" + self.tr("Number of maximum worker threads for some IO tasks")
        )
        behavior_glayout.addWidget(worker_threads_label, 2, 0)

        self.__worker_threads_box = QSpinBox()
        self.__worker_threads_box.installEventFilter(self)
        self.__worker_threads_box.setMinimum(1)
        self.__worker_threads_box.setValue(self._initial_config.worker_thread_num)
        self.__worker_threads_box.valueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        behavior_glayout.addWidget(self.__worker_threads_box, 2, 1)

        self.__bind_nxm_checkbox = QCheckBox(
            "*"
            + self.tr(
                'Automatically bind to "Mod Manager Download" '
                "buttons on Nexus Mods on startup"
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
        behavior_glayout.addWidget(self.__bind_nxm_checkbox, 3, 0, 1, 2)

        self.__use_spell_check_checkbox = QCheckBox(
            self.tr("Enable spell checking in translation editor")
        )
        self.__use_spell_check_checkbox.setChecked(self._initial_config.use_spell_check)
        self.__use_spell_check_checkbox.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        behavior_glayout.addWidget(self.__use_spell_check_checkbox, 4, 0, 1, 2)

        self.__auto_import_checkbox = QCheckBox(
            self.tr("Automatically import installed translations into the database")
        )
        self.__auto_import_checkbox.setChecked(
            self._initial_config.auto_import_translations
        )
        self.__auto_import_checkbox.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        behavior_glayout.addWidget(self.__auto_import_checkbox, 5, 0, 1, 2)

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
        behavior_glayout.addWidget(
            self.__auto_create_db_translations_checkbox, 6, 0, 1, 2
        )

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
        behavior_glayout.addWidget(self.__double_click_strings, 7, 0, 1, 2)

    def __clear_cache(self) -> None:
        self.__cache.clear_caches()
        self.__clear_cache_button.setText(
            self.tr(
                "Clear cache (This will reset all mod file states and delete cached API "
                "requests and more temporary data!)"
            )
        )
        self.__clear_cache_button.setEnabled(False)

    @override
    def validate(self) -> None:
        accent_color: str = self.__accent_color_entry.text().strip()

        if not ValidationUtils.is_valid_hex_color(accent_color):
            raise ConfigValidationError(
                self.tr("Accent color must be a valid hexadecimal color code!")
            )

        ValidationUtils.validate_parent_path(self.__output_path_entry.text())
        ValidationUtils.validate_parent_path(self.__temp_path_entry.text())
        ValidationUtils.validate_parent_path(self.__downloads_path_entry.text())

    @override
    def apply(self, config: AppConfig) -> None:
        config.log_num_of_files = self.__logs_num_box.value()
        config.log_level = self.__log_level_box.getCurrentValue()
        config.language = self.__app_lang_box.getCurrentValue()
        config.ui_mode = self.__ui_mode_box.getCurrentValue()
        config.accent_color = self.__accent_color_entry.text()
        config.detector_confidence = self.__confidence_box.value()
        config.download_thread_num = self.__download_threads_box.value()
        config.worker_thread_num = self.__worker_threads_box.value()
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
