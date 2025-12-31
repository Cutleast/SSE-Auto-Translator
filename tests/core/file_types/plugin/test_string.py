"""
Copyright (c) Cutleast
"""

from typing import Any

import pytest
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from pydantic import ValidationError

from core.file_types.plugin.string import PluginString
from core.string.string_status import StringStatus


class TestPluginString:
    """
    Tests `core.file_types.plugin.string.PluginString`.
    """

    def test_from_string_data_complete(self) -> None:
        """
        Tests the deserialization of a valid string with a complete translation.
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
        string: PluginString = PluginString.model_validate(string_data, by_alias=True)

        # then
        assert string.editor_id == string_data["editor_id"]
        assert string.form_id == string_data["form_id"]
        assert string.index == string_data["index"]
        assert string.type == string_data["type"]
        assert string.original == string_data["original"]
        assert string.string == string_data["string"]
        assert string.status == StringStatus.TranslationComplete

    def test_to_string_data_complete(self) -> None:
        """
        Tests the serialization of a valid string with a complete translation.
        """

        # given
        string: PluginString = PluginString(
            editor_id="TestString",
            form_id="00123456|Skyrim.esm",
            index=None,
            type="BOOK FULL",
            original="The title of the book",
            string="Der Titel des Buchs",
            status=StringStatus.TranslationComplete,
        )

        # when
        string_data: dict[str, Any] = string.model_dump(by_alias=True)

        # then
        assert string_data["editor_id"] == string.editor_id
        assert string_data["form_id"] == string.form_id
        assert string_data["index"] == string.index
        assert string_data["type"] == string.type
        assert string_data["original"] == string.original
        assert string_data["string"] == string.string
        assert string_data["status"] == string.status.name

    def test_from_string_data_untranslated(self) -> None:
        """
        Tests the deserialization of a string without a translation.
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
        string: PluginString = PluginString.model_validate(
            string_data.copy(), by_alias=True
        )

        # then
        assert string.editor_id == string_data["editor_id"]
        assert string.form_id == string_data["form_id"]
        assert string.index == string_data["index"]
        assert string.type == string_data["type"]
        assert string.original == string_data["string"]
        assert string.string is None
        assert string.status == StringStatus.TranslationRequired

    def test_from_string_data_without_form_id(self) -> None:
        """
        Tests the deserialization of a string without a FormID.
        """

        # given
        string_data: dict[str, Any] = {
            "editor_id": "TestString",
            "index": None,
            "type": "BOOK FULL",
            "string": "The title of the book",
        }

        # when/then
        with pytest.raises(
            ValidationError,
            match="1 validation error for PluginString\nform_id\n  Field required",
        ):
            PluginString.model_validate(string_data, by_alias=True)

    test_id_cases: list[tuple[PluginString, str]] = [
        (
            PluginString(
                editor_id="TestString",
                form_id="00123456|Skyrim.esm",
                index=None,
                type="BOOK FULL",
                original="The title of the book",
                string="Der Titel des Buchs",
                status=StringStatus.TranslationComplete,
            ),
            "123456|skyrim.esm###TestString###BOOK FULL###None",
        ),
        (
            PluginString(
                form_id="00234567|Skyrim.esm",
                index=2,
                type="BOOK DESC",
                original="The content of the book",
                string="Der Inhalt des Buchs",
                status=StringStatus.TranslationComplete,
            ),
            "234567|skyrim.esm###None###BOOK DESC###2",
        ),
    ]

    @pytest.mark.parametrize("string, expected_output", test_id_cases)
    def test_id(self, string: PluginString, expected_output: str) -> None:
        """
        Tests `PluginString.id`-property.
        """

        # when
        real_output: str = string.id

        # then
        assert real_output == expected_output

    LOCALIZED_INFO_DATA: list[tuple[PluginString, str]] = [
        (
            PluginString(
                original="The title of the book",
                string="Der Titel des Buchs",
                status=StringStatus.TranslationComplete,
                form_id="00123456|Skyrim.esm",
                type="BOOK FULL",
                editor_id="TestString",
            ),
            "Form ID: 00123456|Skyrim.esm\nEditor ID: TestString\nType: BOOK FULL",
        ),
        (
            PluginString(
                original="The title of the book",
                string="Der Titel des Buchs",
                status=StringStatus.TranslationComplete,
                form_id="00123456|Skyrim.esm",
                type="BOOK FULL",
            ),
            "Form ID: 00123456|Skyrim.esm\nType: BOOK FULL",
        ),
        (
            PluginString(
                original="The title of the book",
                string="Der Titel des Buchs",
                status=StringStatus.TranslationComplete,
                form_id="00123456|Skyrim.esm",
                type="BOOK FULL",
                index=1,
            ),
            "Form ID: 00123456|Skyrim.esm\nType: BOOK FULL\nIndex: 1",
        ),
        (
            PluginString(
                original="The title of the book",
                string="Der Titel des Buchs",
                status=StringStatus.TranslationComplete,
                form_id="00123456|Skyrim.esm",
                type="BOOK FULL",
                index=1,
                editor_id="TestString",
            ),
            "Form ID: 00123456|Skyrim.esm\nEditor ID: TestString\nType: BOOK FULL\n"
            "Index: 1",
        ),
    ]

    @pytest.mark.parametrize("string, expected_output", LOCALIZED_INFO_DATA)
    def test_get_localized_info(
        self, string: PluginString, expected_output: str
    ) -> None:
        """
        Tests `PluginString.get_localized_info()`.
        """

        # when
        real_output: str = string.get_localized_info()

        # then
        assert real_output == expected_output

    def test_in_referencedict(self) -> None:
        """
        Tests hashing and indexing of strings in
        `core.utilities.container_utils.ReferenceDict`.
        """

        # given
        string1: PluginString = PluginString(
            editor_id="TestString",
            form_id="00123456|Skyrim.esm",
            index=None,
            type="BOOK FULL",
            original="The title of the book",
            string="Der Titel des Buchs",
            status=StringStatus.TranslationComplete,
        )
        test_dict: ReferenceDict[PluginString, str] = ReferenceDict({string1: "test"})

        # when
        string1.string = "The title of the book"
        string1.status = StringStatus.TranslationRequired

        # then
        assert test_dict[string1] == "test"
