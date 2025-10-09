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
        translation_timestamp: int, original_mod_timestamp: int
    ) -> int:
        """Stub for `NexusModsApi.__get_sort_key()`."""

        raise NotImplementedError

    TEST_SORT_KEY_DATA: list[tuple[int, int, int]] = [
        (0, 0, int(10e6)),
        (
            int(to_timestamp("01.10.2025 19:10")),
            int(to_timestamp("01.10.2025 18:00")),
            4_200,  # 1 hour and 10 minutes
        ),
    ]
    """Test data for `TestNexusModsApi.test_get_sort_key"""

    @pytest.mark.parametrize(
        "translation_timestamp, original_mod_timestamp, expected_output",
        TEST_SORT_KEY_DATA,
    )
    def test_get_sort_key(
        self,
        translation_timestamp: int,
        original_mod_timestamp: int,
        expected_output: int,
    ) -> None:
        """
        Tests `NexusModsApi.__get_sort_key()`.
        """

        # given
        method = Utils.get_private_method(
            NexusModsApi, TestNexusModsApi.GET_SORT_KEY, self.get_sort_key_stub
        )

        # when
        actual_result: int = method(translation_timestamp, original_mod_timestamp)

        # then
        assert actual_result == expected_output
