"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os

import jstyleson as json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app import MainApp
from core.utilities import apply_dark_title_bar
from ui.widgets.stacked_widget import StackedWidget


class StartupDialog(QWidget):
    """
    Startup dialog class.
    """

    def __init__(self, app: MainApp, parent: QWidget = None):
        super().__init__(parent)

        from .instance_page import InstancePage
        from .introduction import IntroductionPage
        from .setup_page import SetupPage

        self.app = app
        self.loc = app.loc
        self.mloc = self.loc.startup_dialog

        # Initialize logger
        self.log = logging.getLogger("StartupDialog")

        # Configure window
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setObjectName("root")
        self.setWindowTitle(self.mloc.startup)
        self.setFixedSize(900, 610)
        apply_dark_title_bar(self)

        # Create layout
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        # Page widget
        self.page_widget = StackedWidget(orientation="horizontal")
        self.page_widget.setObjectName("primary")
        vlayout.addWidget(self.page_widget, 1)

        self.introduction_page = IntroductionPage(self)
        self.page_widget.addWidget(self.introduction_page)

        self.setup_page = SetupPage(self)
        self.page_widget.addWidget(self.setup_page)

        self.instance_page = InstancePage(self)
        self.page_widget.addWidget(self.instance_page)

        self.page_widget.setCurrentWidget(self.introduction_page)
        self.show()

    def finish(self):
        language = self.setup_page.lang_box.currentText()
        provider_preference = self.setup_page.source_dropdown.currentText()
        api_key = self.setup_page.api_setup.api_key
        use_masterlist = self.setup_page.masterlist_box.isChecked()
        enable_interface_files = self.setup_page.enable_interface_files_box.isChecked()
        enable_scripts = self.setup_page.enable_scripts_box.isChecked()
        enable_textures = self.setup_page.enable_textures_box.isChecked()
        enable_sound_files = self.setup_page.enable_sound_files_box.isChecked()
        mod_manager_name = self.instance_page.mod_manager.name
        instance_name = self.instance_page.modinstance_name
        instance_path = self.instance_page.instance_path_entry.text()
        instance_profile = self.instance_page.profile_name

        user_path = self.app.data_path / "user"
        user_config = {
            "language": language,
            "api_key": api_key,
            "mod_manager": mod_manager_name,
            "modinstance": instance_name,
            "use_masterlist": use_masterlist,
            "instance_profile": instance_profile,
            "provider_preference": provider_preference,
            "enable_interface_files": enable_interface_files,
            "enable_scripts": enable_scripts,
            "enable_textures": enable_textures,
            "enable_sound_files": enable_sound_files,
        }

        if not user_path.is_dir():
            os.mkdir(user_path)

        with open(self.app.user_conf_path, "w", encoding="utf8") as file:
            json.dump(user_config, file, indent=4)

        if instance_path.strip():
            (user_path / "portable.txt").write_text(instance_path.strip())

        database_path = user_path / "database" / language.lower()
        if not database_path.is_dir():
            os.makedirs(database_path, exist_ok=True)

            index_path = database_path / "index.json"
            if not index_path.is_file():
                index_data = []

                with open(index_path, "w", encoding="utf8") as index_file:
                    json.dump(index_data, index_file, indent=4)

        self.app.setup_complete = True

        super().close()

        self.app.start_main_app()
