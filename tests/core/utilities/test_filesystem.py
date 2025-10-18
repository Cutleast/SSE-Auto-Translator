"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, TypeVar

import pytest

from core.utilities.filesystem import split_path_with_bsa

T = TypeVar("T")


class TestFilesystem:
    """
    Tests `core.utilities.filesystem`.
    """

    TEST_SPLIT_BSA_PATH_DATA: list[tuple[Path, Optional[Path], Optional[Path]]] = [
        (
            Path("C:\\Modding\\Test.bsa\\Test.txt"),
            Path("C:\\Modding\\Test.bsa"),
            Path("Test.txt"),
        ),
        (
            Path("C:\\Modding\\Test\\Test.txt"),
            None,
            Path("C:\\Modding\\Test\\Test.txt"),
        ),
        (Path("Test.bsa\\Test.txt"), Path("Test.bsa"), Path("Test.txt")),
        (Path("Test.bsa"), Path("Test.bsa"), None),
    ]

    @pytest.mark.parametrize(
        "input_path, expected_bsa_path, expected_file_path", TEST_SPLIT_BSA_PATH_DATA
    )
    def test_split_path_with_bsa(
        self,
        input_path: Path,
        expected_bsa_path: Optional[Path],
        expected_file_path: Optional[Path],
    ) -> None:
        """
        Tests `core.utilities.filesystem.split_path_with_bsa()`.
        """

        # when
        real_bsa_path: Optional[Path]
        real_file_path: Optional[Path]
        real_bsa_path, real_file_path = split_path_with_bsa(input_path)

        # then
        assert real_bsa_path == expected_bsa_path
        assert real_file_path == expected_file_path
