"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any

import pytest

from core.database.translation import Translation
from core.translation_provider.cdt_api.cdt_id import CdtModId
from core.translation_provider.nm_api.nxm_id import NxmModId
from core.translation_provider.source import Source

from ..core_test import CoreTest


class TestTranslation(CoreTest):
    """
    Tests `core.database.translation.Translation`.
    """

    INDEX_DATA_TEST_DATA: list[tuple[dict[str, Any], Translation, bool]] = [
        (
            {
                "name": "A translation",
                "mod_id": 123456,
                "file_id": 789012,
                "version": "1.0",
                "original_mod_id": 987654,
                "original_file_id": 321098,
                "original_version": "1.0",
                "source": "NexusMods",
                "timestamp": 1753612277,
            },
            Translation(
                name="A translation",
                path=Path(),
                mod_id=NxmModId(mod_id=123456, file_id=789012),
                version="1.0",
                source=Source.NexusMods,
                timestamp=1753612277,
            ),
            True,
        ),
        (
            {
                "name": "A French translation",
                "mod_id": 123456,
                "version": "1.0",
                "original_mod_id": 987654,
                "original_file_id": 321098,
                "original_version": "1.0",
                "source": "Confrerie",
                "timestamp": 1753612277,
            },
            Translation(
                name="A French translation",
                path=Path(),
                mod_id=CdtModId(mod_id=123456, nm_mod_id=987654),
                version="1.0",
                source=Source.Confrerie,
                timestamp=1753612277,
            ),
            True,
        ),
        (
            {
                "name": "Another translation",
                "mod_id": None,
                "file_id": None,
                "version": None,
                "original_mod_id": None,
                "original_file_id": None,
                "original_version": None,
                "source": "Local",
                "timestamp": 1753615040,
            },
            Translation(name="Another translation", path=Path(), timestamp=1753615040),
            True,
        ),
        (
            {"name": "A minimal translation"},
            Translation(name="A minimal translation", path=Path()),
            False,
        ),
        (
            {
                "name": "Sacrosanct - Vampires de Bordeciel",
                "mod_id": {
                    "installation_file_name": "sacrosanct___vampires_de_bordeciel_6.0.0_sse.7z",
                    "mod_id": 1907,
                    "nm_mod_id": 3928,
                    "source": "Confrérie des Traducteurs",
                },
                "version": "6.0.0",
                "source": "Confrérie des Traducteurs",
                "timestamp": 1735921724,
            },
            Translation(
                name="Sacrosanct - Vampires de Bordeciel",
                path=Path(),
                mod_id=CdtModId(
                    installation_file_name="sacrosanct___vampires_de_bordeciel_6.0.0_sse.7z",
                    mod_id=1907,
                    nm_mod_id=3928,
                ),
                version="6.0.0",
                source=Source.Confrerie,
                timestamp=1735921724,
            ),
            True,
        ),
    ]

    @pytest.mark.parametrize(
        "index_data, expected_translation, compare_timestamp", INDEX_DATA_TEST_DATA
    )
    def test_from_index_data(
        self,
        index_data: dict[str, Any],
        expected_translation: Translation,
        compare_timestamp: bool,
    ) -> None:
        """
        Tests `Translation.from_index_data()`.

        Args:
            index_data (dict[str, Any]): Index data to parse.
            expected_translation (Translation): Expected translation.
            compare_timestamp (bool): Whether to compare the timestamp.
        """

        # when
        translation: Translation = Translation.from_index_data(index_data, Path())

        # then
        assert translation.name == expected_translation.name
        assert translation.mod_id == expected_translation.mod_id
        assert translation.version == expected_translation.version
        assert translation.source == expected_translation.source
        if compare_timestamp:
            assert translation.timestamp == expected_translation.timestamp
