"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from pathlib import Path

import py7zr

from .archive import Archive


class SevenZipArchive(Archive):
    """
    Class for 7z Archives.
    """

    def get_files(self) -> list[str]:
        return [
            file.filename
            for file in py7zr.SevenZipFile(self.path).files
            if not file.is_directory
        ]

    def extract_all(self, dest: Path):
        py7zr.SevenZipFile(self.path).extractall(dest)

    def extract(self, filename: str, dest: Path):
        py7zr.SevenZipFile(self.path).extract(dest, [filename])
