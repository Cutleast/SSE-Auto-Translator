"""
Copyright (c) Cutleast
"""

import pytest
from pytestqt.qtbot import QtBot

from src.ui.widgets.copy_entry import CopyLineEdit

from .._setup.clipboard import Clipboard
from ..base_test import BaseTest


class TestCopyLineEdit(BaseTest):
    """
    Tests `ui.widgets.copy_entry.CopyLineEdit`.
    """

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> CopyLineEdit:
        """
        Fixture to create and provide a CopyLineEdit instance for tests.

        Args:
            qtbot (QtBot): The QtBot fixture.

        Returns:
            CopyLineEdit: The created CopyLineEdit instance.
        """

        copy_line_edit = CopyLineEdit()
        qtbot.addWidget(copy_line_edit)
        return copy_line_edit

    def test_initial_state(self, widget: CopyLineEdit) -> None:
        """
        Test the initial state of the widget.

        Args:
            widget (CopyLineEdit): The CopyLineEdit instance to test.
        """

        assert widget.text() == ""

    def test_copy_action_copies_text(
        self, widget: CopyLineEdit, clipboard: Clipboard
    ) -> None:
        """
        Test the copy action copies the text to the clipboard.

        Args:
            widget (CopyLineEdit): The CopyLineEdit instance to test.
            clipboard (Clipboard): The mocked clipboard.
        """

        # given
        test_text: str = "Hello, Clipboard!"
        widget.setText(test_text)

        # when
        widget.copy_action.trigger()

        # then
        assert clipboard.paste() == test_text

    def test_copy_action_ignores_empty_text(
        self, widget: CopyLineEdit, clipboard: Clipboard
    ) -> None:
        """
        Test the copy action does not copy empty text to the clipboard.

        Args:
            widget (CopyLineEdit): The CopyLineEdit instance to test.
            clipboard (Clipboard): The mocked clipboard.
        """

        # given
        test_text: str = "Existing Content"
        clipboard.copy(test_text)

        # when
        assert widget.text() == ""
        widget.copy_action.trigger()

        # then
        assert clipboard.paste() == test_text
