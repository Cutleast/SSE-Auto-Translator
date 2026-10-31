"""
Copyright (c) Cutleast
"""

from pathlib import Path

from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict

from core.file_types.interface.file import InterfaceFile
from core.file_types.interface.string import InterfaceString
from core.mod_file.context import ModFileContext
from core.string.types import String, StringList


class TestInterfaceFile:
    """
    Tests `core.file_types.interface.file.InterfaceFile`.
    """

    def test_get_string_contexts(self) -> None:
        """
        Tests that the context of an interface string contains its adjacent entries.
        """

        # given
        mod_file_path = Path("interface") / "translations" / "test_english.txt"
        strings: StringList = [
            InterfaceString(mcm_id=f"$Test_{index}", original=f"Entry {index}")
            for index in range(6)
        ]

        # when
        contexts: ReferenceDict[String, ModFileContext] = (
            InterfaceFile.get_string_contexts(
                mod_file_path, strings, {mod_file_path: strings}
            )
        )

        # then
        first_context: ModFileContext = contexts[strings[0]]
        middle_context: ModFileContext = contexts[strings[3]]
        assert [related.string for related in first_context.related_strings] == [
            strings[1],
            strings[2],
        ]
        assert [related.string for related in middle_context.related_strings] == [
            strings[1],
            strings[2],
            strings[4],
            strings[5],
        ]
        assert all(
            related.mod_file == mod_file_path
            for related in middle_context.related_strings
        )
