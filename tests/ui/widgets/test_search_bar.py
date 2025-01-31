"""
Copyright (c) Cutleast
"""

import os
from typing import Any, Optional

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from src.ui.widgets.search_bar import SearchBar

from ..ui_test import UiTest

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


class TestSearchBar(UiTest):
    """
    Tests `ui.widgets.search_bar.SearchBar`.
    """

    CS_TOGGLE_IDENTIFIER = "_SearchBar__cs_toggle"
    CLEAR_BUTTON_IDENTIFIER = "_SearchBar__clear_button"

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> SearchBar:
        """
        Fixture to create and provide a SearchBar instance for tests.
        """

        search_bar = SearchBar()
        qtbot.addWidget(search_bar)
        search_bar.show()
        return search_bar

    def get_clear_button(self, widget: SearchBar) -> QPushButton:
        clear_button: Optional[Any] = getattr(
            widget, TestSearchBar.CLEAR_BUTTON_IDENTIFIER, None
        )

        if clear_button is None:
            raise ValueError("Clear button not found!")
        elif not isinstance(clear_button, QPushButton):
            raise TypeError("Clear button is not a QPushButton!")

        return clear_button

    def get_cs_toggle(self, widget: SearchBar) -> QPushButton:
        cs_toggle: Optional[Any] = getattr(
            widget, TestSearchBar.CS_TOGGLE_IDENTIFIER, None
        )

        if cs_toggle is None:
            raise ValueError("Case sensitivity toggle button not found!")
        if not isinstance(cs_toggle, QPushButton):
            raise TypeError("Case sensitivity toggle button is not a QPushButton!")

        return cs_toggle

    def test_initial_state(self, widget: SearchBar) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        clear_button: QPushButton = self.get_clear_button(widget)
        cs_toggle: QPushButton = self.get_cs_toggle(widget)

        # then
        assert widget.text() == ""
        assert not widget.getCaseSensitivity()
        assert clear_button.isHidden()
        assert not cs_toggle.isChecked()
        assert cs_toggle.isHidden()

    def test_text_change_updates_buttons(self, widget: SearchBar, qtbot: QtBot) -> None:
        """
        Test that entering text updates the visibility of the clear and toggle buttons.
        """

        # given
        clear_button: QPushButton = self.get_clear_button(widget)
        cs_toggle: QPushButton = self.get_cs_toggle(widget)

        # when
        assert clear_button.isHidden()
        assert cs_toggle.isHidden()
        widget.setText("Search Text")

        # then
        qtbot.waitUntil(lambda: clear_button.isVisible() and cs_toggle.isVisible())

    def test_clear_button_functionality(self, widget: SearchBar, qtbot: QtBot) -> None:
        """
        Test that clicking the clear button clears the text and hides the buttons.
        """

        # given
        clear_button: QPushButton = self.get_clear_button(widget)
        cs_toggle: QPushButton = self.get_cs_toggle(widget)

        # when
        widget.setText("Search Text")
        qtbot.waitUntil(lambda: clear_button.isVisible() and cs_toggle.isVisible())
        qtbot.mouseClick(clear_button, Qt.MouseButton.LeftButton)

        # then
        assert widget.text() == ""
        assert clear_button.isHidden()
        assert cs_toggle.isHidden()

    def test_case_sensitivity_toggle(self, widget: SearchBar, qtbot: QtBot) -> None:
        """
        Test the case sensitivity toggle button.
        """

        # given
        cs_toggle: QPushButton = self.get_cs_toggle(widget)

        # when
        widget.setText("Search Text")
        qtbot.waitUntil(cs_toggle.isVisible)
        qtbot.mouseClick(cs_toggle, Qt.MouseButton.LeftButton)
        assert cs_toggle.isChecked()
        assert widget.getCaseSensitivity()
        qtbot.mouseClick(cs_toggle, Qt.MouseButton.LeftButton)

        # then
        assert not cs_toggle.isChecked()
        assert not widget.getCaseSensitivity()

    def test_live_mode_signal_emission(self, widget: SearchBar, qtbot: QtBot) -> None:
        """
        Test that the `searchChanged` signal is emitted in live mode.
        """

        # given
        widget.setLiveMode(True)

        # when
        with qtbot.waitSignal(widget.searchChanged, timeout=1000) as signal:
            widget.setText("Live Test")

        # then
        assert signal.args == [("Live Test", False)]

    def test_return_pressed_signal(self, widget: SearchBar, qtbot: QtBot) -> None:
        """
        Test that pressing return emits the searchChanged signal in non-live mode.
        """

        # given
        widget.setLiveMode(False)

        # when
        with qtbot.waitSignal(widget.searchChanged, timeout=1000) as signal:
            qtbot.keyPress(widget, Qt.Key.Key_Return)

        # then
        assert signal.args == [("", False)]
