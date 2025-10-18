"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.settings.settings_page import SettingsPage
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from cutleast_core_lib.ui.widgets.link_button import LinkButton
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

from .blacklist_dialog import BlacklistDialog


class UserSettings(SettingsPage[UserConfig]):
    """
    Page for user settings.
    """

    __vlayout: QVBoxLayout

    __lang_box: EnumDropdown[GameLanguage]
    __source_label: QLabel
    __source_box: EnumDropdown[ProviderPreference]
    __api_key_entry: KeyLineEdit
    __masterlist_box: QCheckBox

    __modinstance_selector: InstanceSelectorWidget
    __parse_bsas_checkbox: QCheckBox

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

        self.__author_blacklist = self._initial_config.author_blacklist.copy()

    def __init_translations_settings(self) -> None:
        translations_group = QGroupBox(self.tr("Translations"))
        self.__vlayout.addWidget(translations_group)
        translations_flayout = QFormLayout()
        translations_group.setLayout(translations_flayout)

        self.__lang_box = EnumDropdown(GameLanguage, self._initial_config.language)
        self.__lang_box.installEventFilter(self)
        self.__lang_box.currentValueChanged.connect(self.__on_lang_change)
        self.__lang_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__lang_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        translations_flayout.addRow("*" + self.tr("Game language"), self.__lang_box)

        self.__source_label = QLabel("*" + self.tr("Translation source"))
        self.__source_label.setEnabled(
            self._initial_config.language == GameLanguage.French
        )

        self.__source_box = EnumDropdown(
            ProviderPreference, self._initial_config.provider_preference
        )
        self.__source_box.installEventFilter(self)
        self.__source_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__source_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        self.__source_box.setEnabled(
            self._initial_config.language == GameLanguage.French
        )
        translations_flayout.addRow(self.__source_label, self.__source_box)

        api_key_hlayout = QHBoxLayout()
        self.__api_key_entry = KeyLineEdit()
        self.__api_key_entry.setText(self._initial_config.api_key)
        self.__api_key_entry.textChanged.connect(lambda _: self.changed_signal.emit())
        self.__api_key_entry.textChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        api_key_hlayout.addWidget(self.__api_key_entry, 1)
        api_setup_button = QPushButton(self.tr("Start API setup..."))
        api_setup_button.clicked.connect(self.__start_api_setup)
        api_key_hlayout.addWidget(api_setup_button)
        translations_flayout.addRow(
            "*" + self.tr("Nexus Mods API Key"), api_key_hlayout
        )

        self.__masterlist_box = QCheckBox()
        self.__masterlist_box.setText(
            self.tr("Use global masterlist from GitHub repository (recommended)")
        )
        self.__masterlist_box.setChecked(self._initial_config.use_masterlist)
        self.__masterlist_box.stateChanged.connect(lambda _: self.changed_signal.emit())
        open_masterlist_button = LinkButton(
            "https://github.com/Cutleast/SSE-Auto-Translator/tree/master/masterlists",
            self.tr("Open masterlist (in browser)"),
        )
        translations_flayout.addRow(self.__masterlist_box, open_masterlist_button)

        author_blacklist_button = QPushButton(
            self.tr("Open translation author blacklist...")
        )
        author_blacklist_button.clicked.connect(self.__open_author_blacklist)
        translations_flayout.addRow(author_blacklist_button)

    def __init_instance_settings(self) -> None:
        instance_group = QGroupBox("*" + self.tr("Modlist"))
        self.__vlayout.addWidget(instance_group)
        instance_vlayout = QVBoxLayout()
        instance_group.setLayout(instance_vlayout)

        self.__modinstance_selector = InstanceSelectorWidget()
        self.__modinstance_selector.set_cur_instance_data(
            self._initial_config.modinstance
        )
        self.__modinstance_selector.changed.connect(self.changed_signal.emit)
        self.__modinstance_selector.changed.connect(self.restart_required_signal.emit)
        instance_vlayout.addWidget(self.__modinstance_selector)

        self.__parse_bsas_checkbox = QCheckBox(
            self.tr(
                "Parse BSA archives (This may slow down app startup depending on the "
                "size of your modlist!)"
            )
        )
        self.__parse_bsas_checkbox.setChecked(self._initial_config.parse_bsa_archives)
        self.__parse_bsas_checkbox.stateChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__parse_bsas_checkbox.stateChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        instance_vlayout.addWidget(self.__parse_bsas_checkbox)

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
            self.changed_signal.emit()

    def __start_api_setup(self) -> None:
        dialog = QDialog(QApplication.activeModalWidget())
        dialog.setWindowTitle(self.tr("Nexus Mods API key"))
        dialog.setMinimumSize(800, 400)

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        api_setup = ApiSetup()
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
        config.parse_bsa_archives = self.__parse_bsas_checkbox.isChecked()
