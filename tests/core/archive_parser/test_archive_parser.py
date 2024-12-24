"""
Copyright (c) Cutleast
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.join(os.getcwd(), "src"))

from core.archive_parser.archive_parser import ArchiveParser


class TestArchiveParser:
    """
    Tests `core.archive_parser.archive_parser.ArchiveParser`.

    # TODO: Expand this
    """

    bsas_path: Path = Path(__file__).parent / "bsas"
    test_bsas: list[Path] = [
        bsas_path / "RiftenExtension.bsa",
        bsas_path / "RiftenExtension - Textures.bsa",
    ]

    @pytest.mark.parametrize("bsa_path", test_bsas)
    def test_parse_archive(self, bsa_path: Path) -> None:
        # given
        parser = ArchiveParser(bsa_path)

        # when
        parser.parse_archive()

        # then
        assert parser.parsed_data is not None
