"""
Copyright (c) Cutleast
"""

import pytest

from core.translation_provider.nm_api.nxm_request import NxmRequest
from tests.core.core_test import CoreTest


class TestNxmRequest(CoreTest):
    """
    Tests `core.translation_provider.nm_api.nxm_request.NxmRequest`.
    """

    def test_from_url(self) -> None:
        """
        Tests parsing a valid NXM download URL.
        """

        # given
        url: str = (
            "nxm://skyrimspecialedition/mods/123/files/456?key=test-key&expires=1"
            "&user_id=2"
        )

        # when
        request: NxmRequest = NxmRequest.from_url(url)

        # then
        assert request.game == "skyrimspecialedition"
        assert request.mod_id == 123
        assert request.file_id == 456
        assert request.key == "test-key"

    @pytest.mark.parametrize(
        "url",
        [
            "https://skyrimspecialedition/mods/123/files/456?key=test&expires=1&user_id=2",
            "nxm://skyrimspecialedition/mods/a/files/456?key=test&expires=1&user_id=2",
            "nxm://skyrimspecialedition/mods/123/files/456?expires=1&user_id=2",
            "nxm://skyrimspecialedition/files/456?key=test&expires=1&user_id=2",
        ],
    )
    def test_from_url_with_invalid_url(self, url: str) -> None:
        """
        Tests rejecting an invalid NXM download URL.
        """

        # when / then
        with pytest.raises(ValueError):
            NxmRequest.from_url(url)
