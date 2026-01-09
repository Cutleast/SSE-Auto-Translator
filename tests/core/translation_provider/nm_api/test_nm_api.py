"""
Copyright (c) Cutleast
"""

import pytest
from cutleast_core_lib.core.utilities.datetime import to_timestamp
from cutleast_core_lib.test.utils import Utils

from core.translation_provider.provider_manager import NexusModsApi
from tests.core.core_test import CoreTest


class TestNexusModsApi(CoreTest):
    """
    Tests `core.translation_provider.nm_api.NexusModsApi`.
    """

    GET_SORT_KEY: str = "get_sort_key"
    """Identifier for accessing the private method `NexusModsApi.__get_sort_key()`."""

    @staticmethod
    def get_sort_key_stub(
        translation_timestamp: int,
        translation_version: str,
        original_mod_timestamp: int,
        original_mod_version: str,
    ) -> tuple[bool, bool, int]:
        """Stub for `NexusModsApi.__get_sort_key()`."""

        raise NotImplementedError

    TEST_SORT_KEY_DATA: list[tuple[int, str, int, str, tuple[bool, bool, int]]] = [
        (0, "", 0, "", (False, False, 0)),
        (
            int(to_timestamp("01.10.2025 19:10")),
            "1.1-DV1.0",
            int(to_timestamp("01.10.2025 18:00")),
            "v1.1",
            (
                True,  # translation version starts with original mod version
                True,  # translation_timestamp > original_mod_timestamp
                1759338600,  # translation_timestamp
            ),
        ),
    ]
    """Test data for `TestNexusModsApi.test_get_sort_key"""

    @pytest.mark.parametrize(
        "translation_timestamp, translation_version, original_mod_timestamp, original_mod_version, expected_output",
        TEST_SORT_KEY_DATA,
    )
    def test_get_sort_key(
        self,
        translation_timestamp: int,
        translation_version: str,
        original_mod_timestamp: int,
        original_mod_version: str,
        expected_output: tuple[bool, int],
    ) -> None:
        """
        Tests `NexusModsApi.__get_sort_key()`.
        """

        # given
        method = Utils.get_private_method(
            NexusModsApi, TestNexusModsApi.GET_SORT_KEY, self.get_sort_key_stub
        )

        # when
        actual_result: tuple[bool, bool, int] = method(
            translation_timestamp,
            translation_version,
            original_mod_timestamp,
            original_mod_version,
        )

        # then
        assert actual_result == expected_output
