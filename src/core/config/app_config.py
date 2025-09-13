"""
Copyright (c) Cutleast
"""

import tempfile
from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.core.config.app_config import AppConfig as BaseAppConfig
from cutleast_core_lib.core.utilities.dynamic_default_model import default_factory
from cutleast_core_lib.ui.utilities.ui_mode import UIMode

from core.utilities.localisation import Language


class AppConfig(BaseAppConfig):
    """
    Class for application settings.
    """

    debug_mode: bool = False
    """
    Debug mode. Enables various debug features and information. Used for development.
    """

    language: Language = Language.System
    """App language"""

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

    _tmp_dir: Optional[Path] = None

    def get_tmp_dir(self) -> Path:
        """
        Returns the path to the temporary directory. Creates one if it doesn't exist.

        Returns:
            Path: Path to the temporary directory
        """

        if self._tmp_dir is None:
            self._tmp_dir = Path(
                tempfile.mkdtemp(prefix="SSE-AT_temp-", dir=self.temp_path)
            )

        return self._tmp_dir

    @override
    @staticmethod
    def get_config_name() -> str:
        return "app/config.json"

    @default_factory("accent_color")
    @classmethod
    def _get_default_accent_color(cls) -> str:
        return "#a998d2"

    @default_factory("ui_mode")
    @classmethod
    def _get_default_ui_mode(cls) -> UIMode:
        return UIMode.Dark
