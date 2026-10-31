"""
Copyright (c) Cutleast
"""

from pathlib import Path
from unittest.mock import MagicMock

from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict

from core.database.database import TranslationDatabase
from core.file_types.plugin.string import PluginString
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translation_context.builder import ContextBuilder
from core.translation_context.context import TranslationContext


class TestContextBuilder:
    """
    Tests `core.translation_context.builder.ContextBuilder`.
    """

    def test_context_is_found_after_editing_the_string(self) -> None:
        """
        Tests that the context of a string is still found after its translation was
        edited, which changes the hash of the string.
        """

        # given
        database = MagicMock(spec=TranslationDatabase)
        database.vanilla_translation.strings = {}
        database.user_translations = []
        string = PluginString(
            form_id="05000833|Test.esp", type="WEAP FULL", original="Elite Wolf Bow"
        )
        strings: dict[Path, StringList] = {Path("Test.esp"): [string]}
        contexts: ReferenceDict[String, TranslationContext] = ContextBuilder(
            database
        ).build_context(strings)

        # when
        string.string = "Elite-Wolfsbogen"
        string.status = StringStatus.TranslationComplete

        # then
        assert string in contexts
        assert contexts[string].mod_file_context.string_kind == "Weapon - Name"
