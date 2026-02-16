"""
Copyright (c) Cutleast
"""

from typing import Any

import pytest

from core.translation_provider.cdt_api.ctd_api import CDTApi
from core.translation_provider.cdt_api.models.cdt_translation import CdtTranslation

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

    def test_deserialize_response_data(self) -> None:
        """
        Tests the deserialization of the response data returned by the CDT API.
        """

        # given
        response_data: dict[str, Any] = {
            "NexusModId": 49616,
            "FrenchName": "USMP - Compilation de correctifs",
            "Version": "2.6.7",
            "Filename": "usmp___compilation_de_correctifs_2.6.7_sse.7z",
            "DownloadLink": "https://www.confrerie-des-traducteurs.fr/skyrim/telechargement-se/3425?fromSseAtAPI=1",
            "LastArchiveUpdateDate": {
                "date": "2026-01-08 14:46:05.000000",
                "timezone_type": 3,
                "timezone": "Europe/Paris",
            },
        }

        # when
        actual_translation: CdtTranslation = CdtTranslation.model_validate(
            response_data, by_alias=True
        )

        # then
        assert actual_translation.nexus_mods_id == 49616
        assert actual_translation.name == "USMP - Compilation de correctifs"
        assert actual_translation.version == "2.6.7"
        assert (
            actual_translation.file_name
            == "usmp___compilation_de_correctifs_2.6.7_sse.7z"
        )
        assert (
            actual_translation.download_link
            == "https://www.confrerie-des-traducteurs.fr/skyrim/telechargement-se/3425?fromSseAtAPI=1"
        )
        assert actual_translation.timestamp == 1767883025
