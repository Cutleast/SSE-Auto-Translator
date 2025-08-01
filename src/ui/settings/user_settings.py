"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.config.user_config import UserConfig
from core.translation_provider.provider_preference import ProviderPreference
from core.utilities.game_language import GameLanguage
from ui.modinstance_selector.instance_selector_widget import InstanceSelectorWidget
from ui.widgets.api_setup import ApiSetup
from ui.widgets.enum_dropdown import EnumDropdown
from ui.widgets.key_entry import KeyEntry
from ui.widgets.link_button import LinkButton

from .blacklist_dialog import BlacklistDialog
from .settings_page import SettingsPage


class UserSettings(SettingsPage[UserConfig]):
    """
    Page for user settings.
    """

    __vlayout: QVBoxLayout

    __lang_box: EnumDropdown[GameLanguage]
    __source_label: QLabel
    __source_box: EnumDropdown[ProviderPreference]
    __api_key_entry: KeyEntry
    __masterlist_box: QCheckBox

    __modinstance_selector: InstanceSelectorWidget

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

        self.__init_translations_settings()
        self.__init_instance_settings()
        self.__init_file_type_settings()

        self.__author_blacklist = self._initial_config.author_blacklist.copy()

    def __init_translations_settings(self) -> None:
        translations_group = QGroupBox(self.tr("Translations"))
        self.__vlayout.addWidget(translations_group)
        translations_flayout = QFormLayout()
        translations_group.setLayout(translations_flayout)

        self.__lang_box = EnumDropdown(GameLanguage, self._initial_config.language)
        self.__lang_box.installEventFilter(self)
        self.__lang_box.currentValueChanged.connect(self.__on_lang_change)
        self.__lang_box.currentValueChanged.connect(self._on_change)
        self.__lang_box.currentValueChanged.connect(self._on_restart_required)
        translations_flayout.addRow(
            "*" + self.tr("Choose Game Language:"), self.__lang_box
        )

        self.__source_label = QLabel("*" + self.tr("Source:"))
        self.__source_label.setEnabled(
            self._initial_config.language == GameLanguage.French
        )

        self.__source_box = EnumDropdown(
            ProviderPreference, self._initial_config.provider_preference
        )
        self.__source_box.installEventFilter(self)
        self.__source_box.currentValueChanged.connect(self._on_change)
        self.__source_box.currentValueChanged.connect(self._on_restart_required)
        self.__source_box.setEnabled(
            self._initial_config.language == GameLanguage.French
        )
        translations_flayout.addRow(self.__source_label, self.__source_box)

        api_key_hlayout = QHBoxLayout()
        self.__api_key_entry = KeyEntry()
        self.__api_key_entry.setText(self._initial_config.api_key)
        self.__api_key_entry.textChanged.connect(self._on_change)
        self.__api_key_entry.textChanged.connect(self._on_restart_required)
        api_key_hlayout.addWidget(self.__api_key_entry, 1)
        api_setup_button = QPushButton(self.tr("Start API Setup"))
        api_setup_button.clicked.connect(self.__start_api_setup)
        api_key_hlayout.addWidget(api_setup_button)
        translations_flayout.addRow(
            "*" + self.tr("Nexus Mods API Key"), api_key_hlayout
        )

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
        translations_flayout.addRow(self.__masterlist_box, open_masterlist_button)

        author_blacklist_button = QPushButton(
            self.tr("Open Translation Author Blacklist...")
        )
        author_blacklist_button.clicked.connect(self.__open_author_blacklist)
        translations_flayout.addRow(author_blacklist_button)

    def __init_instance_settings(self) -> None:
        instance_group = QGroupBox("*" + self.tr("Modinstance"))
        self.__vlayout.addWidget(instance_group)
        instance_vlayout = QVBoxLayout()
        instance_group.setLayout(instance_vlayout)

        self.__modinstance_selector = InstanceSelectorWidget()
        self.__modinstance_selector.set_cur_instance_data(
            self._initial_config.modinstance
        )
        self.__modinstance_selector.changed.connect(self._on_change)
        self.__modinstance_selector.changed.connect(self._on_restart_required)
        instance_vlayout.addWidget(self.__modinstance_selector)

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

    def __on_lang_change(self, lang: GameLanguage) -> None:
        self.__source_label.setEnabled(lang == GameLanguage.French)
        self.__source_box.setEnabled(lang == GameLanguage.French)

        if lang == GameLanguage.French:
            self.__source_box.setCurrentValue(ProviderPreference.PreferNexusMods)
        else:
            self.__source_box.setCurrentValue(ProviderPreference.OnlyNexusMods)

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

        api_setup = ApiSetup(self.cache)
        vlayout.addWidget(api_setup)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        save_button = QPushButton(self.tr("Save"))
        save_button.setDefault(True)
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
        config.language = self.__lang_box.getCurrentValue()
        config.api_key = self.__api_key_entry.text()
        config.modinstance = self.__modinstance_selector.get_cur_instance_data()  # pyright: ignore[reportAttributeAccessIssue]
        config.use_masterlist = self.__masterlist_box.isChecked()
        config.provider_preference = self.__source_box.getCurrentValue()
        config.author_blacklist = self.__author_blacklist
        config.enable_interface_files = self.__enable_interface_files_box.isChecked()
        config.enable_scripts = self.__enable_scripts_box.isChecked()
        config.enable_textures = self.__enable_textures_box.isChecked()
        config.enable_sound_files = self.__enable_sound_files_box.isChecked()
