"""
Copyright (c) Cutleast
"""

from typing import Any

import pytest

from core.translation_provider.cdt_api.ctd_api import CDTApi

from ...core_test import CoreTest


class TestCDTApi(CoreTest):
    """
    Tests `core.translation_provider.cdt_api.ctd_api.CDTApi`.
    """

    def test_get_cdt_id_from_url(self) -> None:
        """
        Tests `core.translation_provider.cdt_api.ctd_api.CDTApi.get_cdt_id_from_url()`.
        """

        # given
        test_url: str = "https://www.confrerie-des-traducteurs.fr/skyrim/mods/1234"
        expected_id: int = 1234

        # when
        actual_id: int = CDTApi.get_cdt_id_from_url(test_url)

        # then
        assert expected_id == actual_id

    invalid_urls: list[str] = [
        "https://www.confrerie-des-traducteurs.fr/skyrim/telechargement_se/",
        "https://www.confrerie-des-traducteurs.fr/skyrim/mods/",
        "https://test.com/skyrim/mods/1234",
        "",
    ]

    @pytest.mark.parametrize("url", invalid_urls)
    def test_get_cdt_id_from_url_with_invalid_url(self, url: str) -> None:
        """
        Tests `core.translation_provider.cdt_api.ctd_api.CDTApi.get_cdt_id_from_url()`
        with invalid urls.
        """

        with pytest.raises(ValueError, match="Could not extract CDT id from"):
            CDTApi.get_cdt_id_from_url(url)

    def test_get_timestamp_from_response_data(self) -> None:
        """
        Tests `core.translation_provider.cdt_api.ctd_api.CDTApi.get_timestamp_from_response_data()`.
        """

        # given
        response_data: dict[str, Any] = {
            "LastArchiveUpdateDate": {
                "date": "2024-03-22 21:16:32.000000",
                "timezone_type": 3,
                "timezone": "Europe/Paris",
            }
        }
        expected_timestamp: int = 1711141652

        # when
        actual_timestamp: int = CDTApi.get_timestamp_from_response_data(response_data)

        # then
        assert expected_timestamp == actual_timestamp
