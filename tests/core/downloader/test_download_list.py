"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any

import pytest

from core.downloader.download_list import DownloadListItem
from core.downloader.file_download import FileDownload
from core.downloader.mod_info import ModInfo
from core.translation_provider.cdt_api.cdt_id import CdtModId
from core.translation_provider.mod_details import ModDetails
from core.translation_provider.nm_api.nxm_id import NxmModId
from core.translation_provider.source import Source
from tests.core.core_test import CoreTest


class TestDownloadList(CoreTest):
    """
    Tests `core.downloader.download_list.DownloadList`.
    """

    TEST_DATA: list[tuple[dict[str, Any], DownloadListItem]] = [
        (
            {
                "mod": {
                    "display_name": "Alternate Start - Live Another Life - SSE [4.2.1]",
                    "mod_id": {
                        "installation_file_name": "Alternate Start - Live Another Life-272-4-2-1-1702620391.7z",
                        "source": "NexusMods",
                        "mod_id": 272,
                        "file_id": 452003,
                        "nm_game_id": "skyrimspecialedition",
                    },
                    "source": "NexusMods",
                },
                "mod_file": "Alternate Start - Live Another Life.esp",
                "translation": {
                    "display_name": "Vivez une nouvelle vie",
                    "mod_id": {
                        "installation_file_name": "vivez_une_nouvelle_vie_4.2.5_sse.7z",
                        "source": "Confrérie des Traducteurs",
                        "mod_id": 587,
                        "nm_mod_id": 272,
                    },
                    "source": "Confrérie des Traducteurs",
                },
                "download": {
                    "mod_details": {
                        "display_name": "Vivez une nouvelle vie",
                        "file_name": "vivez_une_nouvelle_vie_4.2.5_sse.7z",
                        "mod_id": {
                            "installation_file_name": "vivez_une_nouvelle_vie_4.2.5_sse.7z",
                            "source": "Confrérie des Traducteurs",
                            "mod_id": 587,
                            "nm_mod_id": 272,
                        },
                        "version": "4.2.5",
                        "timestamp": 1751557708,
                        "author": None,
                        "uploader": None,
                        "modpage_url": "https://www.confrerie-des-traducteurs.fr/skyrim/mods/587",
                    },
                    "source": "Confrérie des Traducteurs",
                    "stale": False,
                },
            },
            DownloadListItem(
                mod=ModInfo(
                    display_name="Alternate Start - Live Another Life - SSE [4.2.1]",
                    mod_id=NxmModId(
                        installation_file_name="Alternate Start - Live Another Life-272-4-2-1-1702620391.7z",
                        mod_id=272,
                        file_id=452003,
                        nm_game_id="skyrimspecialedition",
                    ),
                    source=Source.NexusMods,
                ),
                mod_file=Path("Alternate Start - Live Another Life.esp"),
                translation=ModInfo(
                    display_name="Vivez une nouvelle vie",
                    mod_id=CdtModId(
                        installation_file_name="vivez_une_nouvelle_vie_4.2.5_sse.7z",
                        source=Source.Confrerie,
                        mod_id=587,
                        nm_mod_id=272,
                    ),
                    source=Source.Confrerie,
                ),
                download=FileDownload(
                    mod_details=ModDetails(
                        display_name="Vivez une nouvelle vie",
                        file_name="vivez_une_nouvelle_vie_4.2.5_sse.7z",
                        mod_id=CdtModId(
                            installation_file_name="vivez_une_nouvelle_vie_4.2.5_sse.7z",
                            source=Source.Confrerie,
                            mod_id=587,
                            nm_mod_id=272,
                        ),
                        version="4.2.5",
                        timestamp=1751557708,
                        author=None,
                        uploader=None,
                        modpage_url="https://www.confrerie-des-traducteurs.fr/skyrim/mods/587",
                    ),
                    source=Source.Confrerie,
                ),
            ),
        )
    ]

    @pytest.mark.parametrize("json_data, expected_download_list_item", TEST_DATA)
    def test_deserialize(
        self, json_data: dict[str, Any], expected_download_list_item: DownloadListItem
    ) -> None:
        """
        Tests the deserialization of download list items.

        Args:
            json_data (dict[str, Any]): JSON data.
            expected_download_list_item (DownloadListItem): Expected download list item.
        """

        # when
        download_list_item: DownloadListItem = DownloadListItem.model_validate(
            json_data
        )

        # then
        assert download_list_item == expected_download_list_item
