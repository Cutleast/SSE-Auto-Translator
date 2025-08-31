"""
Copyright (c) Cutleast
"""

import pytest
from cutleast_core_lib.test.utils import Utils
from PySide6.QtWidgets import QComboBox
from pytestqt.qtbot import QtBot

from core.mod_managers.vortex.profile_info import ProfileInfo
from core.mod_managers.vortex.vortex_api import VortexApi
from tests.base_test import BaseTest
from tests.setup.mock_plyvel import MockPlyvelDB
from ui.modinstance_selector.vortex_selector_widget import VortexSelectorWidget


class TestVortexSelectorWidget(BaseTest):
    """
    Tests `ui.modinstance_selector.vortex_selector_widget.VortexSelectorWidget`.
    """

    PROFILE_DROPDOWN: tuple[str, type[QComboBox]] = "profile_dropdown", QComboBox
    """Identifier for accessing the private profile_dropdown field."""

    @pytest.fixture
    def widget(self, vortex_db: MockPlyvelDB, qtbot: QtBot) -> VortexSelectorWidget:
        """
        Fixture to create and provide a VortexSelectorWidget instance for tests.
        """

        vortex_widget = VortexSelectorWidget(VortexApi().get_instance_names())
        qtbot.addWidget(vortex_widget)
        vortex_widget.show()
        return vortex_widget

    def assert_initial_state(self, widget: VortexSelectorWidget) -> None:
        """
        Asserts the initial state of the widget.
        """

        profile_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestVortexSelectorWidget.PROFILE_DROPDOWN
        )

        assert profile_dropdown.currentIndex() == 0
        assert profile_dropdown.isEnabled()
        assert profile_dropdown.count() == 3
        assert not widget.validate()

    def test_initial_state(self, widget: VortexSelectorWidget) -> None:
        """
        Tests the initial state of the widget.
        """

        self.assert_initial_state(widget)

    def test_select_profile(
        self,
        vortex_profile_info: ProfileInfo,
        widget: VortexSelectorWidget,
        qtbot: QtBot,
    ) -> None:
        """
        Tests the selection of a profile.
        """

        # given
        profile_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestVortexSelectorWidget.PROFILE_DROPDOWN
        )

        # then
        assert profile_dropdown.count() == 3
        assert profile_dropdown.itemText(1) == "Default (BkIX54nayg)"
        assert profile_dropdown.itemText(2) == "Test Instance (1a2b3c4d)"

        # when
        with qtbot.waitSignal(widget.changed):
            with qtbot.waitSignal(widget.valid) as valid_signal:
                profile_dropdown.setCurrentIndex(1)

        # then
        assert valid_signal.args == [True]
        assert widget.validate()

        # when
        with qtbot.waitSignal(widget.changed):
            with qtbot.waitSignal(widget.valid) as valid_signal:
                profile_dropdown.setCurrentIndex(0)

        # then
        assert valid_signal.args == [False]
        assert not widget.validate()

        # when
        with qtbot.waitSignal(widget.changed):
            with qtbot.waitSignal(widget.valid) as valid_signal:
                profile_dropdown.setCurrentIndex(2)

        # then
        assert valid_signal.args == [True]
        assert widget.validate()

        # when
        profile_info: ProfileInfo = widget.get_instance()

        # then
        assert profile_info.id == vortex_profile_info.id
