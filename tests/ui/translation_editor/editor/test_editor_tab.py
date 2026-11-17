"""
Copyright (c) Cutleast
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.utilities.text_edit_history import TextEditHistory
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QPushButton
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from core.database.translation import Translation
from core.editor.editor import Editor
from core.editor.models.editor_string import EditorString
from core.string.string_status import StringStatus
from core.translator.models.request import TranslationRequest
from core.translator.models.result import TranslationResult
from core.translator.service import TranslatorService
from core.user_data.user_data import UserData
from tests.base_test import BaseTest
from tests.setup.data_factory import DataFactory
from tests.setup.paths import DICTIONARY_PATH
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

    HISTORY: tuple[str, type[TextEditHistory]] = "history", TextEditHistory
    """Identifier for accessing the private history field of the translator dialog."""

    TRANSLATION_NAME: str = "Wet and Cold SE - German"
    """The name of the edited test translation."""

    @pytest.fixture
    def editor_tab(self, tmp_path: Path, qtbot: QtBot) -> EditorTab:
        """
        Creates and shows an editor tab for the test translation and waits until the
        background initialization of the editor is finished.

        Args:
            tmp_path (Path): The temporary folder of the test.
            qtbot (QtBot): The Qt bot fixture.

        Returns:
            EditorTab: The editor tab.
        """

        translation: Translation = DataFactory.stored_translation(
            TestEditorTab.TRANSLATION_NAME, tmp_path
        )
        user_data: UserData = DataFactory.user_data(
            tmp_path / "user", DataFactory.database(tmp_path, [translation])
        )
        editor_tab = EditorTab(
            translation,
            user_data,
            MagicMock(spec=TranslatorService),
            tmp_path / "user",
            DICTIONARY_PATH,
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
            dialog.text_changed.emit(string, "Geänderter Text", False)

        # then
        assert editor_tab.changes_pending
        assert string.string.string == "Geänderter Text"
        assert string.string.status == StringStatus.TranslationIncomplete

    def test_api_translation_replaces_only_selected_part(
        self, editor_tab: EditorTab, mocker: MockerFixture
    ) -> None:
        """
        Tests that the API translation button translates only the selected part of the
        translated text and states this in its text.
        """

        # given
        editor: Editor = Utils.get_private_field(editor_tab, *TestEditorTab.EDITOR)
        dialog: TranslatorDialog = Utils.get_private_field(
            editor_tab, *TestEditorTab.DIALOG
        )
        translated_edit: QPlainTextEdit = Utils.get_private_field(
            dialog, "translated_edit", QPlainTextEdit
        )
        api_translate_button: QPushButton = Utils.get_private_field(
            dialog, "api_translate_button", QPushButton
        )
        translator_service: MagicMock = Utils.get_private_field(
            editor_tab, "translator_service", MagicMock
        )
        translator: MagicMock = translator_service.get_translator.return_value
        translator.supports_instructions.return_value = False
        translator.translate.side_effect = lambda request, _: TranslationResult(
            request=request, translated_text="schönes"
        )
        mocker.patch(
            "ui.translation_editor.editor.editor_tab.ProgressDialog",
            side_effect=lambda function, _: MagicMock(run=lambda: function(MagicMock())),
        )

        string: EditorString = editor.all_strings[0]
        dialog.set_string(string, 0)
        translated_edit.setPlainText("Ein beautiful Schwert")
        cursor: QTextCursor = translated_edit.textCursor()
        cursor.setPosition(3)
        cursor.setPosition(14, QTextCursor.MoveMode.KeepAnchor)
        translated_edit.setTextCursor(cursor)

        # when
        button_text: str = api_translate_button.text()
        api_translate_button.click()

        # then
        request: TranslationRequest = translator.translate.call_args.args[0]
        assert button_text == "Translate selected part with API"
        assert request.text == "beautiful"
        assert request.excerpt is not None
        assert request.excerpt.prefix == "Ein "
        assert request.excerpt.suffix == " Schwert"
        assert translated_edit.toPlainText() == "Ein schönes Schwert"
        assert translated_edit.textCursor().selection().toPlainText() == "schönes"
        assert string.string.string == "Ein schönes Schwert"
        assert string.string.status == StringStatus.TranslationIncomplete

        # when
        translated_edit.undo()

        # then
        assert translated_edit.toPlainText() == "Ein beautiful Schwert"

    def test_api_translation_is_undoable_and_recorded(
        self, editor_tab: EditorTab, mocker: MockerFixture
    ) -> None:
        """
        Tests that an API translation of the entire string is applied directly, recorded
        as revision in the edit history and can be undone.
        """

        # given
        editor: Editor = Utils.get_private_field(editor_tab, *TestEditorTab.EDITOR)
        dialog: TranslatorDialog = Utils.get_private_field(
            editor_tab, *TestEditorTab.DIALOG
        )
        history: TextEditHistory = Utils.get_private_field(
            dialog, *TestEditorTab.HISTORY
        )
        translated_edit: QPlainTextEdit = Utils.get_private_field(
            dialog, "translated_edit", QPlainTextEdit
        )
        api_translate_button: QPushButton = Utils.get_private_field(
            dialog, "api_translate_button", QPushButton
        )
        translator_service: MagicMock = Utils.get_private_field(
            editor_tab, "translator_service", MagicMock
        )
        translator: MagicMock = translator_service.get_translator.return_value
        translator.supports_instructions.return_value = False
        translator.translate.side_effect = lambda request, _: TranslationResult(
            request=request, translated_text="Ein schönes Schwert"
        )
        mocker.patch(
            "ui.translation_editor.editor.editor_tab.ProgressDialog",
            side_effect=lambda function, _: MagicMock(run=lambda: function(MagicMock())),
        )

        string: EditorString = editor.all_strings[0]
        dialog.set_string(string, 0)
        translated_edit.setPlainText("Ein Schwert")

        # when
        api_translate_button.click()

        # then
        assert translated_edit.toPlainText() == "Ein schönes Schwert"
        assert string.string.string == "Ein schönes Schwert"
        assert string.string.status == StringStatus.TranslationIncomplete
        assert [revision.text for revision in history.revisions][-2:] == [
            "Ein Schwert",
            "Ein schönes Schwert",
        ]

        # when
        translated_edit.undo()

        # then
        assert translated_edit.toPlainText() == "Ein Schwert"

    def test_history_is_cleared_on_string_change(self, editor_tab: EditorTab) -> None:
        """
        Tests that the edit history only contains the loaded text after another string
        was loaded.
        """

        # given
        editor: Editor = Utils.get_private_field(editor_tab, *TestEditorTab.EDITOR)
        dialog: TranslatorDialog = Utils.get_private_field(
            editor_tab, *TestEditorTab.DIALOG
        )
        history: TextEditHistory = Utils.get_private_field(
            dialog, *TestEditorTab.HISTORY
        )
        translated_edit: QPlainTextEdit = Utils.get_private_field(
            dialog, "translated_edit", QPlainTextEdit
        )
        dialog.set_string(editor.all_strings[0], 0)
        translated_edit.setPlainText("Geänderter Text")
        history.commit()

        # when
        dialog.set_string(editor.all_strings[1], 0)

        # then
        assert [revision.text for revision in history.revisions] == [
            translated_edit.toPlainText()
        ]

    def test_reset_is_undoable(self, editor_tab: EditorTab) -> None:
        """
        Tests that resetting the current string in the translator dialog can be undone.
        """

        # given
        editor: Editor = Utils.get_private_field(editor_tab, *TestEditorTab.EDITOR)
        dialog: TranslatorDialog = Utils.get_private_field(
            editor_tab, *TestEditorTab.DIALOG
        )
        translated_edit: QPlainTextEdit = Utils.get_private_field(
            dialog, "translated_edit", QPlainTextEdit
        )
        reset_button: QPushButton = Utils.get_private_field(
            dialog, "reset_button", QPushButton
        )
        string: EditorString = editor.all_strings[0]
        dialog.set_string(string, 0)
        dialog.text_changed.emit(string, "Geänderter Text", False)

        # when
        reset_button.click()

        # then
        assert translated_edit.toPlainText() != "Geänderter Text"

        # when
        translated_edit.undo()

        # then
        assert translated_edit.toPlainText() == "Geänderter Text"

    def test_close_tab(self, editor_tab: EditorTab) -> None:
        """
        Tests that an unmodified tab can be closed.
        """

        # when / then
        assert editor_tab.close_tab()
