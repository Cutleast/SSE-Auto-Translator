"""
Copyright (c) Cutleast
"""

from pathlib import Path
from unittest.mock import MagicMock

from core.config.translator_config import TranslatorConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.editor.editor import Editor
from core.editor.models import EditorString
from core.file_types.plugin.string import PluginString
from core.string.string_status import StringStatus
from core.translation_context.glossary import TranslationGlossary
from core.translator.service import TranslatorService
from core.utilities.game_language import GameLanguage


class TestEditor:
    """
    Tests `core.editor.editor.Editor`.
    """

    @staticmethod
    def __create_editor(tmp_path: Path) -> Editor:
        """
        Creates an editor for a translation with a name and a string containing it.

        Args:
            tmp_path (Path): Temporary directory used as user data path.

        Returns:
            Editor: The created editor with a built translation context.
        """

        database = MagicMock(spec=TranslationDatabase)
        database.vanilla_translation.strings = {}
        database.user_translations = []
        config = MagicMock(spec=TranslatorConfig)
        config.glossary = {}
        translation = MagicMock(spec=Translation)
        translation.strings = {
            Path("Test.esp"): [
                PluginString(
                    form_id="05000800|Test.esp",
                    type="CELL FULL",
                    original="Whiterun",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="05000801|Test.esp",
                    type="INFO NAM1",
                    original="Go to Whiterun.",
                    status=StringStatus.TranslationRequired,
                ),
            ]
        }

        editor = Editor(
            translation,
            GameLanguage.German,
            database,
            None,
            config,
            MagicMock(spec=TranslatorService),
            tmp_path,
        )
        editor.build_string_context()

        return editor

    @staticmethod
    def __get_mod_terms(string: EditorString) -> list[tuple[str, str]]:
        """
        Gets the glossary terms of a string that originate from the edited translation.

        Args:
            string (EditorString): The string to get the glossary terms of.

        Returns:
            list[tuple[str, str]]: The original and translated text of each term.
        """

        assert string.context is not None

        return [
            (term.original, term.translated)
            for term in string.context.glossary_terms
            if term.source == TranslationGlossary.TermSource.Mod
        ]

    def test_completing_name_refreshes_glossary_terms(self, tmp_path: Path) -> None:
        """
        Tests that completing a name translation adds the name to the glossary terms of
        strings containing it.
        """

        # given
        editor: Editor = TestEditor.__create_editor(tmp_path)
        name, text = editor.all_strings
        assert TestEditor.__get_mod_terms(text) == []

        # when
        editor.set_translated_text(name, "Weißlauf", sync_identical=False)
        editor.set_string_status(
            name, StringStatus.TranslationComplete, sync_identical=False
        )

        # then
        assert TestEditor.__get_mod_terms(text) == [("Whiterun", "Weißlauf")]

    def test_resetting_name_removes_glossary_term(self, tmp_path: Path) -> None:
        """
        Tests that resetting a completed name translation removes the name from the
        glossary terms of strings containing it.
        """

        # given
        editor: Editor = TestEditor.__create_editor(tmp_path)
        name, text = editor.all_strings
        editor.set_translated_text(name, "Weißlauf", sync_identical=False)
        editor.set_string_status(
            name, StringStatus.TranslationComplete, sync_identical=False
        )

        # when
        editor.reset_string(name, sync_identical=False)

        # then
        assert TestEditor.__get_mod_terms(text) == []
