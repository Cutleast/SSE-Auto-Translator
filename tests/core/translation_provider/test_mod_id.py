"""
Copyright (c) Cutleast
"""

from typing import Any

import pytest
from pydantic import TypeAdapter

from core.translation_provider.cdt_api.cdt_id import CdtModId
from core.translation_provider.mod_id import ModId
from core.translation_provider.nm_api.nxm_id import NxmModId
from tests.core.core_test import CoreTest

ModIdAdapter = TypeAdapter(ModId)


class TestModId(CoreTest):
    """
    Tests `core.translation_provider.mod_id.ModId`.
    """

    TEST_DATA: list[tuple[dict[str, Any], ModId]] = [
        (
            {
                "installation_file_name": "Alternate Start - Live Another Life-272-4-2-1-1702620391.7z",
                "source": "NexusMods",
                "mod_id": 272,
                "file_id": 452003,
            },
            NxmModId(
                mod_id=272,
                file_id=452003,
                installation_file_name="Alternate Start - Live Another Life-272-4-2-1-1702620391.7z",
            ),
        ),
        (
            {
                "installation_file_name": "vivez_une_nouvelle_vie_4.2.5_sse.7z",
                "source": "Confrérie des Traducteurs",
                "mod_id": 587,
                "nm_mod_id": 272,
            },
            CdtModId(
                installation_file_name="vivez_une_nouvelle_vie_4.2.5_sse.7z",
                mod_id=587,
                nm_mod_id=272,
            ),
        ),
    ]

    @pytest.mark.parametrize("json_data, expected_mod_id", TEST_DATA)
    def test_deserialize_by_discriminator(
        self, json_data: dict[str, Any], expected_mod_id: ModId
    ) -> None:
        """
        Tests the deserialization of mod ids based on their source.

        Args:
            json_data (dict[str, Any]): JSON data.
            expected_mod_id (ModId): Expected mod id.
        """

        # when
        actual_mod_id: ModId = ModIdAdapter.validate_python(json_data)

        # then
        assert actual_mod_id == expected_mod_id

    @pytest.mark.parametrize("expected_json_data, mod_id", TEST_DATA)
    def test_serialize(self, expected_json_data: dict[str, Any], mod_id: ModId) -> None:
        """
        Tests the serialization of mod ids.

        Args:
            expected_json_data (dict[str, Any]): Expected JSON data.
            mod_id (ModId): Mod id.
        """

        # when
        actual_json_data: dict[str, Any] = ModIdAdapter.dump_python(
            mod_id, mode="json", exclude_defaults=True
        )

        # then
        assert actual_json_data == expected_json_data
