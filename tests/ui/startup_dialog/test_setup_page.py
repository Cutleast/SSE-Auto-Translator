"""
Copyright (c) Cutleast
"""

from typing import Any, Optional

import pytest
from PySide6.QtWidgets import QComboBox

from app import App
from ui.startup_dialog.setup_page import SetupPage

from ...app_test import AppTest
from ..ui_test import UiTest


class TestSetupPage(UiTest, AppTest):
    """
    Tests `ui.startup_dialog.setup_page.SetupPage`.
    """

    LANG_DROPDOWN_IDENTIFIER: str = "_SetupPage__lang_dropdown"

    def get_lang_dropdown(self, widget: SetupPage) -> QComboBox:
        lang_dropdown: Optional[Any] = getattr(
            widget, TestSetupPage.LANG_DROPDOWN_IDENTIFIER, None
        )

        if lang_dropdown is None:
            raise ValueError("Language dropdown not found!")
        elif not isinstance(lang_dropdown, QComboBox):
            raise TypeError("Language dropdown is not a QComboBox!")

        return lang_dropdown

    langs: list[tuple[Optional[str], str]] = [
        ("french", "French"),
        ("german", "German"),
        (None, ""),
    ]

    @pytest.mark.parametrize("lang, expected_output", langs)
    def test_preselected_lang(
        self,
        lang: Optional[str],
        expected_output: str,
        app_context: App,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Tests the preselected language for the game based on the system language.
        """

        # given
        monkeypatch.setattr(
            "core.utilities.localisation.LocalisationUtils.detect_preferred_lang",
            lambda: lang,
        )

        # when
        setup_page = SetupPage()

        # then
        assert self.get_lang_dropdown(setup_page).currentText() == expected_output
