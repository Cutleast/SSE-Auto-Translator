"""
Copyright (c) Cutleast
"""

import os
import sys
from typing import Any

import pytest

sys.path.append(os.path.join(os.getcwd(), "src"))

from core.database.string import String
from core.utilities.container_utils import ReferenceDict


class TestString:
    """
    Tests `core.database.string.String`.
    """

    def test_from_string_data_complete(self) -> None:
        """
        Tests `core.database.string.String.from_string_data()` on a valid string
        data dict with a complete translation.
        """

        # given
        string_data: dict[str, Any] = {
            "editor_id": "TestString",
            "form_id": "00123456|Skyrim.esm",
            "index": None,
            "type": "BOOK FULL",
            "original": "The title of the book",
            "string": "Der Titel des Buchs",
            "status": "TranslationComplete",
        }

        # when
        string: String = String.from_string_data(string_data)

        # then
        assert string.editor_id == string_data["editor_id"]
        assert string.form_id == string_data["form_id"]
        assert string.index == string_data["index"]
        assert string.type == string_data["type"]
        assert string.original_string == string_data["original"]
        assert string.translated_string == string_data["string"]
        assert string.status == String.Status.TranslationComplete

    def test_to_string_data_complete(self) -> None:
        """
        Tests `core.database.string.String.to_string_data()` on a valid string with a
        complete translation.
        """

        # given
        string: String = String(
            editor_id="TestString",
            form_id="00123456|Skyrim.esm",
            index=None,
            type="BOOK FULL",
            original_string="The title of the book",
            translated_string="Der Titel des Buchs",
            status=String.Status.TranslationComplete,
        )

        # when
        string_data: dict[str, Any] = string.to_string_data()

        # then
        assert string_data["editor_id"] == string.editor_id
        assert string_data["form_id"] == string.form_id
        assert string_data["index"] == string.index
        assert string_data["type"] == string.type
        assert string_data["original"] == string.original_string
        assert string_data["string"] == string.translated_string
        assert string_data["status"] == string.status.name

    def test_from_string_data_untranslated(self) -> None:
        """
        Tests `core.database.string.String.from_string_data()` on a valid string
        data dict without a translation.
        """

        # given
        string_data: dict[str, Any] = {
            "editor_id": "TestString",
            "form_id": "00123456|Skyrim.esm",
            "index": None,
            "type": "BOOK FULL",
            "string": "The title of the book",
        }

        # when
        string: String = String.from_string_data(string_data)

        # then
        assert string.editor_id == string_data["editor_id"]
        assert string.form_id == string_data["form_id"]
        assert string.index == string_data["index"]
        assert string.type == string_data["type"]
        assert string.original_string == string_data["string"]
        assert string.translated_string is None
        assert string.status == String.Status.TranslationRequired

    def test_from_string_data_without_form_id(self) -> None:
        """
        Tests `core.database.string.String.from_string_data()` on an invalid string
        without a `form_id`.
        """

        # given
        string_data: dict[str, Any] = {
            "editor_id": "TestString",
            "index": None,
            "type": "BOOK FULL",
            "string": "The title of the book",
        }

        # when/then
        with pytest.raises(ValueError, match="String data has no FormID!"):
            String.from_string_data(string_data)

    test_id_cases: list[tuple[String, str]] = [
        (
            String(
                editor_id="TestString",
                form_id="00123456|Skyrim.esm",
                index=None,
                type="BOOK FULL",
                original_string="The title of the book",
                translated_string="Der Titel des Buchs",
                status=String.Status.TranslationComplete,
            ),
            "123456|skyrim.esm###TestString###BOOK FULL###None",
        ),
        (
            String(
                form_id="00234567|Skyrim.esm",
                index=2,
                type="BOOK DESC",
                original_string="The content of the book",
                translated_string="Der Inhalt des Buchs",
                status=String.Status.TranslationComplete,
            ),
            "234567|skyrim.esm###None###BOOK DESC###2",
        ),
    ]

    @pytest.mark.parametrize("string, expected_output", test_id_cases)
    def test_id(self, string: String, expected_output: str) -> None:
        """
        Tests `core.database.string.String.id`-property.
        """

        # when
        real_output: str = string.id

        # then
        assert real_output == expected_output

    def test_in_referencedict(self) -> None:
        """
        Tests hashing and indexing of strings in
        `core.utilities.container_utils.ReferenceDict`.
        """

        # given
        string1: String = String(
            editor_id="TestString",
            form_id="00123456|Skyrim.esm",
            index=None,
            type="BOOK FULL",
            original_string="The title of the book",
            translated_string="Der Titel des Buchs",
            status=String.Status.TranslationComplete,
        )
        test_dict: ReferenceDict[String, str] = ReferenceDict({string1: "test"})

        # when
        string1.translated_string = "The title of the book"
        string1.status = String.Status.TranslationRequired

        # then
        assert test_dict[string1] == "test"
