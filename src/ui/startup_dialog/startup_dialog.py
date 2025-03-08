"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from typing import Optional

import jstyleson as json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget

from app_context import AppContext
from core.config.user_config import UserConfig
from core.mod_managers import SUPPORTED_MOD_MANAGERS
from core.mod_managers.mod_manager import ModManager
from core.translation_provider.provider import Provider
from core.utilities.path import Path
from ui.widgets.stacked_widget import StackedWidget

from .instance_page import InstancePage
from .introduction import IntroductionPage
from .setup_page import SetupPage


class StartupDialog(QDialog):
    """
    Startup dialog class.
    """

    log: logging.Logger = logging.getLogger("StartupDialog")

    __vlayout: QVBoxLayout
    __page_widget: StackedWidget
    __introduction_page: IntroductionPage
    __setup_page: SetupPage
    __instance_page: InstancePage

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Configure window
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setObjectName("root")
        self.setWindowTitle(self.tr("Welcome!"))
        self.setFixedSize(900, 610)

        self.__init_ui()

    def __init_ui(self) -> None:
        # Create layout
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        # Page widget
        self.__page_widget = StackedWidget(
            orientation=StackedWidget.Orientation.Horizontal
        )
        self.__page_widget.setObjectName("transparent")
        self.__vlayout.addWidget(self.__page_widget, 1)

        self.__introduction_page = IntroductionPage()
        self.__introduction_page.prev_signal.connect(self.reject)
        self.__introduction_page.next_signal.connect(self.__page_widget.slideInNext)
        self.__page_widget.addWidget(self.__introduction_page)

        self.__setup_page = SetupPage()
        self.__setup_page.prev_signal.connect(self.__page_widget.slideInPrev)
        self.__setup_page.next_signal.connect(self.__page_widget.slideInNext)
        self.__page_widget.addWidget(self.__setup_page)

        self.__instance_page = InstancePage()
        self.__instance_page.prev_signal.connect(self.__page_widget.slideInPrev)
        self.__instance_page.next_signal.connect(self.finish)
        self.__page_widget.addWidget(self.__instance_page)

        self.__page_widget.setCurrentWidget(self.__introduction_page)

    def finish(self) -> None:
        mod_managers: dict[str, type[ModManager]] = {
            mod_manager.name: mod_manager for mod_manager in SUPPORTED_MOD_MANAGERS
        }

        language: str
        provider_preference: str
        api_key: str
        use_masterlist: bool
        enable_interface_files: bool
        enable_scripts: bool
        enable_textures: bool
        enable_sound_files: bool
        (
            language,
            provider_preference,
            api_key,
            use_masterlist,
            enable_interface_files,
            enable_scripts,
            enable_textures,
            enable_sound_files,
        ) = self.__setup_page.get_values()

        mod_manager_name: str
        instance_name: str
        instance_profile: str
        instance_path: str
        mod_manager_name, instance_name, instance_profile, instance_path = (
            self.__instance_page.get_values()
        )

        data_path: Path = AppContext.get_app().data_path
        user_path: Path = data_path / "user"

        user_config = UserConfig(user_path)
        user_config.language = language
        user_config.api_key = api_key
        user_config.mod_manager = mod_managers[mod_manager_name]
        user_config.modinstance = instance_name
        user_config.use_masterlist = use_masterlist
        user_config.instance_profile = instance_profile
        user_config.instance_path = Path(instance_path)
        user_config.provider_preference = Provider.Preference[provider_preference]
        user_config.enable_interface_files = enable_interface_files
        user_config.enable_scripts = enable_scripts
        user_config.enable_textures = enable_textures
        user_config.enable_sound_files = enable_sound_files
        user_config.save()

        database_path: Path = user_path / "database" / language.lower()
        if not database_path.is_dir():
            os.makedirs(database_path, exist_ok=True)

            index_path: Path = database_path / "index.json"
            if not index_path.is_file():
                with open(index_path, "w", encoding="utf8") as index_file:
                    json.dump([], index_file, indent=4)

        super().accept()
