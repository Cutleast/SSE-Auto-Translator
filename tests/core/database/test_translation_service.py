"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.database.translation_service import TranslationService
from core.string.string import String

from ..core_test import CoreTest


class TestTranslationService(CoreTest):
    """
    Tests `core.database.translation_service.TranslationService`.
    """

    def test_load_strings_from_legacy_file(self) -> None:
        """
        Tests the deserialization and loading of strings from a legacy .ats file.
        """

        # given
        legacy_ats_file_path: Path = (
            self.data_path()
            / "translations"
            / "Obsidian Weathers and Seasons - German"
            / "obsidian weathers.esp.ats"
        )
        expected_strings: list[String] = [
            String(
                form_id="04000D65|Obsidian Weathers.esp",
                type="SPEL FULL",
                original="Options: Obsidian Weathers",
                string="Optionen: Obsidian-Wetter",
                editor_id="ObsidianSpell",
                status=String.Status.TranslationComplete,
            ),
            String(
                form_id="04000D62|Obsidian Weathers.esp",
                type="MESG ITXT",
                original="Default",
                string="Standard",
                index=0,
                editor_id="ObsidianMessage",
                status=String.Status.TranslationComplete,
            ),
        ]

        # when
        actual_strings: list[String] = TranslationService.load_strings_from_legacy_file(
            legacy_ats_file_path
        )

        # then
        assert len(actual_strings) == 29
        actual_hashes: list[int] = [
            CoreTest.calc_unique_string_hash(string) for string in actual_strings
        ]
        for string in expected_strings:
            assert CoreTest.calc_unique_string_hash(string) in actual_hashes, (
                f"{string} is missing!"
            )

    def test_load_strings_from_json_file(self) -> None:
        """
        Tests the deserialization and loading of strings from a JSON file.
        """

        # given
        json_file_path: Path = (
            self.data_path()
            / "translations"
            / "Obsidian Weathers and Seasons - German"
            / "obsidian weathers.esp.json"
        )
        expected_strings: list[String] = [
            String(
                form_id="04000D65|Obsidian Weathers.esp",
                type="SPEL FULL",
                original="Options: Obsidian Weathers",
                string="Optionen: Obsidian-Wetter",
                editor_id="ObsidianSpell",
                status=String.Status.TranslationComplete,
            ),
            String(
                form_id="04000D62|Obsidian Weathers.esp",
                type="MESG ITXT",
                original="Default",
                string="Standard",
                index=0,
                editor_id="ObsidianMessage",
                status=String.Status.TranslationComplete,
            ),
        ]

        # when
        actual_strings: list[String] = TranslationService.load_strings_from_json_file(
            json_file_path
        )

        # then
        assert len(actual_strings) == 29
        actual_hashes: list[int] = [
            CoreTest.calc_unique_string_hash(string) for string in actual_strings
        ]
        for string in expected_strings:
            assert CoreTest.calc_unique_string_hash(string) in actual_hashes, (
                f"{string} is missing!"
            )

    @staticmethod
    def provide_update_string_data() -> list[tuple[String, list[String], String]]:
        """
        Provides test data for `test_update_string`.

        Returns:
            list[tuple[String, list[String], String]]: Test data.
        """

        test_data: list[tuple[String, list[String], String]] = []

        # test translation by form id
        string1a = String(
            form_id="1",
            type="SPEL FULL",
            original="Original",
        )
        string1b = String(
            form_id="1",
            type="SPEL FULL",
            original="Original",
            string="Translated",
        )
        string1c = String(
            form_id="1",
            type="SPEL FULL",
            original="Original",
            string="Translated",
            status=String.Status.TranslationComplete,
        )

        # test translation by original string
        string2a = String(
            form_id="2",
            type="SPEL FULL",
            original="Original",
        )
        string2b = String(
            form_id="a different form id",
            type="SPEL FULL",
            original="Original",
            string="Translated",
        )
        string2c = String(
            form_id="2",
            type="SPEL FULL",
            original="Original",
            string="Translated",
            status=String.Status.TranslationIncomplete,
        )

        # test that unmatched strings aren't altered
        string3a = String(
            form_id="3",
            type="SPEL FULL",
            original="Original",
        )
        string3b = String(
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
        existing_strings: list[String],
        expected_string: String,
    ) -> None:
        """
        Tests `TranslationService.update_string()`.

        Args:
            string_to_update (String): String to update.
            existing_strings (list[String]): Existing strings to use for translation.
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
        strings: list[String] = [
            String(
                form_id="1",
                type="SPEL FULL",
                original="Original",
                string="Translated",
                index=0,
                editor_id="ObsidianSpell",
                status=String.Status.TranslationComplete,
            )
        ]

        # when
        TranslationService.save_strings_to_json_file(json_file_path, strings)

        # then
        assert json_file_path.exists()
        assert json_file_path.read_text("utf8") == (
            '[{"form_id":"1","type":"SPEL FULL","original":"Original",'
            '"string":"Translated","index":0,"editor_id":"ObsidianSpell",'
            '"status":"TranslationComplete"}]'
        )

        # when
        reloaded_strings: list[String] = TranslationService.load_strings_from_json_file(
            json_file_path
        )

        # then
        assert reloaded_strings == strings
