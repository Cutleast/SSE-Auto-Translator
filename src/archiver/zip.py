"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import zipfile

from .archive import Archive


class ZIPARchive(Archive):
    """
    Class for ZIP Archives.
    """

    def get_files(self) -> list[str]:
        return [
            file.filename
            for file in zipfile.ZipFile(self.path).filelist
            if not file.is_dir()
        ]
