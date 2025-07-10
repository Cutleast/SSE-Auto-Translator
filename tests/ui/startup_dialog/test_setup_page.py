"""
Copyright (c) Cutleast
"""

from typing import Optional

import pytest

from app import App
from core.utilities.game_language import GameLanguage
from tests.utils import Utils
from ui.startup_dialog.setup_page import SetupPage
from ui.widgets.enum_dropdown import EnumDropdown

from ...app_test import AppTest
from ..ui_test import UiTest


class TestSetupPage(UiTest, AppTest):
    """
    Tests `ui.startup_dialog.setup_page.SetupPage`.
    """

    LANG_DROPDOWN: tuple[str, type[EnumDropdown[GameLanguage]]] = (
        "lang_dropdown",
        EnumDropdown,
    )
    """Identifier for accessing the private lang_dropdown field."""

    langs: list[tuple[Optional[str], GameLanguage]] = [
        ("french", GameLanguage.French),
        ("german", GameLanguage.German),
        (None, GameLanguage.Chinese),
    ]

    @pytest.mark.parametrize("lang, expected_output", langs)
    def test_preselected_lang(
        self,
        lang: Optional[str],
        expected_output: GameLanguage,
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
        setup_page = SetupPage(self.cache())
        lang_dropdown: EnumDropdown[GameLanguage] = Utils.get_private_field(
            setup_page, *TestSetupPage.LANG_DROPDOWN
        )

        # then
        assert lang_dropdown.getCurrentValue() == expected_output
