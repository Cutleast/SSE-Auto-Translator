"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path

import rarfile

from .archive import Archive


class RARArchive(Archive):
    """
    Class for RAR Archives.
    """

    def get_files(self) -> list[str]:
        return [
            file.filename
            for file in rarfile.RarFile(self.path).infolist()
            if file.is_file()
        ]

    def extract_all(self, dest: Path):
        retcode = os.system(f'7z.exe x "{self.path}" -o"{dest}" -aoa -y')

        if retcode:
            raise Exception("Unpacking command failed!")

    def extract(self, filename: str, dest: Path):
        retcode = os.system(f'7z.exe x "{self.path}" "{filename}" -o"{dest}" -aoa -y')

        if retcode:
            raise Exception("Unpacking command failed!")
