"""
Copyright (c) Cutleast
"""

from core.translation_provider.cdt_api.utils import (
    TimestampData,
    get_unix_timestamp_from_timestamp_data,
)

from ...core_test import CoreTest


class TestUtils(CoreTest):
    """
    Tests the utility methods from `core.translation_provider.cdt_api.utils`.
    """

    def test_get_timestamp_from_response_data(self) -> None:
        """
        Tests `core.translation_provider.cdt_api.ctd_api.CDTApi.get_timestamp_from_response_data()`.
        """

        # given
        response_data: dict[str, TimestampData] = {
            "LastArchiveUpdateDate": {
                "date": "2024-03-22 21:16:32.000000",
                "timezone_type": 3,
                "timezone": "Europe/Paris",
            }
        }
        expected_timestamp: int = 1711141652

        # when
        actual_timestamp: int = get_unix_timestamp_from_timestamp_data(
            response_data["LastArchiveUpdateDate"]
        )

        # then
        assert expected_timestamp == actual_timestamp
