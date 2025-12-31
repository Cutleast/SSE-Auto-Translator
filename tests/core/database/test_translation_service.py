"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.database.translation_service import TranslationService
from core.file_types.plugin.string import PluginString
from core.string.string_loader import StringLoader
from core.string.string_status import StringStatus
from core.string.types import String, StringList

from ..core_test import CoreTest


class TestTranslationService(CoreTest):
    """
    Tests `core.database.translation_service.TranslationService`.
    """

    @staticmethod
    def provide_update_string_data() -> list[
        tuple[PluginString, StringList, PluginString]
    ]:
        """
        Provides test data for `test_update_string`.

        Returns:
            list[tuple[String, StringList, String]]: Test data.
        """

        test_data: list[tuple[PluginString, StringList, PluginString]] = []

        # test translation by form id
        string1a = PluginString(
            form_id="1",
            type="SPEL FULL",
            original="Original",
        )
        string1b = PluginString(
            form_id="1",
            type="SPEL FULL",
            original="Original",
            string="Translated",
        )
        string1c = PluginString(
            form_id="1",
            type="SPEL FULL",
            original="Original",
            string="Translated",
            status=StringStatus.TranslationComplete,
        )

        # test translation by original string
        string2a = PluginString(
            form_id="2",
            type="SPEL FULL",
            original="Original",
        )
        string2b = PluginString(
            form_id="a different form id",
            type="SPEL FULL",
            original="Original",
            string="Translated",
        )
        string2c = PluginString(
            form_id="2",
            type="SPEL FULL",
            original="Original",
            string="Translated",
            status=StringStatus.TranslationIncomplete,
        )

        # test that unmatched strings aren't altered
        string3a = PluginString(
            form_id="3",
            type="SPEL FULL",
            original="Original",
        )
        string3b = PluginString(
            form_id="a different form id",
            type="SPEL FULL",
            original="and a different original",
            string="Translated",
        )

        test_data.append((string1a, [string1b], string1c))
        test_data.append((string2a, [string2b], string2c))
        test_data.append((string3a, [string3b], string3a))

        return test_data

    @pytest.mark.parametrize(
        "string_to_update, existing_strings, expected_string",
        provide_update_string_data(),
    )
    def test_update_string(
        self,
        string_to_update: String,
        existing_strings: StringList,
        expected_string: String,
    ) -> None:
        """
        Tests `TranslationService.update_string()`.

        Args:
            string_to_update (String): String to update.
            existing_strings (StringList): Existing strings to use for translation.
            expected_string (String): Expected updated string.
        """

        # given
        input_hash: int = CoreTest.calc_unique_string_hash(string_to_update)
        expected_hash: int = CoreTest.calc_unique_string_hash(expected_string)
        existing_strings_by_id: dict[str, String] = {
            string.id: string for string in existing_strings
        }
        existing_strings_by_original: dict[str, String] = {
            string.original: string for string in existing_strings
        }

        # when
        updated: bool = TranslationService.update_string(
            string_to_update, existing_strings_by_id, existing_strings_by_original
        )
        actual_hash: int = CoreTest.calc_unique_string_hash(string_to_update)

        # then
        assert updated == (input_hash != expected_hash)
        assert actual_hash == expected_hash, (
            f"<{string_to_update}> and <{expected_string}> differ!"
        )

    def test_save_strings_to_json_file(self) -> None:
        """
        Tests `TranslationService.save_strings_to_json_file()`.
        """

        # given
        json_file_path: Path = self.tmp_folder() / "strings.json"
        strings: StringList = [
            PluginString(
                form_id="1",
                type="SPEL FULL",
                original="Original",
                string="Translated",
                index=0,
                editor_id="ObsidianSpell",
                status=StringStatus.TranslationComplete,
            )
        ]

        # when
        TranslationService.save_strings_to_json_file(json_file_path, strings)

        # then
        assert json_file_path.exists()
        assert json_file_path.read_text("utf8") == (
            '[{"original":"Original","string":"Translated",'
            '"status":"TranslationComplete","form_id":"1","type":"SPEL FULL",'
            '"index":0,"editor_id":"ObsidianSpell"}]'
        )

        # when
        reloaded_strings: StringList = StringLoader.load_strings_from_json_file(
            json_file_path
        )

        # then
        assert reloaded_strings == strings
