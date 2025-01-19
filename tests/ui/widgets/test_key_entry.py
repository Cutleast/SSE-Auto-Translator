"""
Copyright (c) Cutleast
"""

import pytest
from PySide6.QtWidgets import QLineEdit
from pytestqt.qtbot import QtBot

from src.ui.widgets.key_entry import KeyEntry

from ..base_test import BaseTest


class TestKeyEntry(BaseTest):
    """
    Tests `ui.widgets.key_entry.KeyEntry`.
    """

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> KeyEntry:
        """
        Fixture to create and provide a KeyEntry instance for tests.

        Args:
            qtbot (QtBot): The QtBot fixture.

        Returns:
            KeyEntry: The created KeyEntry instance.
        """

        key_entry = KeyEntry()
        qtbot.addWidget(key_entry)
        return key_entry

    def test_initial_state(self, widget: KeyEntry) -> None:
        """
        Test the initial state of the widget.
        """

        assert widget.echoMode() == QLineEdit.EchoMode.Password

    def test_visibility_toggle(self, widget: KeyEntry) -> None:
        """
        Test the visibility toggle method.
        """

        # given
        assert widget.echoMode() == QLineEdit.EchoMode.Password

        # when
        widget.toggle_visibility()

        # then
        assert widget.echoMode() == QLineEdit.EchoMode.Normal

    def test_visibility_toggle_action(self, widget: KeyEntry) -> None:
        """
        Test the visibility toggle action.
        """

        # given
        assert widget.echoMode() == QLineEdit.EchoMode.Password

        # when
        widget.toggle_visibility_action.trigger()

        # then
        assert widget.echoMode() == QLineEdit.EchoMode.Normal
