"""
Copyright (c) Cutleast
"""

import re
from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel

from core.mod_managers.mod_manager import ModManager
from core.mod_managers.vortex.profile_info import ProfileInfo
from core.mod_managers.vortex.vortex_api import VortexApi

from .base_selector_widget import BaseSelectorWidget


class VortexSelectorWidget(BaseSelectorWidget[ProfileInfo, VortexApi]):
    """
    Class for selecting profiles from Vortex.
    """

    __profile_dropdown: QComboBox
    __glayout: QGridLayout

    @override
    @staticmethod
    def get_mod_manager() -> ModManager:
        return ModManager.Vortex

    @override
    def _init_ui(self) -> None:
        self.__glayout = QGridLayout()
        self.__glayout.setContentsMargins(0, 0, 0, 0)
        self.__glayout.setColumnStretch(0, 1)
        self.__glayout.setColumnStretch(1, 3)
        self.__glayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__glayout)

        profile_label = QLabel(self.tr("Profile:"))
        self.__glayout.addWidget(profile_label, 0, 0)

        self.__profile_dropdown = QComboBox()
        self.__profile_dropdown.installEventFilter(self)
        self.__profile_dropdown.addItem(self.tr("Please select..."))
        self.__profile_dropdown.addItems(self._instance_names)
        self.__profile_dropdown.currentTextChanged.connect(
            lambda _: self.changed.emit()
        )
        self.__glayout.addWidget(self.__profile_dropdown, 0, 1)

    @override
    def _update(self) -> None:
        self.__profile_dropdown.clear()
        self.__profile_dropdown.addItem(self.tr("Please select..."))
        self.__profile_dropdown.addItems(self._instance_names)
        self.changed.emit()

    @override
    def validate(self) -> bool:
        valid: bool = self.__profile_dropdown.currentIndex() > 0

        return valid

    @override
    def get_instance(self) -> ProfileInfo:
        instance_name: str = self.__profile_dropdown.currentText()
        match: Optional[re.Match] = re.match(r"^(.*) \((.*)\)$", instance_name)

        if match is None:
            raise ValueError(f"Invalid instance name: {instance_name!r}")

        profile_id: str = match.group(2)

        return ProfileInfo(
            display_name=instance_name, id=profile_id, mod_manager=ModManager.Vortex
        )

    @override
    def set_instance(self, instance_data: ProfileInfo) -> None:
        self.__profile_dropdown.setCurrentText(instance_data.display_name)

    @override
    def reset(self) -> None:
        self.__profile_dropdown.setCurrentIndex(0)
