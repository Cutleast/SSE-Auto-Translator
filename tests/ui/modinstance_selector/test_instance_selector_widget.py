"""
Copyright (c) Cutleast
"""

from typing import Optional, cast

import pytest
from cutleast_core_lib.test.utils import Utils
from pyfakefs.fake_filesystem import FakeFilesystem
from PySide6.QtWidgets import QComboBox, QStackedLayout, QWidget
from pytestqt.qtbot import QtBot

from core.mod_managers.instance_info import InstanceInfo
from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer.mo2_instance_info import Mo2InstanceInfo
from core.mod_managers.vortex.profile_info import ProfileInfo
from tests.base_test import BaseTest
from tests.setup.mock_plyvel import MockPlyvelDB
from ui.modinstance_selector.base_selector_widget import BaseSelectorWidget
from ui.modinstance_selector.instance_selector_widget import InstanceSelectorWidget
from ui.modinstance_selector.modorganizer_selector_widget import (
    ModOrganizerSelectorWidget,
)
from ui.modinstance_selector.vortex_selector_widget import VortexSelectorWidget
from ui.widgets.enum_placeholder_dropdown import EnumPlaceholderDropdown

from .test_vortex_selector_widget import TestVortexSelectorWidget


class TestInstanceSelectorWidget(BaseTest):
    """
    Tests `ui.modinstance_selector.instance_selector_widget.InstanceSelectorWidget`.
    """

    CUR_INSTANCE_DATA: tuple[str, type[InstanceInfo]] = (
        "cur_instance_data",
        InstanceInfo,
    )
    """Identifier for accessing the private cur_instance_data field."""

    CUR_MOD_MANAGER: tuple[str, type[ModManager]] = "cur_mod_manager", ModManager
    """Identifier for accessing the private cur_mod_manager field."""

    MOD_MANAGERS: tuple[str, type[dict[ModManager, BaseSelectorWidget]]] = (
        "mod_managers",
        dict[ModManager, BaseSelectorWidget],
    )
    """Identifier for accessing the private mod_managers field."""

    MOD_MANAGER_DROPDOWN: tuple[str, type[EnumPlaceholderDropdown[ModManager]]] = (
        "mod_manager_dropdown",
        EnumPlaceholderDropdown[ModManager],
    )
    """Identifier for accessing the private mod_manager_dropdown field."""

    INSTANCE_STACK_LAYOUT: tuple[str, type[QStackedLayout]] = (
        "instance_stack_layout",
        QStackedLayout,
    )
    """Identifier for accessing the private instance_stack_layout field."""

    PLACEHOLDER_WIDGET: tuple[str, type[QWidget]] = "placeholder_widget", QWidget
    """Identifier for accessing the private placeholder_widget field."""

    @pytest.fixture
    def widget(
        self, test_fs: FakeFilesystem, vortex_db: MockPlyvelDB, qtbot: QtBot
    ) -> InstanceSelectorWidget:
        """
        Fixture to create and provide an InstanceSelectorWidget instance for tests.
        """

        instance_selector_widget = InstanceSelectorWidget()
        qtbot.addWidget(instance_selector_widget)
        instance_selector_widget.show()
        return instance_selector_widget

    def assert_initial_state(self, widget: InstanceSelectorWidget) -> None:
        """
        Asserts the initial state of the widget.
        """

        cur_instance_data: Optional[InstanceInfo] = Utils.get_private_field_optional(
            widget, *TestInstanceSelectorWidget.CUR_INSTANCE_DATA
        )
        cur_mod_manager: Optional[ModManager] = Utils.get_private_field_optional(
            widget, *TestInstanceSelectorWidget.CUR_MOD_MANAGER
        )
        mod_manager_dropdown: EnumPlaceholderDropdown[ModManager] = (
            Utils.get_private_field(
                widget, *TestInstanceSelectorWidget.MOD_MANAGER_DROPDOWN
            )
        )
        instance_stack_layout: QStackedLayout = Utils.get_private_field(
            widget, *TestInstanceSelectorWidget.INSTANCE_STACK_LAYOUT
        )
        placeholder_widget: QWidget = Utils.get_private_field(
            widget, *TestInstanceSelectorWidget.PLACEHOLDER_WIDGET
        )

        assert cur_instance_data is None
        assert cur_mod_manager is None
        assert mod_manager_dropdown.currentIndex() == -1
        assert instance_stack_layout.currentWidget() is placeholder_widget
        assert not widget.validate()

    def test_initial_state(self, widget: InstanceSelectorWidget) -> None:
        """
        Tests the initial state of the widget.
        """

        self.assert_initial_state(widget)

    def test_select_mo2_instance(
        self,
        widget: InstanceSelectorWidget,
        mo2_instance_info: Mo2InstanceInfo,
        qtbot: QtBot,
    ) -> None:
        """
        Tests the selection of an MO2 instance.
        """

        # given
        mod_manager_dropdown: EnumPlaceholderDropdown[ModManager] = (
            Utils.get_private_field(
                widget, *TestInstanceSelectorWidget.MOD_MANAGER_DROPDOWN
            )
        )
        instance_stack_layout: QStackedLayout = Utils.get_private_field(
            widget, *TestInstanceSelectorWidget.INSTANCE_STACK_LAYOUT
        )
        mo2_selector_widget: ModOrganizerSelectorWidget = cast(
            ModOrganizerSelectorWidget,
            Utils.get_private_field(widget, *TestInstanceSelectorWidget.MOD_MANAGERS)[
                ModManager.ModOrganizer
            ],
        )

        # when
        with qtbot.waitSignals([widget.changed, widget.instance_valid], order="simple"):
            mod_manager_dropdown.setCurrentValue(ModManager.ModOrganizer)

        # then
        assert instance_stack_layout.currentWidget() is mo2_selector_widget
        assert not widget.validate()

        # when
        with qtbot.waitSignals([widget.changed, widget.instance_valid], order="simple"):
            mo2_selector_widget.set_instance(mo2_instance_info)

        # then
        assert widget.validate()

        # when
        instance_info: Optional[InstanceInfo] = widget.get_cur_instance_data()

        # then
        assert instance_info == mo2_instance_info

    def test_change_instance(
        self,
        widget: InstanceSelectorWidget,
        mo2_instance_info: Mo2InstanceInfo,
        vortex_profile_info: ProfileInfo,
        qtbot: QtBot,
    ) -> None:
        """
        Tests the changing of from one mod instance to another.
        """

        # given
        mod_manager_dropdown: EnumPlaceholderDropdown[ModManager] = (
            Utils.get_private_field(
                widget, *TestInstanceSelectorWidget.MOD_MANAGER_DROPDOWN
            )
        )
        instance_stack_layout: QStackedLayout = Utils.get_private_field(
            widget, *TestInstanceSelectorWidget.INSTANCE_STACK_LAYOUT
        )
        mo2_selector_widget: ModOrganizerSelectorWidget = cast(
            ModOrganizerSelectorWidget,
            Utils.get_private_field(widget, *TestInstanceSelectorWidget.MOD_MANAGERS)[
                ModManager.ModOrganizer
            ],
        )
        vortex_selector_widget: VortexSelectorWidget = cast(
            VortexSelectorWidget,
            Utils.get_private_field(widget, *TestInstanceSelectorWidget.MOD_MANAGERS)[
                ModManager.Vortex
            ],
        )
        vortex_profile_dropdown: QComboBox = Utils.get_private_field(
            vortex_selector_widget, *TestVortexSelectorWidget.PROFILE_DROPDOWN
        )

        # when
        widget.set_cur_instance_data(mo2_instance_info)

        # then
        assert mod_manager_dropdown.getCurrentValue() == ModManager.ModOrganizer
        assert instance_stack_layout.currentWidget() is mo2_selector_widget
        assert widget.validate()
        assert widget.get_cur_instance_data() == mo2_instance_info

        # when
        with qtbot.waitSignals([widget.changed, widget.instance_valid]):
            mod_manager_dropdown.setCurrentValue(ModManager.Vortex)

        # then
        assert instance_stack_layout.currentWidget() is vortex_selector_widget
        assert not widget.validate()
        assert widget.get_cur_instance_data() is None

        # when
        with qtbot.waitSignals([widget.changed, widget.instance_valid]):
            vortex_profile_dropdown.setCurrentText(vortex_profile_info.display_name)

        # then
        assert widget.validate()
        assert widget.get_cur_instance_data() == vortex_profile_info

    def test_unselect_instance(
        self,
        widget: InstanceSelectorWidget,
        mo2_instance_info: Mo2InstanceInfo,
        qtbot: QtBot,
    ) -> None:
        """
        Tests the unselection of an instance.
        """

        # given
        mod_manager_dropdown: EnumPlaceholderDropdown[ModManager] = (
            Utils.get_private_field(
                widget, *TestInstanceSelectorWidget.MOD_MANAGER_DROPDOWN
            )
        )
        instance_stack_layout: QStackedLayout = Utils.get_private_field(
            widget, *TestInstanceSelectorWidget.INSTANCE_STACK_LAYOUT
        )
        mo2_selector_widget: ModOrganizerSelectorWidget = cast(
            ModOrganizerSelectorWidget,
            Utils.get_private_field(widget, *TestInstanceSelectorWidget.MOD_MANAGERS)[
                ModManager.ModOrganizer
            ],
        )
        placeholder_widget: QWidget = Utils.get_private_field(
            widget, *TestInstanceSelectorWidget.PLACEHOLDER_WIDGET
        )

        # when
        widget.set_cur_instance_data(mo2_instance_info)

        # then
        assert instance_stack_layout.currentWidget() is mo2_selector_widget
        assert widget.validate()
        assert widget.get_cur_instance_data() == mo2_instance_info

        # when
        with qtbot.waitSignals([widget.changed, widget.instance_valid]):
            mod_manager_dropdown.setCurrentValue(None)

        # then
        assert instance_stack_layout.currentWidget() is placeholder_widget
        assert not widget.validate()
        assert widget.get_cur_instance_data() is None

    def test_change_between_empty_instances(
        self,
        widget: InstanceSelectorWidget,
        mo2_instance_info: Mo2InstanceInfo,
        qtbot: QtBot,
    ) -> None:
        """
        Tests changing the mod manager between empty instances.
        """

        # given
        mod_manager_dropdown: EnumPlaceholderDropdown[ModManager] = (
            Utils.get_private_field(
                widget, *TestInstanceSelectorWidget.MOD_MANAGER_DROPDOWN
            )
        )
        # set initial instance
        widget.set_cur_instance_data(mo2_instance_info)

        # when
        mod_manager_dropdown.setCurrentValue(ModManager.Vortex)

        # then
        assert widget.get_cur_instance_data() is None
        assert not widget.validate()

        # when
        mod_manager_dropdown.setCurrentValue(ModManager.ModOrganizer)

        # then
        assert widget.get_cur_instance_data() is None
        assert not widget.validate()

        # when
        mod_manager_dropdown.setCurrentValue(ModManager.Vortex)

        # then
        assert widget.get_cur_instance_data() is None
        assert not widget.validate()
