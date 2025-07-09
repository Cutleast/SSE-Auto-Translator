"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Annotated, Optional, override

from pydantic import Field

from core.utilities.localisation import Language
from core.utilities.logger import Logger

from ._base_config import BaseConfig

DEFAULT_ACCENT_COLOR: str = "#a998d2"
"""Default accent color."""


class AppConfig(BaseConfig):
    """
    Class for application settings.
    """

    log_level: Annotated[Logger.Level, Field(alias="log.level")] = Logger.Level.DEBUG
    """Log level"""

    log_num_of_files: Annotated[int, Field(alias="log.num_of_files", ge=-1)] = 5
    """Number of newest log files to keep"""

    log_format: Annotated[str, Field(alias="log.format")] = (
        "[%(asctime)s.%(msecs)03d][%(levelname)s][%(name)s.%(funcName)s]: %(message)s"
    )
    """Log format"""

    log_date_format: Annotated[str, Field(alias="log.date_format")] = (
        "%d.%m.%Y %H:%M:%S"
    )
    """Log date format"""

    log_file_name: Annotated[str, Field(alias="log.file_name")] = (
        "%d-%m-%Y-%H-%M-%S.log"
    )
    """Log file name"""

    language: Language = Language.System
    """App language"""

    accent_color: str = DEFAULT_ACCENT_COLOR
    """Accent color"""

    detector_confidence: float = 0.8
    """Language detector confidence"""

    auto_bind_nxm: bool = False
    """Automatically bind to "Mod Manager Download" Buttons on Nexus Mods on Startup"""

    use_spell_check: bool = True
    """Use spell checker in translation editor"""

    output_path: Optional[Path] = None
    """Target path for the created output mod. Parent must be an existing directory."""

    temp_path: Optional[Path] = None
    """
    Overrides the used directory for temporary files. Parent must be an existing
    directory.
    """

    downloads_path: Optional[Path] = None
    """
    Path for persistently storing downloaded translation archives. Parent must be an
    existing directory.
    """

    auto_import_translations: bool = True
    """Whether to import installed translations into the database automatically."""

    auto_create_database_translations: bool = True
    """
    Whether to automatically create translations for mod files that are entirely covered
    by already installed translations.
    """

    show_strings_on_double_click: bool = True
    """
    Whether to show strings when a mod or mod file is double clicked in the modlist or a
    translation in the "Translations" tab.
    """

    @override
    @staticmethod
    def get_config_name() -> str:
        return "app/config.json"
