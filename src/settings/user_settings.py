"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

import mod_managers
import utilities as utils
from main import MainApp
from widgets import KeyEntry, ApiSetup


class UserSettings(qtw.QScrollArea):
    """
    Widget for user settings.
    """

    on_change_signal = qtc.Signal()
    """
    This signal gets emitted every time
    the user changes some setting.
    """

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.settings

        self.setObjectName("root")

        self.setWidgetResizable(True)
        self.setObjectName("transparent")
        scroll_widget = qtw.QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)
        # slayout = qtw.QVBoxLayout()
        # scroll_widget.setLayout(slayout)

        flayout = qtw.QFormLayout()
        scroll_widget.setLayout(flayout)

        # Language
        self.lang_box = qtw.QComboBox()
        self.lang_box.installEventFilter(self)
        self.lang_box.setEditable(False)
        self.lang_box.addItems([lang[0].capitalize() for lang in utils.SUPPORTED_LANGS])
        self.lang_box.setCurrentText(self.app.user_config["language"])
        self.lang_box.currentTextChanged.connect(self.on_change)
        flayout.addRow(self.mloc.game_lang, self.lang_box)

        # Source
        source_label = qtw.QLabel(self.loc.main.source)
        source_label.setEnabled(self.app.user_config["language"] == "French")
        self.source_dropdown = qtw.QComboBox()
        self.source_dropdown.installEventFilter(self)
        self.source_dropdown.setEnabled(self.app.user_config["language"] == "French")
        self.source_dropdown.setEditable(False)
        self.source_dropdown.addItems(app.provider.Preference._member_names_)
        self.source_dropdown.setCurrentText(self.app.user_config["provider_preference"])
        self.source_dropdown.currentTextChanged.connect(self.on_change)

        def on_lang_change(lang: str):
            source_label.setEnabled(lang == "French")
            self.source_dropdown.setEnabled(lang == "French")

            if lang == "French":
                self.source_dropdown.setCurrentText(
                    app.provider.Preference.PreferConfrerie.name
                )
            else:
                self.source_dropdown.setCurrentText(
                    app.provider.Preference.OnlyNexusMods.name
                )

        self.lang_box.currentTextChanged.connect(on_lang_change)
        flayout.addRow(source_label, self.source_dropdown)

        # API Setup / Settings
        api_key_hlayout = qtw.QHBoxLayout()
        self.api_key_entry = KeyEntry()
        self.api_key_entry.setText(self.app.user_config["api_key"])
        api_key_hlayout.addWidget(self.api_key_entry)
        api_setup_button = qtw.QPushButton(self.mloc.start_api_setup)
        api_setup_button.clicked.connect(self.start_api_setup)
        api_key_hlayout.addWidget(api_setup_button)
        flayout.addRow(self.mloc.nm_api_key, api_key_hlayout)

        # Mod Manager selection
        self.mod_manager_dropdown = qtw.QComboBox()
        self.mod_manager_dropdown.installEventFilter(self)
        self.mod_manager_dropdown.setEditable(False)
        self.mod_manager_dropdown.addItems(
            [mod_manager.name for mod_manager in mod_managers.SUPPORTED_MOD_MANAGERS]
        )

        def on_mod_manager_select(index: int):
            mod_manager = mod_managers.SUPPORTED_MOD_MANAGERS[index]()

            self.modinstance_dropdown.clear()
            instances = mod_manager.get_instances()
            self.modinstance_dropdown.addItems(instances)
            self.modinstance_dropdown.setCurrentIndex(0)

        self.mod_manager_dropdown.currentIndexChanged.connect(on_mod_manager_select)
        flayout.addRow(self.loc.main.mod_manager, self.mod_manager_dropdown)

        # Modinstance Selection
        self.modinstance_dropdown = qtw.QComboBox()
        self.modinstance_dropdown.installEventFilter(self)
        self.modinstance_dropdown.setEditable(False)
        flayout.addRow(self.loc.main.modinstance, self.modinstance_dropdown)

        self.mod_manager_dropdown.setCurrentText(self.app.user_config["mod_manager"])
        self.mod_manager_dropdown.currentTextChanged.connect(self.on_change)

        on_mod_manager_select(self.mod_manager_dropdown.currentIndex())
        self.modinstance_dropdown.setCurrentText(self.app.user_config["modinstance"])

        def on_instance_select(modinstance: str):
            instance_path_label.setEnabled(modinstance == "Portable")
            self.instance_path_entry.setEnabled(modinstance == "Portable")
            self.instance_path_entry.clear()
            browse_instance_path_button.setEnabled(modinstance == "Portable")

            mod_manager = mod_managers.SUPPORTED_MOD_MANAGERS[
                self.mod_manager_dropdown.currentIndex()
            ]()
            self.instance_profile_dropdown.clear()
            if modinstance != "Portable":
                profiles = mod_manager.get_instance_profiles(modinstance)
                self.instance_profile_dropdown.addItems(profiles)
                if "Default" in profiles:
                    self.instance_profile_dropdown.setCurrentText("Default")
                self.instance_profile_dropdown.setEnabled(len(profiles) > 1)
                profile_label.setEnabled(len(profiles) > 1)
            else:
                profile_label.setDisabled(True)
                self.instance_profile_dropdown.setDisabled(True)

        self.modinstance_dropdown.currentTextChanged.connect(self.on_change)
        self.modinstance_dropdown.currentTextChanged.connect(on_instance_select)

        # Profile Selection
        profile_label = qtw.QLabel(self.loc.main.instance_profile)
        self.instance_profile_dropdown = qtw.QComboBox()
        self.instance_profile_dropdown.installEventFilter(self)
        self.instance_profile_dropdown.setDisabled(True)
        self.instance_profile_dropdown.setEditable(False)
        self.instance_profile_dropdown.currentTextChanged.connect(self.on_change)
        mod_manager = mod_managers.SUPPORTED_MOD_MANAGERS[
            self.mod_manager_dropdown.currentIndex()
        ]()
        modinstance = self.modinstance_dropdown.currentText()
        profiles = mod_manager.get_instance_profiles(modinstance)
        self.instance_profile_dropdown.addItems(profiles)
        self.instance_profile_dropdown.setEnabled(len(profiles) > 1)
        self.instance_profile_dropdown.view
        profile_label.setEnabled(len(profiles) > 1)
        if "Default" in profiles:
            self.instance_profile_dropdown.setCurrentText("Default")
        if self.app.user_config.get("instance_profile"):
            self.instance_profile_dropdown.setCurrentText(
                self.app.user_config["instance_profile"]
            )
        flayout.addRow(profile_label, self.instance_profile_dropdown)

        # Path to portable modinstance
        instance_path_label = qtw.QLabel(self.loc.main.instance_path)
        instance_path_label.setEnabled(
            self.app.user_config["modinstance"] == "Portable"
        )
        hlayout = qtw.QHBoxLayout()
        flayout.addRow(instance_path_label, hlayout)

        self.instance_path_entry = qtw.QLineEdit()
        path_file = self.app.data_path / "user" / "portable.txt"
        if path_file.is_file() and self.app.user_config["modinstance"] == "Portable":
            self.instance_path_entry.setText(path_file.read_text().strip())
        self.instance_path_entry.setEnabled(
            self.app.user_config["modinstance"] == "Portable"
        )

        def on_path_change(new_path: str):
            ini_path = Path(new_path) / "ModOrganizer.ini"

            if ini_path.is_file():
                profiles = mod_managers.ModOrganizer.get_profiles_from_ini(ini_path)
            else:
                profiles = []

            self.instance_profile_dropdown.clear()
            self.instance_profile_dropdown.addItems(profiles)
            self.instance_profile_dropdown.setEnabled(len(profiles) > 1)
            profile_label.setEnabled(len(profiles) > 1)

        self.instance_path_entry.textChanged.connect(on_path_change)
        hlayout.addWidget(self.instance_path_entry)
        browse_instance_path_button = qtw.QPushButton()
        browse_instance_path_button.setIcon(
            qta.icon("fa5s.folder-open", color="#ffffff")
        )
        browse_instance_path_button.setEnabled(
            self.app.user_config["modinstance"] == "Portable"
        )

        def browse():
            file_dialog = qtw.QFileDialog(self.app.activeModalWidget())
            file_dialog.setWindowTitle(self.loc.main.browse)
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            utils.apply_dark_title_bar(file_dialog)
            if cur_text := self.instance_path_entry.text().strip():
                path = Path(cur_text)
                if path.is_dir():
                    file_dialog.setDirectoryUrl(str(path))
            if file_dialog.exec():
                file = file_dialog.selectedFiles()[0]
                file = os.path.normpath(file)
                self.instance_path_entry.setText(file)

        browse_instance_path_button.clicked.connect(browse)
        hlayout.addWidget(browse_instance_path_button)

        # Masterlist
        self.masterlist_box = qtw.QCheckBox(self.mloc.use_masterlist)
        self.masterlist_box.setChecked(self.app.user_config.get("use_masterlist", True))
        self.masterlist_box.stateChanged.connect(self.on_change)
        flayout.addRow(self.masterlist_box)

        # Enabled File Types
        filetypes_label = qtw.QLabel(self.loc.settings.enabled_file_types)
        filetypes_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        filetypes_label.setObjectName("relevant_label")
        flayout.addRow(filetypes_label)

        self.enable_interface_files_box = qtw.QCheckBox(
            self.loc.settings.enable_interface_files
        )
        self.enable_interface_files_box.stateChanged.connect(self.on_change)
        self.enable_interface_files_box.setChecked(
            self.app.user_config["enable_interface_files"]
        )
        flayout.addRow(self.enable_interface_files_box)

        self.enable_scripts_box = qtw.QCheckBox(
            self.loc.settings.enable_scripts + " [EXPERIMENTAL]"
        )
        self.enable_scripts_box.stateChanged.connect(self.on_change)
        self.enable_scripts_box.setChecked(self.app.user_config["enable_scripts"])
        flayout.addRow(self.enable_scripts_box)

        self.enable_textures_box = qtw.QCheckBox(
            self.loc.settings.enable_textures + " [EXPERIMENTAL]"
        )
        self.enable_textures_box.stateChanged.connect(self.on_change)
        self.enable_textures_box.setChecked(self.app.user_config["enable_textures"])
        flayout.addRow(self.enable_textures_box)

        self.enable_sound_files_box = qtw.QCheckBox(
            self.loc.settings.enable_sound_files + " [EXPERIMENTAL]"
        )
        self.enable_sound_files_box.stateChanged.connect(self.on_change)
        self.enable_sound_files_box.setChecked(
            self.app.user_config["enable_sound_files"]
        )
        flayout.addRow(self.enable_sound_files_box)

    def start_api_setup(self):
        """
        Opens API Setup in a separate dialog.
        """

        dialog = qtw.QDialog(self)
        dialog.setWindowTitle(self.mloc.nm_api_key)
        dialog.setMinimumSize(800, 400)
        utils.apply_dark_title_bar(dialog)

        vlayout = qtw.QVBoxLayout()
        dialog.setLayout(vlayout)

        api_setup = ApiSetup(self.app)
        vlayout.addWidget(api_setup)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        save_button = qtw.QPushButton(self.loc.main.save)
        save_button.setObjectName("accent_button")
        save_button.setDisabled(True)
        api_setup.valid_signal.connect(lambda valid: save_button.setEnabled(valid))

        def save():
            self.api_key_entry.setText(api_setup.api_key)
            dialog.accept()

        save_button.clicked.connect(save)
        hlayout.addWidget(save_button)

        cancel_button = qtw.QPushButton(self.loc.main.cancel)
        cancel_button.clicked.connect(dialog.reject)
        hlayout.addWidget(cancel_button)

        dialog.exec()

    def on_change(self, *args):
        """
        This emits change signal without passing parameters.
        """

        self.on_change_signal.emit()

    def get_settings(self):
        profile = (
            self.instance_profile_dropdown.currentText()
            if self.instance_profile_dropdown.currentText()
            else None
        )

        return {
            "language": self.lang_box.currentText(),
            "api_key": self.api_key_entry.text(),
            "mod_manager": self.mod_manager_dropdown.currentText(),
            "modinstance": self.modinstance_dropdown.currentText(),
            "use_masterlist": self.masterlist_box.isChecked(),
            "instance_profile": profile,
            "provider_preference": self.source_dropdown.currentText(),
            "enable_interface_files": self.enable_interface_files_box.isChecked(),
            "enable_scripts": self.enable_scripts_box.isChecked(),
            "enable_textures": self.enable_textures_box.isChecked(),
            "enable_sound_files": self.enable_sound_files_box.isChecked(),
        }
    
    def eventFilter(self, source: qtc.QObject, event: qtc.QEvent):
        if event.type() == qtc.QEvent.Type.Wheel and isinstance(source, qtw.QComboBox):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
