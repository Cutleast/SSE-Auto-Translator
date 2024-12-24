"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.config.user_config import UserConfig
from core.mod_managers import SUPPORTED_MOD_MANAGERS
from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer import ModOrganizer
from core.translation_provider.provider import Provider
from core.utilities.constants import SUPPORTED_LANGS
from ui.widgets.api_setup import ApiSetup
from ui.widgets.browse_edit import BrowseLineEdit
from ui.widgets.key_entry import KeyEntry
from ui.widgets.link_button import LinkButton
from ui.widgets.smooth_scroll_area import SmoothScrollArea

from .blacklist_dialog import BlacklistDialog


class UserSettings(SmoothScrollArea):
    """
    Widget for user settings.
    """

    on_change_signal = Signal()
    """
    This signal gets emitted every time
    the user changes some setting.
    """

    user_config: UserConfig

    def __init__(self) -> None:
        super().__init__()

        self.user_config = AppContext.get_app().user_config

        self.setObjectName("transparent")
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        # TODO: Refactor this

        flayout = QFormLayout()
        scroll_widget.setLayout(flayout)

        # Language
        self.lang_box = QComboBox()
        self.lang_box.installEventFilter(self)
        self.lang_box.setEditable(False)
        self.lang_box.addItems([lang[0].capitalize() for lang in SUPPORTED_LANGS])
        self.lang_box.setCurrentText(self.user_config.language)
        self.lang_box.currentTextChanged.connect(self.on_change)
        flayout.addRow(self.tr("Game Language"), self.lang_box)

        # Source
        provider_box = QGroupBox(self.tr("Source"))
        flayout.addRow(provider_box)
        provider_flayout = QFormLayout()
        provider_box.setLayout(provider_flayout)

        self.source_label = QLabel(self.tr("Source"))
        self.source_label.setEnabled(self.user_config.language == "French")
        self.source_dropdown = QComboBox()
        self.source_dropdown.installEventFilter(self)
        self.source_dropdown.setEnabled(self.user_config.language == "French")
        self.source_dropdown.setEditable(False)
        self.source_dropdown.addItems(
            [preference.name for preference in Provider.Preference]
        )
        self.source_dropdown.setCurrentText(self.user_config.provider_preference.name)
        self.source_dropdown.currentTextChanged.connect(self.on_change)
        self.lang_box.currentTextChanged.connect(self.__on_lang_change)
        provider_flayout.addRow(self.source_label, self.source_dropdown)

        # API Setup / Settings
        api_key_hlayout = QHBoxLayout()
        self.api_key_entry = KeyEntry()
        self.api_key_entry.setText(self.user_config.api_key)
        api_key_hlayout.addWidget(self.api_key_entry)
        api_setup_button = QPushButton(self.tr("Start API Setup"))
        api_setup_button.clicked.connect(self.start_api_setup)
        api_key_hlayout.addWidget(api_setup_button)
        provider_flayout.addRow(self.tr("Nexus Mods API Key"), api_key_hlayout)

        # Masterlist
        self.masterlist_box = QCheckBox(
            self.tr("Use global Masterlist from GitHub Repository (recommended)")
        )
        self.masterlist_box.setChecked(self.user_config.use_masterlist)
        self.masterlist_box.stateChanged.connect(self.on_change)
        open_masterlist_button = LinkButton(
            "https://github.com/Cutleast/SSE-Auto-Translator/tree/master/masterlists",
            self.tr("Open Masterlist (in Browser)"),
        )
        provider_flayout.addRow(self.masterlist_box, open_masterlist_button)

        # Author Blacklist
        author_blacklist_button = QPushButton(
            self.tr("Open Translation Author Blacklist...")
        )
        author_blacklist_button.clicked.connect(self.edit_blacklist)
        provider_flayout.addRow(author_blacklist_button)

        # Mod Manager selection
        instance_groupbox = QGroupBox(self.tr("Modinstance"))
        flayout.addRow(instance_groupbox)
        instance_flayout = QFormLayout()
        instance_groupbox.setLayout(instance_flayout)

        self.mod_manager_dropdown = QComboBox()
        self.mod_manager_dropdown.installEventFilter(self)
        self.mod_manager_dropdown.setEditable(False)
        self.mod_manager_dropdown.addItems(
            [mod_manager.name for mod_manager in SUPPORTED_MOD_MANAGERS]
        )
        self.mod_manager_dropdown.currentIndexChanged.connect(
            self.__on_mod_manager_select
        )
        instance_flayout.addRow(self.tr("Mod Manager"), self.mod_manager_dropdown)

        # Modinstance Selection
        self.modinstance_dropdown = QComboBox()
        self.modinstance_dropdown.installEventFilter(self)
        self.modinstance_dropdown.setEditable(False)
        instance_flayout.addRow(self.tr("Modinstance"), self.modinstance_dropdown)

        self.mod_manager_dropdown.setCurrentText(self.user_config.mod_manager.name)
        self.mod_manager_dropdown.currentTextChanged.connect(self.on_change)
        self.__on_mod_manager_select(self.mod_manager_dropdown.currentIndex())
        self.modinstance_dropdown.setCurrentText(self.user_config.modinstance)
        self.modinstance_dropdown.currentTextChanged.connect(self.on_change)
        self.modinstance_dropdown.currentTextChanged.connect(self.__on_instance_select)

        # Profile Selection
        self.profile_label = QLabel(self.tr("Instance Profile (MO2)"))
        self.instance_profile_dropdown = QComboBox()
        self.instance_profile_dropdown.installEventFilter(self)
        self.instance_profile_dropdown.setDisabled(True)
        self.instance_profile_dropdown.setEditable(False)
        self.instance_profile_dropdown.currentTextChanged.connect(self.on_change)
        mod_manager: ModManager = SUPPORTED_MOD_MANAGERS[
            self.mod_manager_dropdown.currentIndex()
        ]()
        modinstance: str = self.modinstance_dropdown.currentText()
        profiles: list[str] = mod_manager.get_instance_profiles(
            modinstance, self.user_config.instance_path
        )
        self.instance_profile_dropdown.addItems(profiles)
        self.instance_profile_dropdown.setEnabled(len(profiles) > 1)
        self.instance_profile_dropdown.view
        self.profile_label.setEnabled(len(profiles) > 1)
        if "Default" in profiles:
            self.instance_profile_dropdown.setCurrentText("Default")
        self.instance_profile_dropdown.setCurrentText(self.user_config.instance_profile)
        instance_flayout.addRow(self.profile_label, self.instance_profile_dropdown)

        # Path to portable modinstance
        self.instance_path_label = QLabel(self.tr("Path to Portable Instance"))
        self.instance_path_label.setEnabled(self.user_config.modinstance == "Portable")

        self.instance_path_entry = BrowseLineEdit()
        if self.user_config.instance_path is not None:
            self.instance_path_entry.setText(str(self.user_config.instance_path))
        self.instance_path_entry.setEnabled(self.user_config.modinstance == "Portable")
        self.instance_path_entry.textChanged.connect(self.__on_instance_path_change)
        self.instance_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        instance_flayout.addRow(self.instance_path_label, self.instance_path_entry)

        # Enabled File Types
        filetypes_groupbox = QGroupBox(self.tr("Enabled File Types"))
        flayout.addRow(filetypes_groupbox)
        filetypes_vlayout = QVBoxLayout()
        filetypes_groupbox.setLayout(filetypes_vlayout)

        self.enable_interface_files_box = QCheckBox(
            self.tr("Enable Interface Files (Data/Interface/*.txt)")
        )
        self.enable_interface_files_box.stateChanged.connect(self.on_change)
        self.enable_interface_files_box.setChecked(
            self.user_config.enable_interface_files
        )
        filetypes_vlayout.addWidget(self.enable_interface_files_box)

        self.enable_scripts_box = QCheckBox(
            self.tr("Enable Papyrus Scripts (Data/Scripts/*.pex)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.enable_scripts_box.stateChanged.connect(self.on_change)
        self.enable_scripts_box.setChecked(self.user_config.enable_scripts)
        filetypes_vlayout.addWidget(self.enable_scripts_box)

        self.enable_textures_box = QCheckBox(
            self.tr("Enable Textures (Data/Textures/*)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.enable_textures_box.stateChanged.connect(self.on_change)
        self.enable_textures_box.setChecked(self.user_config.enable_textures)
        filetypes_vlayout.addWidget(self.enable_textures_box)

        self.enable_sound_files_box = QCheckBox(
            self.tr("Enable Sound Files (Data/Sound/*)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.enable_sound_files_box.stateChanged.connect(self.on_change)
        self.enable_sound_files_box.setChecked(self.user_config.enable_sound_files)
        filetypes_vlayout.addWidget(self.enable_sound_files_box)

    def __on_lang_change(self, lang: str) -> None:
        self.source_label.setEnabled(lang == "French")
        self.source_dropdown.setEnabled(lang == "French")

        if lang == "French":
            self.source_dropdown.setCurrentText(
                Provider.Preference.PreferNexusMods.name
            )
        else:
            self.source_dropdown.setCurrentText(Provider.Preference.OnlyNexusMods.name)

    def __on_mod_manager_select(self, index: int) -> None:
        mod_manager = SUPPORTED_MOD_MANAGERS[index]()

        self.modinstance_dropdown.clear()
        instances = mod_manager.get_instances()
        self.modinstance_dropdown.addItems(instances)
        self.modinstance_dropdown.setCurrentIndex(0)

    def __on_instance_select(self, modinstance: str) -> None:
        self.instance_path_label.setEnabled(modinstance == "Portable")
        self.instance_path_entry.setEnabled(modinstance == "Portable")
        self.instance_path_entry.clear()

        mod_manager = SUPPORTED_MOD_MANAGERS[self.mod_manager_dropdown.currentIndex()]()
        self.instance_profile_dropdown.clear()
        if modinstance != "Portable":
            profiles = mod_manager.get_instance_profiles(modinstance)
            self.instance_profile_dropdown.addItems(profiles)
            if "Default" in profiles:
                self.instance_profile_dropdown.setCurrentText("Default")
            self.instance_profile_dropdown.setEnabled(len(profiles) > 1)
            self.profile_label.setEnabled(len(profiles) > 1)
        else:
            self.profile_label.setDisabled(True)
            self.instance_profile_dropdown.setDisabled(True)

    def __on_instance_path_change(self, new_path: str) -> None:
        ini_path = Path(new_path) / "ModOrganizer.ini"

        if ini_path.is_file():
            profiles = ModOrganizer.get_profiles_from_ini(ini_path)
        else:
            profiles = []

        self.instance_profile_dropdown.clear()
        self.instance_profile_dropdown.addItems(profiles)
        self.instance_profile_dropdown.setEnabled(len(profiles) > 1)
        self.profile_label.setEnabled(len(profiles) > 1)

    def edit_blacklist(self) -> None:
        dialog = BlacklistDialog(
            QApplication.activeModalWidget(), self.user_config.author_blacklist.copy()
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.user_config.author_blacklist = dialog.blacklist
            self.on_change()

    def start_api_setup(self) -> None:
        """
        Opens API Setup in a separate dialog.
        """

        dialog = QDialog(QApplication.activeModalWidget())
        dialog.setWindowTitle(self.tr("Nexus Mods API Key"))
        dialog.setMinimumSize(800, 400)

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        api_setup = ApiSetup()
        vlayout.addWidget(api_setup)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        save_button = QPushButton(self.tr("Save"))
        save_button.setObjectName("accent_button")
        save_button.setDisabled(True)
        api_setup.valid_signal.connect(lambda valid: save_button.setEnabled(valid))

        def save() -> None:
            if api_setup.api_key is not None:
                self.api_key_entry.setText(api_setup.api_key)
                dialog.accept()

        save_button.clicked.connect(save)
        hlayout.addWidget(save_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(dialog.reject)
        hlayout.addWidget(cancel_button)

        dialog.exec()

    def on_change(self, *args: Any) -> None:
        """
        This emits change signal without passing parameters.
        """

        self.on_change_signal.emit()

    def save_settings(self) -> None:
        mod_managers: dict[str, type[ModManager]] = {
            mod_manager.name: mod_manager for mod_manager in SUPPORTED_MOD_MANAGERS
        }

        self.user_config.language = self.lang_box.currentText()
        self.user_config.api_key = self.api_key_entry.text()
        self.user_config.mod_manager = mod_managers[
            self.mod_manager_dropdown.currentText()
        ]
        self.user_config.modinstance = self.modinstance_dropdown.currentText()
        self.user_config.use_masterlist = self.masterlist_box.isChecked()
        self.user_config.instance_profile = (
            self.instance_profile_dropdown.currentText()
            if self.instance_profile_dropdown.currentText()
            else ""
        )
        self.user_config.instance_path = (
            Path(self.instance_path_entry.text())
            if self.instance_path_entry.text()
            else None
        )
        self.user_config.provider_preference = Provider.Preference[
            self.source_dropdown.currentText()
        ]
        self.user_config.enable_interface_files = (
            self.enable_interface_files_box.isChecked()
        )
        self.user_config.enable_scripts = self.enable_scripts_box.isChecked()
        self.user_config.enable_textures = self.enable_textures_box.isChecked()
        self.user_config.enable_sound_files = self.enable_sound_files_box.isChecked()
        self.user_config.save()

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and isinstance(source, QComboBox)
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
