"""
Copyright (c) Cutleast
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from cutleast_core_lib.test.utils import Utils
from pytestqt.qtbot import QtBot

from core.database.translation import Translation
from core.editor.editor import Editor
from core.editor.models.editor_string import EditorString
from core.string.string_status import StringStatus
from core.translator.service import TranslatorService
from core.user_data.user_data import UserData
from tests.base_test import BaseTest
from ui.translation_editor.editor.dialog.dialog import TranslatorDialog
from ui.translation_editor.editor.editor_tab import EditorTab
from ui.translation_editor.editor.strings_widget import StringsWidget


class TestEditorTab(BaseTest):
    """
    Smoke tests for `ui.translation_editor.editor.editor_tab.EditorTab`.
    """

    EDITOR: tuple[str, type[Editor]] = "editor", Editor
    """Identifier for accessing the private editor field."""

    STRINGS_WIDGET: tuple[str, type[StringsWidget]] = "strings_widget", StringsWidget
    """Identifier for accessing the private strings_widget field."""

    DIALOG: tuple[str, type[TranslatorDialog]] = "dialog", TranslatorDialog
    """Identifier for accessing the private dialog field."""

    TRANSLATION_NAME: str = "Wet and Cold SE - German"
    """The name of the edited test translation."""

    @pytest.fixture
    def editor_tab(
        self, user_data: UserData, user_data_path: Path, qtbot: QtBot
    ) -> EditorTab:
        """
        Creates and shows an editor tab for the test translation and waits until the
        background initialization of the editor is finished.

        Args:
            user_data (UserData): The test user data.
            user_data_path (Path): The path to the test user data.
            qtbot (QtBot): The Qt bot fixture.

        Returns:
            EditorTab: The editor tab.
        """

        translation: Translation = next(
            translation
            for translation in user_data.database.user_translations
            if translation.name == TestEditorTab.TRANSLATION_NAME
        )
        editor_tab = EditorTab(
            translation,
            user_data,
            MagicMock(spec=TranslatorService),
            user_data_path,
        )
        qtbot.addWidget(editor_tab)
        editor_tab.show()

        editor: Editor = Utils.get_private_field(editor_tab, *TestEditorTab.EDITOR)
        qtbot.waitUntil(
            lambda: all(s.context is not None for s in editor.all_strings),
            timeout=30_000,
        )

        return editor_tab

    def test_shows_all_strings(self, editor_tab: EditorTab) -> None:
        """
        Tests that all strings of the translation are listed after initialization.
        """

        # given
        strings_widget: StringsWidget = Utils.get_private_field(
            editor_tab, *TestEditorTab.STRINGS_WIDGET
        )

        # then
        assert strings_widget.get_visible_string_count() == 204
        assert not editor_tab.changes_pending

    def test_dialog_edit_marks_changes_pending(
        self, editor_tab: EditorTab, qtbot: QtBot
    ) -> None:
        """
        Tests that a text entered in the translator dialog is applied to the string
        and marks the tab as changed.
        """

        # given
        editor: Editor = Utils.get_private_field(editor_tab, *TestEditorTab.EDITOR)
        dialog: TranslatorDialog = Utils.get_private_field(
            editor_tab, *TestEditorTab.DIALOG
        )
        string: EditorString = editor.all_strings[0]

        # when
        with qtbot.waitSignal(editor_tab.changed_signal):
            dialog.text_changed.emit(string, "Geänderter Text")

        # then
        assert editor_tab.changes_pending
        assert string.string.string == "Geänderter Text"
        assert string.string.status == StringStatus.TranslationIncomplete

    def test_close_tab(self, editor_tab: EditorTab) -> None:
        """
        Tests that an unmodified tab can be closed.
        """

        # when / then
        assert editor_tab.close_tab()
