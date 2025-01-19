"""
Copyright (c) Cutleast
"""

import pytest
from pytestqt.qtbot import QtBot

from src.ui.widgets.paste_entry import PasteLineEdit

from .._setup.clipboard import Clipboard
from ..base_test import BaseTest


class TestPasteLineEdit(BaseTest):
    """
    Tests `ui.widgets.paste_entry.PasteLineEdit`.
    """

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> PasteLineEdit:
        """
        Fixture to create and provide a PasteLineEdit instance for tests.

        Args:
            qtbot (QtBot): The QtBot fixture.

        Returns:
            PasteLineEdit: The created PasteLineEdit instance.
        """

        paste_line_edit = PasteLineEdit()
        qtbot.addWidget(paste_line_edit)
        return paste_line_edit

    def test_initial_state(self, widget: PasteLineEdit) -> None:
        """
        Test the initial state of the widget.

        Args:
            widget (PasteLineEdit): The PasteLineEdit instance to test.
        """

        assert widget.text() == ""

    def test_paste_action_pastes_text(
        self, widget: PasteLineEdit, clipboard: Clipboard
    ) -> None:
        """
        Test the paste action pastes the text to the clipboard.

        Args:
            widget (PasteLineEdit): The PasteLineEdit instance to test.
            clipboard (Clipboard): The mocked clipboard.
        """

        # given
        test_text: str = "Hello, Clipboard!"
        clipboard.copy(test_text)

        # when
        widget.paste_action.trigger()

        # then
        assert widget.text() == test_text

    def test_paste_action_ignores_empty_text(
        self, widget: PasteLineEdit, clipboard: Clipboard
    ) -> None:
        """
        Test the paste action does not paste empty text to the clipboard.

        Args:
            widget (PasteLineEdit): The PasteLineEdit instance to test.
            clipboard (Clipboard): The mocked clipboard.
        """

        # given
        test_text: str = "Hello, Clipboard!"
        widget.setText(test_text)
        clipboard.copy("")

        # when
        widget.paste_action.trigger()

        # then
        assert widget.text() == test_text
