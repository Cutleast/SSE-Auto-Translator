"""
Copyright (c) Cutleast
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.core.utilities.singleton import Singleton


class TempFolderProvider(Singleton):
    """
    Singleton class for providing a temporary folder path.
    """

    __folder_name: str
    __base_path: Path
    __temp_folder: Optional[Path] = None

    log: logging.Logger = logging.getLogger("TempFolderProvider")

    def __init__(self, folder_name: str, base_path: Optional[Path] = None) -> None:
        super().__init__()

        self.__folder_name = folder_name
        self.__base_path = base_path or resolve(Path("%temp%"))

    def get_temp_folder(self) -> Path:
        """
        Returns the path to the temporary folder. Creates one if it doesn't exist.

        Returns:
            Path: Path to the temporary folder
        """

        if self.__temp_folder is None or not self.__temp_folder.is_dir():
            self.__temp_folder = self.__base_path / self.__folder_name
            self.__temp_folder.mkdir(parents=True)

        return self.__temp_folder

    def clean_temp_folder(self) -> None:
        """
        Cleans up the temporary folder. Does nothing if there is none or it doesn't
        exist.
        """

        if self.__temp_folder is not None and self.__temp_folder.is_dir():
            shutil.rmtree(self.__temp_folder)
            self.__temp_folder = None
            self.log.info(
                f"Cleaned temp folder '{self.__folder_name}' at '{self.__base_path}'."
            )
