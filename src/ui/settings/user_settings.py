"""
Copyright (c) Cutleast
"""

from typing import override

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

from core.config.user_config import UserConfig
from core.mod_managers import SUPPORTED_MOD_MANAGERS
from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer import ModOrganizer
from core.translation_provider.provider_preference import ProviderPreference
from core.utilities.constants import SUPPORTED_LANGS
from core.utilities.path import Path
from ui.widgets.api_setup import ApiSetup
from ui.widgets.browse_edit import BrowseLineEdit
from ui.widgets.completion_box import CompletionBox
from ui.widgets.key_entry import KeyEntry
from ui.widgets.link_button import LinkButton

from .blacklist_dialog import BlacklistDialog
from .settings_page import SettingsPage


class UserSettings(SettingsPage[UserConfig]):
    """
    Page for user settings.
    """

    __vlayout: QVBoxLayout

    __lang_box: CompletionBox

    __source_label: QLabel
    __source_box: QComboBox
    __api_key_entry: KeyEntry
    __masterlist_box: QCheckBox

    __mod_manager_box: QComboBox
    __modinstance_box: QComboBox
    __instance_profile_label: QLabel
    __instance_profile_box: QComboBox
    __instance_path_label: QLabel
    __instance_path_entry: BrowseLineEdit

    __enable_interface_files_box: QCheckBox
    __enable_scripts_box: QCheckBox
    __enable_textures_box: QCheckBox
    __enable_sound_files_box: QCheckBox

    __author_blacklist: list[str]

    @override
    def _init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        self.__vlayout = QVBoxLayout()
        scroll_widget.setLayout(self.__vlayout)

        self.__init_language_setting()
        self.__init_source_settings()
        self.__init_instance_settings()
        self.__init_file_type_settings()

        self.__author_blacklist = self._initial_config.author_blacklist.copy()

    def __init_language_setting(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        lang_label = QLabel("*" + self.tr("Choose Game Language:"))
        hlayout.addWidget(lang_label)

        self.__lang_box = CompletionBox()
        self.__lang_box.installEventFilter(self)
        self.__lang_box.setPlaceholderText(self.tr("Please select..."))
        lang_items = [lang[0].capitalize() for lang in SUPPORTED_LANGS]
        self.__lang_box.addItems(lang_items)
        self.__lang_box.setCurrentText(self._initial_config.language)
        self.__lang_box.currentTextChanged.connect(self.__on_lang_change)
        self.__lang_box.currentTextChanged.connect(self._on_change)
        self.__lang_box.currentTextChanged.connect(self._on_restart_required)
        hlayout.addWidget(self.__lang_box)

    def __init_source_settings(self) -> None:
        source_group = QGroupBox(self.tr("Source"))
        self.__vlayout.addWidget(source_group)
        source_flayout = QFormLayout()
        source_group.setLayout(source_flayout)

        self.__source_label = QLabel("*" + self.tr("Source:"))
        self.__source_label.setEnabled(self._initial_config.language == "French")

        self.__source_box = QComboBox()
        self.__source_box.installEventFilter(self)
        self.__source_box.addItems(
            [preference.name for preference in ProviderPreference]
        )
        self.__source_box.setCurrentText(self._initial_config.provider_preference.name)
        self.__source_box.currentTextChanged.connect(self._on_change)
        self.__source_box.currentTextChanged.connect(self._on_restart_required)
        self.__source_box.setEnabled(self._initial_config.language == "French")
        source_flayout.addRow(self.__source_label, self.__source_box)

        api_key_hlayout = QHBoxLayout()
        self.__api_key_entry = KeyEntry()
        self.__api_key_entry.setText(self._initial_config.api_key)
        self.__api_key_entry.textChanged.connect(self._on_change)
        self.__api_key_entry.textChanged.connect(self._on_restart_required)
        api_key_hlayout.addWidget(self.__api_key_entry, 1)
        api_setup_button = QPushButton(self.tr("Start API Setup"))
        api_setup_button.clicked.connect(self.__start_api_setup)
        api_key_hlayout.addWidget(api_setup_button)
        source_flayout.addRow("*" + self.tr("Nexus Mods API Key"), api_key_hlayout)

        self.__masterlist_box = QCheckBox()
        self.__masterlist_box.setText(
            self.tr("Use global Masterlist from GitHub Repository (recommended)")
        )
        self.__masterlist_box.setChecked(self._initial_config.use_masterlist)
        self.__masterlist_box.stateChanged.connect(self._on_change)
        open_masterlist_button = LinkButton(
            "https://github.com/Cutleast/SSE-Auto-Translator/tree/master/masterlists",
            self.tr("Open Masterlist (in Browser)"),
        )
        source_flayout.addRow(self.__masterlist_box, open_masterlist_button)

        author_blacklist_button = QPushButton(
            self.tr("Open Translation Author Blacklist...")
        )
        author_blacklist_button.clicked.connect(self.__open_author_blacklist)
        source_flayout.addRow(author_blacklist_button)

    def __init_instance_settings(self) -> None:
        instance_group = QGroupBox(self.tr("Modinstance"))
        self.__vlayout.addWidget(instance_group)
        instance_flayout = QFormLayout()
        instance_group.setLayout(instance_flayout)

        self.__mod_manager_box = QComboBox()
        self.__mod_manager_box.installEventFilter(self)
        self.__mod_manager_box.addItems(
            [manager.name for manager in SUPPORTED_MOD_MANAGERS]
        )
        self.__mod_manager_box.setCurrentText(self._initial_config.mod_manager.name)
        self.__mod_manager_box.currentIndexChanged.connect(self.__on_mod_manager_select)
        self.__mod_manager_box.currentTextChanged.connect(self._on_change)
        self.__mod_manager_box.currentTextChanged.connect(self._on_restart_required)
        instance_flayout.addRow("*" + self.tr("Mod Manager"), self.__mod_manager_box)

        self.__modinstance_box = QComboBox()
        self.__modinstance_box.installEventFilter(self)
        self.__modinstance_box.addItems(
            self._initial_config.mod_manager().get_instances()
        )
        self.__modinstance_box.setCurrentText(self._initial_config.modinstance)
        self.__modinstance_box.currentTextChanged.connect(self.__on_instance_select)
        self.__modinstance_box.currentTextChanged.connect(self._on_change)
        self.__modinstance_box.currentTextChanged.connect(self._on_restart_required)
        instance_flayout.addRow("*" + self.tr("Modinstance"), self.__modinstance_box)

        self.__instance_profile_label = QLabel("*" + self.tr("Instance Profile (MO2)"))
        self.__instance_profile_box = QComboBox()
        self.__instance_profile_box.installEventFilter(self)
        self.__instance_profile_box.addItems(
            self._initial_config.mod_manager().get_instance_profiles(
                self._initial_config.modinstance, self._initial_config.instance_path
            )
        )
        self.__instance_profile_box.setCurrentText(
            self._initial_config.instance_profile
        )
        self.__instance_profile_box.currentTextChanged.connect(self._on_change)
        self.__instance_profile_box.currentTextChanged.connect(
            self._on_restart_required
        )
        instance_flayout.addRow(
            self.__instance_profile_label, self.__instance_profile_box
        )

        self.__instance_path_label = QLabel("*" + self.tr("Path to Portable Instance"))
        self.__instance_path_entry = BrowseLineEdit()
        self.__instance_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        if self._initial_config.instance_path:
            self.__instance_path_entry.setText(
                str(self._initial_config.instance_path.normalize())
            )
        self.__instance_path_entry.textChanged.connect(self.__on_instance_path_change)
        self.__instance_path_entry.textChanged.connect(self._on_change)
        self.__instance_path_entry.textChanged.connect(self._on_restart_required)
        instance_flayout.addRow(self.__instance_path_label, self.__instance_path_entry)

    def __init_file_type_settings(self) -> None:
        filetypes_group = QGroupBox(self.tr("Enabled File Types"))
        self.__vlayout.addWidget(filetypes_group)
        filetypes_vlayout = QVBoxLayout()
        filetypes_group.setLayout(filetypes_vlayout)

        self.__enable_interface_files_box = QCheckBox(
            self.tr("Enable Interface Files (Data/Interface/*.txt)")
        )
        self.__enable_interface_files_box.setChecked(
            self._initial_config.enable_interface_files
        )
        self.__enable_interface_files_box.stateChanged.connect(self._on_change)
        filetypes_vlayout.addWidget(self.__enable_interface_files_box)

        self.__enable_scripts_box = QCheckBox(
            self.tr("Enable Scripts (Data/Scripts/*.pex)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.__enable_scripts_box.setChecked(self._initial_config.enable_scripts)
        self.__enable_scripts_box.stateChanged.connect(self._on_change)
        filetypes_vlayout.addWidget(self.__enable_scripts_box)

        self.__enable_textures_box = QCheckBox(
            self.tr("Enable Textures (Data/Textures/*)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.__enable_textures_box.setChecked(self._initial_config.enable_textures)
        self.__enable_textures_box.stateChanged.connect(self._on_change)
        filetypes_vlayout.addWidget(self.__enable_textures_box)

        self.__enable_sound_files_box = QCheckBox(
            self.tr("Enable Sound Files (Data/Sound/*)")
            + " "
            + self.tr("[EXPERIMENTAL]")
        )
        self.__enable_sound_files_box.setChecked(
            self._initial_config.enable_sound_files
        )
        self.__enable_sound_files_box.stateChanged.connect(self._on_change)
        filetypes_vlayout.addWidget(self.__enable_sound_files_box)

    def __on_lang_change(self, lang: str) -> None:
        self.__source_label.setEnabled(lang == "French")
        self.__source_box.setEnabled(lang == "French")

        if lang == "French":
            self.__source_box.setCurrentText(ProviderPreference.PreferNexusMods.name)
        else:
            self.__source_box.setCurrentText(ProviderPreference.OnlyNexusMods.name)

    def __on_mod_manager_select(self, index: int) -> None:
        mod_manager: ModManager = SUPPORTED_MOD_MANAGERS[index]()

        self.__modinstance_box.clear()
        instances: list[str] = mod_manager.get_instances()
        self.__modinstance_box.addItems(instances)
        self.__modinstance_box.setCurrentIndex(0)

    def __on_instance_select(self, modinstance: str) -> None:
        self.__instance_path_label.setEnabled(modinstance == "Portable")
        self.__instance_path_entry.setEnabled(modinstance == "Portable")
        self.__instance_path_entry.clear()

        mod_manager = SUPPORTED_MOD_MANAGERS[self.__mod_manager_box.currentIndex()]()
        self.__instance_profile_box.clear()
        if modinstance != "Portable":
            profiles: list[str] = mod_manager.get_instance_profiles(modinstance)
            self.__instance_profile_box.addItems(profiles)
            if "Default" in profiles:
                self.__instance_profile_box.setCurrentText("Default")
            self.__instance_profile_box.setEnabled(len(profiles) > 1)
            self.__instance_profile_label.setEnabled(len(profiles) > 1)
        else:
            self.__instance_profile_label.setDisabled(True)
            self.__instance_profile_box.setDisabled(True)

    def __on_instance_path_change(self, new_path: str) -> None:
        ini_path = Path(new_path) / "ModOrganizer.ini"

        if ini_path.is_file():
            profiles = ModOrganizer.get_profiles_from_ini(ini_path)
        else:
            profiles = []

        self.__instance_profile_box.clear()
        self.__instance_profile_box.addItems(profiles)
        self.__instance_profile_box.setEnabled(len(profiles) > 1)
        self.__instance_profile_label.setEnabled(len(profiles) > 1)

    def __open_author_blacklist(self) -> None:
        dialog = BlacklistDialog(
            QApplication.activeModalWidget(), self.__author_blacklist
        )

        if (
            dialog.exec() == QDialog.DialogCode.Accepted
            and self.__author_blacklist != self._initial_config.author_blacklist
        ):
            self._on_change()

    def __start_api_setup(self) -> None:
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
                self.__api_key_entry.setText(api_setup.api_key)
                dialog.accept()

        save_button.clicked.connect(save)
        hlayout.addWidget(save_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(dialog.reject)
        hlayout.addWidget(cancel_button)

        dialog.exec()

    @override
    def apply(self, config: UserConfig) -> None:
        mod_managers: dict[str, type[ModManager]] = {
            mod_manager.name: mod_manager for mod_manager in SUPPORTED_MOD_MANAGERS
        }

        config.language = self.__lang_box.currentText()
        config.api_key = self.__api_key_entry.text()
        config.mod_manager = mod_managers[self.__mod_manager_box.currentText()]
        config.modinstance = self.__modinstance_box.currentText()
        config.use_masterlist = self.__masterlist_box.isChecked()
        config.instance_profile = (
            self.__instance_profile_box.currentText()
            if self.__instance_profile_box.currentText() != "Default"
            else ""
        )
        config.instance_path = (
            Path(self.__instance_path_entry.text())
            if self.__instance_path_entry.text()
            else None
        )
        config.provider_preference = ProviderPreference[self.__source_box.currentText()]
        config.author_blacklist = self.__author_blacklist
        config.enable_interface_files = self.__enable_interface_files_box.isChecked()
        config.enable_scripts = self.__enable_scripts_box.isChecked()
        config.enable_textures = self.__enable_textures_box.isChecked()
        config.enable_sound_files = self.__enable_sound_files_box.isChecked()
