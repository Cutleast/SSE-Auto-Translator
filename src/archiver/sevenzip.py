"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import py7zr

from .archive import Archive


class SevenZipArchive(Archive):
    """
    Class for 7z Archives.
    """

    __files: list[str] = None

    @property
    def files(self) -> list[str]:
        if self.__files is None:
            self.__files = [
                file.filename
                for file in py7zr.SevenZipFile(self.path).files
                if not file.is_directory
            ]
        
        return self.__files
