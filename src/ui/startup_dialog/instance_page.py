"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import override

from core.config.user_config import UserConfig
from ui.modinstance_selector.instance_selector_widget import InstanceSelectorWidget
from ui.startup_dialog.page import Page


class InstancePage(Page):
    """
    Third page. Asks user which mod instance from which mod manager to load.
    """

    __modinstance_selector: InstanceSelectorWidget

    @override
    def _init_form(self) -> None:
        self.__modinstance_selector = InstanceSelectorWidget()
        self.__modinstance_selector.instance_valid.connect(self.valid_signal.emit)
        self._vlayout.addWidget(self.__modinstance_selector)

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
        self.valid_signal.emit(self.__modinstance_selector.validate())

    @override
    def apply(self, config: UserConfig) -> None:
        config.modinstance = self.__modinstance_selector.get_cur_instance_data()  # pyright: ignore[reportAttributeAccessIssue]
