"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

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
