"""
Copyright (c) Cutleast
"""

import logging
import shutil
import sys
import tempfile
from abc import ABC
from typing import Optional

from src.core.utilities.path import Path

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class BaseTest(ABC):
    """
    Base class for all tests.
    """

    _data_path = Path("tests") / "test_data"
    _res_path = Path("res")
    _temp_folder: Optional[Path] = None

    @classmethod
    def setup_class(cls) -> None:
        """
        Sets up temporary folder for temporary test data.
        """

    @classmethod
    def teardown_class(cls) -> None:
        """
        Cleans up temporary folder (if exists).
        """

        if cls._temp_folder is not None:
            shutil.rmtree(cls._temp_folder)

        cls._temp_folder = None

    @classmethod
    def data_path(cls) -> Path:
        """
        Returns the path to the test data folder.

        Returns:
            Path: The path to the test data folder
        """

        return cls._data_path

    @classmethod
    def res_path(cls) -> Path:
        """
        Returns the path to the resource folder.

        Returns:
            Path: The path to the resource folder
        """

        return cls._res_path

    @classmethod
    def tmp_folder(cls) -> Path:
        """
        Creates a temporary folder or returns an existing one.

        The folder gets deleted after all tests from this class are done.

        Returns:
            Path: The path to the temporary folder
        """

        if cls._temp_folder is None:
            temp_folder_name: str = tempfile.mkdtemp(prefix="SSE-AT_test-")
            cls._temp_folder = Path(temp_folder_name)

        return cls._temp_folder
