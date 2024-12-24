"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path
from typing import Any

import qtawesome as qta
from PySide6.QtCore import QEvent, QLocale, QObject, QSize, Signal
from PySide6.QtGui import QColor, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from app_context import AppContext
from core.cacher.cacher import Cacher
from core.config.app_config import AppConfig
from core.utilities.filesystem import get_folder_size
from core.utilities.logger import Logger
from core.utilities.scale import scale_value
from ui.widgets.browse_edit import BrowseLineEdit
from ui.widgets.smooth_scroll_area import SmoothScrollArea


class AppSettings(SmoothScrollArea):
    """
    Widget for application settings.
    """

    on_change_signal = Signal()
    """
    This signal gets emitted every time
    the user changes some setting.
    """

    app_config: AppConfig

    def __init__(self) -> None:
        super().__init__()

        self.app_config = AppContext.get_app().app_config

        self.setObjectName("transparent")

        self.__init_ui()

    def __init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        flayout = QFormLayout()
        scroll_widget.setLayout(flayout)

        self.logs_num_box = QSpinBox()
        self.logs_num_box.installEventFilter(self)
        self.logs_num_box.setRange(-1, 100)
        self.logs_num_box.setValue(self.app_config.log_num_of_files)
        self.logs_num_box.valueChanged.connect(self.on_change)
        flayout.addRow(self.tr("Number of newest log files to keep"), self.logs_num_box)

        self.log_level_box = QComboBox()
        self.log_level_box.installEventFilter(self)
        self.log_level_box.addItems(
            [loglevel.name.capitalize() for loglevel in Logger.LogLevel]
        )
        self.log_level_box.setCurrentText(self.app_config.log_level.name.capitalize())
        self.log_level_box.currentTextChanged.connect(self.on_change)
        flayout.addRow(self.tr("Log Level"), self.log_level_box)

        self.app_lang_box = QComboBox()
        self.app_lang_box.installEventFilter(self)
        self.app_lang_box.addItem("System")
        # TODO: Make this dynamic
        self.app_lang_box.addItems(["de_DE", "en_US", "ru_RU", "zh_CN"])
        self.app_lang_box.setCurrentText(self.app_config.language)
        self.app_lang_box.currentTextChanged.connect(self.on_change)
        flayout.addRow(self.tr("App language"), self.app_lang_box)

        color_hlayout = QHBoxLayout()
        self.accent_color_entry = QLineEdit()
        self.accent_color_entry.setText(self.app_config.accent_color)
        self.accent_color_entry.textChanged.connect(self.on_change)
        color_hlayout.addWidget(self.accent_color_entry)
        self.choose_color_button = QPushButton()

        def choose_color() -> None:
            colordialog = QColorDialog(QApplication.activeModalWidget())
            colordialog.setOption(
                colordialog.ColorDialogOption.DontUseNativeDialog, on=True
            )
            colordialog.setCustomColor(
                0, QColor(self.app_config.get_default_value("accent_color"))
            )
            color = self.accent_color_entry.text()
            if QColor.isValidColor(color):
                colordialog.setCurrentColor(QColor(color))
            if colordialog.exec():
                self.accent_color_entry.setText(
                    colordialog.currentColor().name(QColor.NameFormat.HexRgb)
                )
                self.choose_color_button.setIcon(
                    qta.icon(
                        "mdi6.square-rounded", color=self.accent_color_entry.text()
                    )
                )

        self.choose_color_button.setText(self.tr("Choose Accent Color..."))
        self.choose_color_button.setIconSize(QSize(24, 24))
        self.choose_color_button.clicked.connect(choose_color)
        self.choose_color_button.setIcon(
            qta.icon("mdi6.square-rounded", color=self.app_config.accent_color)
        )
        color_hlayout.addWidget(self.choose_color_button)
        flayout.addRow(self.tr("Accent Color"), color_hlayout)

        self.confidence_box = QDoubleSpinBox()
        self.confidence_box.installEventFilter(self)
        self.confidence_box.setLocale(QLocale.Language.English)
        self.confidence_box.setRange(0, 1)
        self.confidence_box.setSingleStep(0.05)
        self.confidence_box.setValue(self.app_config.detector_confidence)
        self.confidence_box.valueChanged.connect(self.on_change)
        flayout.addRow(self.tr("Language Detector Confidence"), self.confidence_box)

        # Output path
        self.output_path_entry = BrowseLineEdit()
        cur_path: Path = AppContext.get_app().cur_path
        self.output_path_entry.setPlaceholderText(str(cur_path / "SSE-AT Output"))
        self.output_path_entry.setText(str(self.app_config.output_path or ""))
        self.output_path_entry.textChanged.connect(self.on_change)
        self.output_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        flayout.addRow(
            self.tr("Path for Output Mod") + self.tr(" (No Restart Required)"),
            self.output_path_entry,
        )

        # Temp path
        self.temp_path_entry = BrowseLineEdit()
        self.temp_path_entry.setPlaceholderText(os.getenv("TEMP") or "")
        self.temp_path_entry.setText(str(self.app_config.temp_path or ""))
        self.temp_path_entry.textChanged.connect(self.on_change)
        self.temp_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        flayout.addRow(
            self.tr("Path for Temporary Folder")
            + "\n"
            + self.tr("(for temporary files, will be wiped after exit!)"),
            self.temp_path_entry,
        )

        # Downloads path
        self.downloads_path_entry = BrowseLineEdit()
        self.downloads_path_entry.setPlaceholderText(
            self.tr("Defaults to Temporary Folder configured above")
        )
        self.downloads_path_entry.setText(str(self.app_config.downloads_path or ""))
        self.downloads_path_entry.textChanged.connect(self.on_change)
        self.downloads_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        flayout.addRow(self.tr("Downloads Path"), self.downloads_path_entry)

        self.bind_nxm_checkbox = QCheckBox(
            self.tr(
                'Automatically bind to "Mod Manager Download" '
                "Buttons on Nexus Mods on Startup"
            )
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.bind_nxm_checkbox.setChecked(self.app_config.auto_bind_nxm)
        self.bind_nxm_checkbox.stateChanged.connect(self.on_change)
        flayout.addRow(self.bind_nxm_checkbox)

        self.use_spell_check_checkbox = QCheckBox(
            self.tr("Enable Spell Checking in Translation Editor")
            + self.tr(" (No Restart Required)")
        )
        self.use_spell_check_checkbox.setChecked(self.app_config.use_spell_check)
        self.use_spell_check_checkbox.stateChanged.connect(self.on_change)
        flayout.addRow(self.use_spell_check_checkbox)

        self.auto_import_checkbox = QCheckBox(
            self.tr("Automatically import installed translations into the database")
            + self.tr(" (No Restart Required)")
        )
        self.auto_import_checkbox.setChecked(self.app_config.auto_import_translations)
        self.auto_import_checkbox.stateChanged.connect(self.on_change)
        flayout.addRow(self.auto_import_checkbox)

        self.double_click_strings = QCheckBox(
            self.tr(
                "Show strings when double clicking a mod or plugin "
                'in the modlist or a translation in the "Translations" tab'
            )
            + self.tr(" (No Restart Required)")
        )
        self.double_click_strings.setChecked(
            self.app_config.show_strings_on_double_click
        )
        self.double_click_strings.stateChanged.connect(self.on_change)
        flayout.addRow(self.double_click_strings)

        self.clear_cache_button = QPushButton(
            self.tr(
                "Clear Cache (This will reset all plugin states "
                "and delete cached API requests!)"
            )
        )
        self.clear_cache_button.clicked.connect(self.clear_cache)
        cacher: Cacher = AppContext.get_app().cacher
        if cacher.path.is_dir():
            self.clear_cache_button.setEnabled(True)
            self.clear_cache_button.setText(
                self.clear_cache_button.text()
                + f" ({scale_value(get_folder_size(cacher.path))})"
            )
        else:
            self.clear_cache_button.setEnabled(False)
        flayout.addRow(self.clear_cache_button)

    def on_change(self, *args: Any) -> None:
        """
        This emits change signal without passing parameters.
        """

        self.on_change_signal.emit()

    def clear_cache(self) -> None:
        cacher: Cacher = AppContext.get_app().cacher
        cacher.clear_caches()
        self.clear_cache_button.setText(
            self.tr(
                "Clear Cache (This will reset all plugin states "
                "and delete cached API requests!)"
            )
        )
        self.clear_cache_button.setEnabled(False)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and (
                isinstance(source, QComboBox)
                or isinstance(source, QSpinBox)
                or isinstance(source, QDoubleSpinBox)
            )
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)

    def save_settings(self) -> None:
        self.app_config.log_num_of_files = self.logs_num_box.value()
        self.app_config.log_level = Logger.LogLevel[
            self.log_level_box.currentText().upper()
        ]
        self.app_config.language = self.app_lang_box.currentText()
        self.app_config.accent_color = self.accent_color_entry.text()
        self.app_config.detector_confidence = self.confidence_box.value()
        self.app_config.auto_bind_nxm = self.bind_nxm_checkbox.isChecked()
        self.app_config.use_spell_check = self.use_spell_check_checkbox.isChecked()
        self.app_config.auto_import_translations = self.auto_import_checkbox.isChecked()
        self.app_config.show_strings_on_double_click = (
            self.double_click_strings.isChecked()
        )
        self.app_config.output_path = (
            Path(self.output_path_entry.text().strip())
            if self.output_path_entry.text().strip()
            else None
        )
        self.app_config.temp_path = (
            Path(self.temp_path_entry.text().strip())
            if self.temp_path_entry.text().strip()
            else None
        )
        self.app_config.downloads_path = (
            Path(self.downloads_path_entry.text().strip())
            if self.downloads_path_entry.text().strip()
            else None
        )

        self.app_config.save()
