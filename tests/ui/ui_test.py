"""
Copyright (c) Cutleast
"""

import os

import pytest

from ..base_test import BaseTest
from ._setup.clipboard import Clipboard

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


class UiTest(BaseTest):
    """
    Base class for all ui-related tests.
    """

    @pytest.fixture
    def clipboard(self, monkeypatch: pytest.MonkeyPatch) -> Clipboard:
        """
        Fixture to mock the clipboard using `_setup.clipboard.Clipboard`.
        Patches `QtGui.QClipboard.setText` and `QtGui.QClipboard.text`.

        Args:
            monkeypatch (pytest.MonkeyPatch): The MonkeyPatch fixture.

        Returns:
            Clipboard: The mocked clipboard.
        """

        clipboard = Clipboard()

        monkeypatch.setattr("PySide6.QtGui.QClipboard.setText", clipboard.copy)
        monkeypatch.setattr("PySide6.QtGui.QClipboard.text", clipboard.paste)

        return clipboard
