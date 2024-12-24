"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import zipfile
from typing import Optional

from .archive import Archive


class ZIPARchive(Archive):
    """
    Class for ZIP Archives.
    """

    __files: Optional[list[str]] = None

    @property
    def files(self) -> list[str]:
        if self.__files is None:
            self.__files = [
                file.filename
                for file in zipfile.ZipFile(self.path).filelist
                if not file.is_dir()
            ]

        return self.__files
