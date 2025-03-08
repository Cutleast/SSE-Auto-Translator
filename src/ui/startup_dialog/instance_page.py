"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, override

from PySide6.QtWidgets import QComboBox, QFileDialog, QFormLayout, QLabel

from core.mod_managers import SUPPORTED_MOD_MANAGERS
from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer import ModOrganizer
from core.utilities.path import Path
from ui.startup_dialog.page import Page
from ui.widgets.browse_edit import BrowseLineEdit


class InstancePage(Page):
    """
    Third page. Asks user which mod instance from which mod manager to load.
    """

    __cur_mod_manager: Optional[ModManager] = None
    __cur_modinstance_name: Optional[str] = None

    __mod_manager_dropdown: QComboBox
    __modinstance_dropdown: QComboBox
    __instance_profile_label: QLabel
    __instance_profile_dropdown: QComboBox
    __instance_path_label: QLabel
    __instance_path_entry: BrowseLineEdit

    @override
    def _init_form(self) -> None:
        flayout = QFormLayout()
        self._vlayout.addLayout(flayout)

        # Mod Manager selection
        self.__mod_manager_dropdown = QComboBox()
        self.__mod_manager_dropdown.setEditable(False)
        self.__mod_manager_dropdown.addItem(self.tr("Please select..."))
        self.__mod_manager_dropdown.addItems(
            [mod_manager.name for mod_manager in SUPPORTED_MOD_MANAGERS]
        )

        self.__mod_manager_dropdown.currentTextChanged.connect(
            self.__on_mod_manager_select
        )
        flayout.addRow(self.tr("Mod Manager"), self.__mod_manager_dropdown)

        # Modinstance Selection
        self.__modinstance_dropdown = QComboBox()
        self.__modinstance_dropdown.setDisabled(True)
        self.__modinstance_dropdown.setEditable(False)
        self.__modinstance_dropdown.addItem(self.tr("Please select..."))
        self.__modinstance_dropdown.currentTextChanged.connect(
            self.__on_modinstance_select
        )
        flayout.addRow(self.tr("Modinstance"), self.__modinstance_dropdown)

        # Profile Selection
        self.__instance_profile_label = QLabel(self.tr("Instance Profile (MO2)"))
        self.__instance_profile_dropdown = QComboBox()
        self.__instance_profile_dropdown.setDisabled(True)
        self.__instance_profile_dropdown.setEditable(False)
        self.__instance_profile_dropdown.currentTextChanged.connect(self._validate)
        flayout.addRow(self.__instance_profile_label, self.__instance_profile_dropdown)

        # Path to portable MO2 instance
        self.__instance_path_label = QLabel(self.tr("Path to Portable Instance"))
        self.__instance_path_label.setDisabled(True)
        self.__instance_path_entry = BrowseLineEdit()
        self.__instance_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        self.__instance_path_entry.setDisabled(True)
        self.__instance_path_entry.textChanged.connect(self.__on_path_change)
        flayout.addRow(self.__instance_path_label, self.__instance_path_entry)

    @override
    def _get_title(self) -> str:
        return self.tr("Mod Instance")

    @override
    def _get_description(self) -> str:
        return self.tr(
            "On this page you select a Modinstance to load from a Mod Manager. "
            "You can always change the selected modinstance and mod manager "
            "under Settings > User Settings."
        )

    @override
    def _validate(self) -> None:
        valid: bool = True

        if self.__cur_modinstance_name is None:
            valid = False

        if self.__cur_modinstance_name == "Portable":
            instance_path_str: str = self.__instance_path_entry.text().strip()
            if not instance_path_str:
                valid = False
            elif not (Path(instance_path_str) / "ModOrganizer.ini").is_file():
                valid = False

        self.valid_signal.emit(valid)

    @override
    def get_values(self) -> tuple[str, str, str, str]:
        return (
            self.__mod_manager_dropdown.currentText(),
            self.__modinstance_dropdown.currentText(),
            self.__instance_profile_dropdown.currentText(),
            self.__instance_path_entry.text(),
        )

    def __on_mod_manager_select(self, mod_manager: str) -> None:
        if mod_manager != self.tr("Please select..."):
            self.__cur_mod_manager = SUPPORTED_MOD_MANAGERS[
                self.__mod_manager_dropdown.currentIndex() - 1
            ]()
        else:
            self.__cur_mod_manager = None

        self.__modinstance_dropdown.clear()
        self.__modinstance_dropdown.addItem(self.tr("Please select..."))
        if self.__cur_mod_manager:
            instances = self.__cur_mod_manager.get_instances()
            self.__modinstance_dropdown.addItems(instances)

        self.__modinstance_dropdown.setEnabled(bool(self.__cur_mod_manager))
        self.__modinstance_dropdown.setCurrentIndex(0)

    def __on_modinstance_select(self, modinstance: str) -> None:
        if modinstance != self.tr("Please select..."):
            self.__cur_modinstance_name = modinstance
            self.__instance_path_entry.setEnabled(modinstance == "Portable")
        else:
            self.__cur_modinstance_name = None
            self.__instance_path_entry.setDisabled(True)

        self.__instance_profile_dropdown.clear()
        if (
            self.__cur_mod_manager is not None
            and self.__cur_modinstance_name
            and self.__cur_modinstance_name != "Portable"
        ):
            profiles = self.__cur_mod_manager.get_instance_profiles(
                self.__cur_modinstance_name
            )
            self.__instance_profile_dropdown.addItems(profiles)
            if "Default" in profiles:
                self.__instance_profile_dropdown.setCurrentText("Default")
            self.__instance_profile_label.setEnabled(len(profiles) > 1)
            self.__instance_profile_dropdown.setEnabled(len(profiles) > 1)
        else:
            self.__instance_profile_label.setDisabled(True)
            self.__instance_profile_dropdown.setDisabled(True)

        self.__instance_path_label.setEnabled(modinstance == "Portable")
        self.__instance_path_entry.setEnabled(modinstance == "Portable")
        self.__instance_path_entry.clear()

        self._validate()

    def __on_path_change(self, new_path: str) -> None:
        ini_path = Path(new_path) / "ModOrganizer.ini"

        if ini_path.is_file():
            profiles = ModOrganizer.get_profiles_from_ini(ini_path)

        else:
            profiles = []

        self.__instance_profile_dropdown.clear()
        self.__instance_profile_dropdown.addItems(profiles)
        self.__instance_profile_dropdown.setEnabled(len(profiles) > 1)
        self.__instance_profile_label.setEnabled(len(profiles) > 1)

        self._validate()
