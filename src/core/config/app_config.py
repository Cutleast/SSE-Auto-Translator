"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from core.utilities import is_valid_hex_color
from core.utilities.logger import Logger

from ._base_config import BaseConfig


class AppConfig(BaseConfig):
    """
    Class for application settings.
    """

    log = logging.getLogger("AppConfig")

    def __init__(self, config_folder: Path):
        super().__init__(config_folder / "config.json")

    @property
    def log_level(self) -> Logger.LogLevel:
        """
        Logging level.
        """

        return Logger.LogLevel[self._settings["log.level"].upper()]

    @log_level.setter
    def log_level(self, log_level: Logger.LogLevel) -> None:
        AppConfig.validate_type(log_level, Logger.LogLevel)

        self._settings["log.level"] = log_level.name

    @property
    def log_num_of_files(self) -> int:
        """
        Number of newest log files to keep.
        """

        return self._settings["log.num_of_files"]

    @log_num_of_files.setter
    def log_num_of_files(self, value: int) -> None:
        AppConfig.validate_type(value, int)

        self._settings["log.num_of_files"] = value

    @property
    def log_format(self) -> str:
        """
        Logging format.
        """

        return self._settings["log.format"]

    @log_format.setter
    def log_format(self, format: str) -> None:
        AppConfig.validate_type(format, str)

        self._settings["log.format"] = format

    @property
    def log_date_format(self) -> str:
        """
        Logging date format.
        """

        return self._settings["log.date_format"]

    @log_date_format.setter
    def log_date_format(self, date_format: str) -> None:
        AppConfig.validate_type(date_format, str)

        self._settings["log.date_format"] = date_format

    @property
    def log_file_name(self) -> str:
        """
        Base file name for log files.
        """

        return self._settings["log.file_name"]

    @log_file_name.setter
    def log_file_name(self, file_name: str) -> None:
        AppConfig.validate_type(file_name, str)
        AppConfig.validate_value(file_name, lambda x: x.endswith(".log"))

        self._settings["log.file_name"] = file_name

    @property
    def language(self) -> str:
        """
        App language.
        """

        return self._settings["language"]

    @language.setter
    def language(self, language: str) -> None:
        AppConfig.validate_type(language, str)

        self._settings["language"] = language

    @property
    def accent_color(self) -> str:
        """
        Accent color for the UI.
        """

        return self._settings["accent_color"]

    @accent_color.setter
    def accent_color(self, accent_color: str) -> None:
        AppConfig.validate_type(accent_color, str)
        AppConfig.validate_value(accent_color, is_valid_hex_color)

        self._settings["accent_color"] = accent_color

    @property
    def detector_confidence(self) -> float:
        """
        Language detector confidence.
        """

        return self._settings["detector_confidence"]

    @detector_confidence.setter
    def detector_confidence(self, detector_confidence: float) -> None:
        AppConfig.validate_type(detector_confidence, float)
        AppConfig.validate_value(detector_confidence, lambda c: 0 <= c <= 1)

        self._settings["detector_confidence"] = detector_confidence

    @property
    def auto_bind_nxm(self) -> bool:
        """
        Automatically bind to "Mod Manager Download" Buttons on Nexus Mods on Startup.
        """

        return self._settings["auto_bind_nxm"]

    @auto_bind_nxm.setter
    def auto_bind_nxm(self, auto_bind_nxm: bool) -> None:
        AppConfig.validate_type(auto_bind_nxm, bool)

        self._settings["auto_bind_nxm"] = auto_bind_nxm

    @property
    def use_spell_check(self) -> bool:
        """
        Use spell checker in translation editor.
        """

        return self._settings["use_spell_check"]

    @use_spell_check.setter
    def use_spell_check(self, use_spell_check: bool) -> None:
        AppConfig.validate_type(use_spell_check, bool)

        self._settings["use_spell_check"] = use_spell_check

    @property
    def output_path(self) -> Optional[Path]:
        """
        Target path for the created output mod.
        Parent must be an existing directory.
        """

        return (
            Path(self._settings["output_path"])
            if self._settings["output_path"] is not None
            else None
        )

    @output_path.setter
    def output_path(self, output_path: Optional[Path]) -> None:
        AppConfig.validate_type(output_path, Path, may_be_none=True)
        AppConfig.validate_value(
            output_path, lambda p: p.parent.is_dir(), may_be_none=True
        )

        self._settings["output_path"] = (
            str(output_path) if output_path is not None else None
        )

    @property
    def temp_path(self) -> Optional[Path]:
        """
        Path for temporary files.
        Parent must be an existing directory.
        """

        return (
            Path(self._settings["temp_path"]) if self._settings["temp_path"] else None
        )

    @temp_path.setter
    def temp_path(self, temp_path: Optional[Path]) -> None:
        AppConfig.validate_type(temp_path, Path, may_be_none=True)
        AppConfig.validate_value(
            temp_path, lambda p: p.parent.is_dir(), may_be_none=True
        )

        self._settings["temp_path"] = str(temp_path) if temp_path is not None else None

    @property
    def downloads_path(self) -> Optional[Path]:
        """
        Path for downloads.
        Parent must be an existing directory.
        """

        return (
            Path(self._settings["downloads_path"])
            if self._settings["downloads_path"]
            else None
        )

    @downloads_path.setter
    def downloads_path(self, downloads_path: Optional[Path]) -> None:
        AppConfig.validate_type(downloads_path, Path, may_be_none=True)
        AppConfig.validate_value(
            downloads_path, lambda p: p.parent.is_dir(), may_be_none=True
        )

        self._settings["downloads_path"] = (
            str(downloads_path) if downloads_path else None
        )

    @property
    def auto_import_translations(self) -> bool:
        """
        Import installed translations into the database automatically.
        """

        return self._settings["auto_import_translations"]

    @auto_import_translations.setter
    def auto_import_translations(self, auto_import_translations: bool) -> None:
        AppConfig.validate_type(auto_import_translations, bool)

        self._settings["auto_import_translations"] = auto_import_translations

    @property
    def auto_create_database_translations(self) -> bool:
        """
        Automatically create translations for plugins that are entirely covered
        by already installed translations.
        """

        return self._settings["auto_create_database_translations"]

    @auto_create_database_translations.setter
    def auto_create_database_translations(
        self, auto_create_database_translations: bool
    ) -> None:
        AppConfig.validate_type(auto_create_database_translations, bool)

        self._settings["auto_create_database_translations"] = (
            auto_create_database_translations
        )

    @property
    def show_strings_on_double_click(self) -> bool:
        """
        Show strings when a mod or plugin is double clicked in the modlist
        or a translation in the "Translations" tab.
        """

        return self._settings["show_strings_on_double_click"]

    @show_strings_on_double_click.setter
    def show_strings_on_double_click(self, show_strings_on_double_click: bool) -> None:
        AppConfig.validate_type(show_strings_on_double_click, bool)

        self._settings["show_strings_on_double_click"] = show_strings_on_double_click
