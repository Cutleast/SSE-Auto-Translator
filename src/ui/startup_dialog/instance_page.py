"""
Copyright (c) Cutleast
"""

from typing import Optional, cast, override

from mod_manager_lib.core.game_service import GameService
from mod_manager_lib.core.mod_manager.modorganizer.instance_info import MO2InstanceInfo
from mod_manager_lib.core.mod_manager.vortex.profile_info import ProfileInfo
from mod_manager_lib.ui.instance_selector.instance_selector_widget import (
    InstanceSelectorWidget,
)
from PySide6.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout

from core.config.user_config import UserConfig
from core.utilities.constants import GAME_ID

from .page import Page


class InstancePage(Page):
    """
    Third page. Asks user which mod instance from which mod manager to load.
    """

    __modinstance_selector: InstanceSelectorWidget
    __parse_bsas_checkbox: QCheckBox

    @override
    def _init_form(self) -> None:
        modinstance_groupbox = QGroupBox(self.tr("Modlist"))
        self._vlayout.addWidget(modinstance_groupbox)
        modinstance_vlayout = QVBoxLayout()
        modinstance_groupbox.setLayout(modinstance_vlayout)

        self.__modinstance_selector = InstanceSelectorWidget()
        self.__modinstance_selector.set_cur_game(GameService.get_game_by_id(GAME_ID))
        self.__modinstance_selector.instance_valid.connect(self.valid_signal.emit)
        modinstance_vlayout.addWidget(self.__modinstance_selector)

        options_groupbox = QGroupBox(self.tr("Options"))
        self._vlayout.addWidget(options_groupbox)
        options_vlayout = QVBoxLayout()
        options_groupbox.setLayout(options_vlayout)

        self.__parse_bsas_checkbox = QCheckBox(
            self.tr(
                "Parse BSA archives (This may slow down app startup depending on the "
                "size of your modlist!)"
            )
        )
        self.__parse_bsas_checkbox.setChecked(True)
        options_vlayout.addWidget(self.__parse_bsas_checkbox)

        self._vlayout.addStretch()

    @override
    def _get_title(self) -> str:
        return self.tr("Modlist")

    @override
    def _get_description(self) -> str:
        return self.tr(
            "On this page you select a modlist to load from a mod manager. You can "
            "always change the selected modlist and mod manager under Settings > User "
            "Settings."
        )

    @override
    def _validate(self) -> None:
        self.valid_signal.emit(self.__modinstance_selector.validate())

    @override
    def apply(self, config: UserConfig) -> None:
        config.mod_instance = cast(
            Optional[MO2InstanceInfo | ProfileInfo],
            self.__modinstance_selector.get_cur_instance_data(),
        )
        config.parse_bsa_archives = self.__parse_bsas_checkbox.isChecked()
