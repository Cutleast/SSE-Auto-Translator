"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.test.utils import Utils
from PySide6.QtWidgets import QLineEdit, QPushButton
from pytestqt.qtbot import QtBot

from tests.base_test import BaseTest
from ui.settings.glossary_term import GlossaryTerm
from ui.settings.glossary_term_dialog import GlossaryTermDialog


class TestGlossaryTermDialog(BaseTest):
    """
    Tests `ui.settings.glossary_term_dialog.GlossaryTermDialog`.
    """

    ORIGINAL_ENTRY: tuple[str, type[QLineEdit]] = "original_entry", QLineEdit
    TRANSLATION_ENTRY: tuple[str, type[QLineEdit]] = "translation_entry", QLineEdit
    OK_BUTTON: tuple[str, type[QPushButton]] = "ok_button", QPushButton

    def test_ok_requires_original_and_translation(self, qtbot: QtBot) -> None:
        """
        Tests that the ok button is only enabled if both fields are filled and that the
        entered values are stripped.
        """

        # given
        dialog = GlossaryTermDialog(None)
        qtbot.addWidget(dialog)
        original_entry: QLineEdit = Utils.get_private_field(
            dialog, *TestGlossaryTermDialog.ORIGINAL_ENTRY
        )
        translation_entry: QLineEdit = Utils.get_private_field(
            dialog, *TestGlossaryTermDialog.TRANSLATION_ENTRY
        )
        ok_button: QPushButton = Utils.get_private_field(
            dialog, *TestGlossaryTermDialog.OK_BUTTON
        )

        # when
        original_entry.setText(" hold ")
        enabled_without_translation: bool = ok_button.isEnabled()
        translation_entry.setText(" Fürstentum ")

        # then
        assert not enabled_without_translation
        assert ok_button.isEnabled()
        assert (dialog.original, dialog.translation) == ("hold", "Fürstentum")

    def test_edit_prefills_term(self, qtbot: QtBot) -> None:
        """
        Tests that editing a term prefills the fields with its values.
        """

        # when
        dialog = GlossaryTermDialog(
            None, GlossaryTerm(original="hold", translation="Fürstentum")
        )
        qtbot.addWidget(dialog)

        # then
        assert (dialog.original, dialog.translation) == ("hold", "Fürstentum")
        assert dialog.windowTitle() == "Edit glossary term"
