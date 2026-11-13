"""
Copyright (c) Cutleast
"""

import re
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest

from core.config.translator_config import TranslatorConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.database.translation_service import TranslationService
from core.editor.editor import Editor
from core.editor.models.diagnostics import TranslationDiagnostics
from core.editor.models.editor_string import EditorString
from core.file_types.plugin.string import PluginString
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.string.string_status import StringStatus
from core.string.types import StringList
from core.translation_context.glossary import TranslationGlossary
from core.translator.service import TranslatorService
from core.utilities.game_language import GameLanguage
from tests.base_test import BaseTest
from tests.setup.data_factory import DataFactory
from tests.setup.paths import DICTIONARY_PATH


class TestEditor(BaseTest):
    """
    Tests `core.editor.editor.Editor` with a translation from the test database.
    """

    TRANSLATION_NAME: str = "Wet and Cold SE - German"
    """The name of the edited test translation."""

    MOD_FILE_PATH: Path = Path("WetandCold.esp")
    """The mod file of the edited test translation."""

    @pytest.fixture
    def translation(self, tmp_path: Path) -> Translation:
        """
        Returns the edited test translation, stored in the temporary folder.

        Args:
            tmp_path (Path): The temporary folder of the test.

        Returns:
            Translation: The test translation.
        """

        return DataFactory.stored_translation(TestEditor.TRANSLATION_NAME, tmp_path)

    @pytest.fixture
    def editor(self, translation: Translation, tmp_path: Path) -> Editor:
        """
        Creates an editor for the test translation with a database that contains only
        this translation and a mod instance with the original mod.

        Args:
            translation (Translation): The edited test translation.
            tmp_path (Path): The temporary folder of the test.

        Returns:
            Editor: The editor.
        """

        original_mod: Mod = DataFactory.instance_mod("Wet and Cold SE")
        for modfile in original_mod.modfiles:
            modfile.status = TranslationStatus.TranslationInstalled

        return Editor(
            translation,
            GameLanguage.German,
            DataFactory.database(tmp_path, [translation]),
            DataFactory.mod_instance([original_mod]),
            TranslatorConfig(),
            MagicMock(spec=TranslatorService),
            tmp_path / "user",
            DICTIONARY_PATH,
        )

    @staticmethod
    def get_strings(editor: Editor, original: str) -> list[EditorString]:
        """
        Gets all editor strings with the specified original text.

        Args:
            editor (Editor): The editor.
            original (str): The original text.

        Returns:
            list[EditorString]: The matching editor strings.
        """

        return [s for s in editor.all_strings if s.string.original == original]

    def test_initial_state(self, editor: Editor, translation: Translation) -> None:
        """
        Tests that the editor contains copies of all strings of the translation.
        """

        # when
        summary: dict[StringStatus, int] = editor.get_string_states_summary()

        # then
        assert not editor.changes_pending
        assert list(editor.strings) == [TestEditor.MOD_FILE_PATH]
        assert summary[StringStatus.TranslationComplete] == 204
        assert all(
            editor_string.string is not original_string
            for editor_string, original_string in zip(
                editor.all_strings, translation.strings[TestEditor.MOD_FILE_PATH]
            )
        )

    def test_completed_string_is_synchronized_to_identical_strings(
        self, editor: Editor
    ) -> None:
        """
        Tests that editing a string with synchronization applies the translation and
        status to all identical strings.
        """

        # given
        hoods: list[EditorString] = TestEditor.get_strings(editor, "Hood")
        editor.reset_strings(hoods)
        changed_strings: list[list[EditorString]] = []
        editor.strings_changed.connect(changed_strings.append)

        # when
        editor.set_translated_text(hoods[0], "Kapuze", sync_identical=True)
        editor.set_string_status(
            hoods[0], StringStatus.TranslationComplete, sync_identical=True
        )

        # then
        assert len(hoods) == 4
        assert editor.changes_pending
        assert [s.string.string for s in hoods] == ["Kapuze"] * 4
        assert all(s.string.status == StringStatus.TranslationComplete for s in hoods)
        assert len(changed_strings[-1]) >= 4

    def test_edit_without_sync_only_changes_edited_string(self, editor: Editor) -> None:
        """
        Tests that strings with the same original text stay untouched if identical
        strings are not synchronized.
        """

        # given
        hoods: list[EditorString] = TestEditor.get_strings(editor, "Hood")
        editor.reset_strings(hoods)

        # when
        editor.set_translated_text(hoods[0], "Kapuze", sync_identical=False)

        # then
        assert hoods[0].string.string == "Kapuze"
        assert all(s.string.string is None for s in hoods[1:])

    def test_apply_database_restores_reset_strings(self, editor: Editor) -> None:
        """
        Tests that reset strings get their translation back from the database.
        """

        # given
        hoods: list[EditorString] = TestEditor.get_strings(editor, "Hood")
        editor.reset_strings(hoods)

        # when
        modified_count: int = editor.apply_database(hoods)

        # then
        assert modified_count == 4
        assert all(s.string.string is not None for s in hoods)
        assert all(s.string.status == StringStatus.TranslationComplete for s in hoods)

    def test_apply_regex(self, editor: Editor) -> None:
        """
        Tests that a regex is applied to the translations of the specified strings.
        """

        # given
        hoods: list[EditorString] = TestEditor.get_strings(editor, "Hood")
        untouched_strings: list[EditorString] = TestEditor.get_strings(
            editor, "Strong Winds"
        )
        pattern: re.Pattern[str] = re.compile(r"^.*$")

        # when
        modified_count: int = editor.apply_regex(hoods, "Kapuze (neu)", pattern)

        # then
        assert modified_count == 4
        assert all(s.string.string == "Kapuze (neu)" for s in hoods)
        assert all(s.string.status == StringStatus.TranslationIncomplete for s in hoods)
        assert all(
            s.string.status == StringStatus.TranslationComplete
            for s in untouched_strings
        )

    def test_diagnostics_report_missing_placeholder(self, editor: Editor) -> None:
        """
        Tests that the diagnostics of an incomplete string are updated when its
        translation changes.
        """

        # given
        string: EditorString = TestEditor.get_strings(
            editor, "Carrying capacity increased by <mag> points."
        )[0]
        editor.set_status([string], StringStatus.TranslationIncomplete)
        editor.get_string_context(string)

        # when
        editor.set_translated_text(
            string, "Die Tragfähigkeit wird erhöht.", sync_identical=False
        )
        diagnostics: Optional[TranslationDiagnostics] = editor.get_string_diagnostics(
            string
        )

        # then
        assert diagnostics is not None
        assert diagnostics.missing_placeholders == {"<mag>": 1}

        # when
        editor.set_translated_text(
            string, "Die Tragfähigkeit wird um <mag> erhöht.", sync_identical=False
        )
        diagnostics = editor.get_string_diagnostics(string)

        # then
        assert diagnostics is not None
        assert diagnostics.missing_placeholders == {}

    def test_initialize_builds_contexts_and_diagnostics(self, editor: Editor) -> None:
        """
        Tests that initializing the editor builds the context of all strings and runs
        the diagnostics on incomplete strings only.
        """

        # given
        incomplete_string: EditorString = TestEditor.get_strings(
            editor, "Carrying capacity increased by <mag> points."
        )[0]
        editor.set_translated_text(
            incomplete_string, "Die Tragfähigkeit steigt.", sync_identical=False
        )
        editor.set_status([incomplete_string], StringStatus.TranslationIncomplete)

        # when
        editor.initialize()

        # then
        assert all(s.context is not None for s in editor.all_strings)
        assert incomplete_string.diagnostics is not None
        assert incomplete_string.diagnostics.missing_placeholders == {"<mag>": 1}
        assert all(
            s.diagnostics is None
            for s in editor.all_strings
            if s is not incomplete_string
        )

    def test_save_persists_changes(
        self, editor: Editor, translation: Translation
    ) -> None:
        """
        Tests that saving writes the edited strings to the translation's files.
        """

        # given
        hoods: list[EditorString] = TestEditor.get_strings(editor, "Hood")
        editor.reset_strings(hoods)
        editor.set_translated_text(hoods[0], "Kapuze", sync_identical=True)
        editor.set_string_status(
            hoods[0], StringStatus.TranslationComplete, sync_identical=True
        )

        # when
        editor.save()

        # then
        assert not editor.changes_pending
        saved_strings: dict[Path, StringList] = (
            TranslationService.load_translation_strings(translation.path)
        )
        saved_hoods: StringList = [
            s for s in saved_strings[TestEditor.MOD_FILE_PATH] if s.original == "Hood"
        ]
        assert [s.string for s in saved_hoods] == ["Kapuze"] * 4

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
            DICTIONARY_PATH,
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
