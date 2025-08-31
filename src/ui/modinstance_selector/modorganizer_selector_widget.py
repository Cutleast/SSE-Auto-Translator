"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.ui.widgets.browse_edit import BrowseLineEdit
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFileDialog, QGridLayout, QLabel

from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer.mo2_instance_info import Mo2InstanceInfo
from core.mod_managers.modorganizer.modorganizer_api import ModOrganizerApi

from .base_selector_widget import BaseSelectorWidget


class ModOrganizerSelectorWidget(BaseSelectorWidget[Mo2InstanceInfo, ModOrganizerApi]):
    """
    Class for selecting instances from Mod Organizer 2.
    """

    __instance_dropdown: QComboBox
    __portable_path_entry: BrowseLineEdit
    __profile_dropdown: QComboBox
    __glayout: QGridLayout

    @override
    @staticmethod
    def get_mod_manager() -> ModManager:
        return ModManager.ModOrganizer

    @override
    def _init_ui(self) -> None:
        self.__glayout = QGridLayout()
        self.__glayout.setContentsMargins(0, 0, 0, 0)
        self.__glayout.setColumnStretch(0, 1)
        self.__glayout.setColumnStretch(1, 3)
        self.__glayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__glayout)

        instance_label = QLabel(self.tr("Instance:"))
        self.__glayout.addWidget(instance_label, 0, 0)

        self.__instance_dropdown = QComboBox()
        self.__instance_dropdown.installEventFilter(self)
        self.__instance_dropdown.addItem(self.tr("Please select..."))
        self.__instance_dropdown.addItems(self._instance_names)
        self.__instance_dropdown.addItem("Portable")
        self.__instance_dropdown.currentTextChanged.connect(
            lambda _: self.changed.emit()
        )
        self.__instance_dropdown.currentTextChanged.connect(
            lambda _: self.__update_profile_dropdown()
        )
        self.__glayout.addWidget(self.__instance_dropdown, 0, 1)

        portable_path_label = QLabel(self.tr("Portable path:"))
        self.__glayout.addWidget(portable_path_label, 1, 0)

        self.__portable_path_entry = BrowseLineEdit()
        self.__portable_path_entry.setFileMode(QFileDialog.FileMode.Directory)
        self.__portable_path_entry.textChanged.connect(lambda _: self.changed.emit())
        self.__portable_path_entry.textChanged.connect(
            lambda _: self.__update_profile_dropdown()
        )
        self.__portable_path_entry.setDisabled(True)
        self.__glayout.addWidget(self.__portable_path_entry, 1, 1)

        profile_label = QLabel(self.tr("Profile:"))
        self.__glayout.addWidget(profile_label, 2, 0)

        self.__profile_dropdown = QComboBox()
        self.__profile_dropdown.installEventFilter(self)
        self.__profile_dropdown.addItem(self.tr("Please select..."))
        self.__profile_dropdown.currentTextChanged.connect(
            lambda _: self.changed.emit()
        )
        self.__profile_dropdown.setDisabled(True)
        self.__glayout.addWidget(self.__profile_dropdown, 2, 1)

    @override
    def _update(self) -> None:
        self.__instance_dropdown.clear()
        self.__instance_dropdown.addItem(self.tr("Please select..."))
        self.__instance_dropdown.addItems(self._instance_names)
        self.__instance_dropdown.addItem("Portable")
        self.__update_profile_dropdown()

    def __update_profile_dropdown(self) -> None:
        instance_name: str = self.__instance_dropdown.currentText()
        is_global: bool = instance_name != "Portable"

        self.__portable_path_entry.setDisabled(is_global)

        instance_path: Path
        if is_global:
            instance_path = (
                resolve(Path("%LOCALAPPDATA%") / "ModOrganizer") / instance_name
            )
        else:
            instance_path = Path(self.__portable_path_entry.text())

        mo2_ini_path: Path = instance_path / "ModOrganizer.ini"

        self.__profile_dropdown.clear()
        self.__profile_dropdown.addItem(self.tr("Please select..."))
        if mo2_ini_path.is_file():
            self.__profile_dropdown.addItems(
                self._api.get_profile_names(instance_path / "ModOrganizer.ini")
            )
        self.__profile_dropdown.setEnabled(self.__profile_dropdown.count() > 1)
        self.changed.emit()

    @override
    def validate(self) -> bool:
        valid: bool = (
            self.__instance_dropdown.currentIndex() > 0
            and (
                self.__instance_dropdown.currentText() != "Portable"
                or Path(
                    self.__portable_path_entry.text() + "/ModOrganizer.ini"
                ).is_file()
            )
            and self.__profile_dropdown.currentIndex() > 0
        )

        return valid

    @override
    def get_instance(self) -> Mo2InstanceInfo:
        instance_name: str = self.__instance_dropdown.currentText()
        is_global: bool = instance_name != "Portable"
        profile_name: str = self.__profile_dropdown.currentText()

        instance_path: Path
        if is_global:
            instance_path = (
                resolve(Path("%LOCALAPPDATA%") / "ModOrganizer") / instance_name
            )
        else:
            instance_path = Path(self.__portable_path_entry.text())

        if not (instance_path / "ModOrganizer.ini").is_file():
            raise ValueError(
                f"Invalid instance: {instance_path!r}! Please select a valid MO2 instance!"
            )

        instance_ini_path: Path = instance_path / "ModOrganizer.ini"
        mods_folder: Path = ModOrganizerApi.get_mods_folder(instance_ini_path)
        profiles_folder: Path = ModOrganizerApi.get_profiles_folder(instance_ini_path)

        return Mo2InstanceInfo(
            display_name=instance_name,
            profile=profile_name,
            is_global=is_global,
            base_folder=instance_path,
            mods_folder=mods_folder,
            profiles_folder=profiles_folder,
            mod_manager=ModManager.ModOrganizer,
        )

    @override
    def set_instance(self, instance_data: Mo2InstanceInfo) -> None:
        self.__instance_dropdown.setCurrentText(
            instance_data.display_name if instance_data.is_global else "Portable"
        )
        self.__portable_path_entry.setText(str(instance_data.base_folder))
        self.__profile_dropdown.setCurrentText(instance_data.profile)
        self.changed.emit()

    @override
    def reset(self) -> None:
        self.__instance_dropdown.setCurrentIndex(0)
        self.__portable_path_entry.setText("")
        self.__profile_dropdown.setCurrentIndex(0)
        self.changed.emit()
