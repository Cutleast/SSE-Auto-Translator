"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import subprocess
from fnmatch import fnmatch
from pathlib import Path


class Archive:
    """
    Base class for archives.

    #### Do not instantiate directly, use Archive.load_archive() instead!
    """

    log = logging.getLogger("Archiver")

    def __init__(self, path: Path):
        self.path = path

    def get_files(self) -> list[str]:
        """
        Returns a list of filenames in archive.
        """

        raise NotImplementedError

    def extract_all(self, dest: Path):
        """
        Extracts all files to `dest`.
        """

        cmd = ["7z.exe", "x", str(self.path), f"-o{dest}", "-aoa", "-y"]

        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode:
            self.log.error(process.stderr)
            raise Exception("Unpacking command failed!")

    def extract(self, filename: str, dest: Path):
        """
        Extracts `filename` from archive to `dest`.
        """

        cmd = ["7z.exe", "x", f"-o{dest}", "-aoa", "-y", "--", str(self.path), filename]

        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode:
            self.log.error(process.stderr)
            raise Exception("Unpacking command failed!")

    def extract_files(self, filenames: list[str], dest: Path):
        """
        Extracts `filenames` from archive to `dest`.
        """

        cmd = [
            "7z.exe",
            "x",
            f"-o{dest}",
            "-aoa",
            "-y",
            "--",
            str(self.path),
        ]
        cmd += filenames

        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode:
            self.log.error(process.stderr)
            raise Exception("Unpacking command failed!")

    def find(self, pattern: str) -> list[str]:
        """
        Returns all files in archive that match `pattern` (wildcard).
        """

        result = [file for file in self.get_files() if fnmatch(file, pattern)]

        if not result:
            raise FileNotFoundError(
                f"Found no file for pattern {pattern!r} in archive."
            )

        return result

    @staticmethod
    def load_archive(archive_path: Path) -> "Archive":
        """
        Returns Archive object suitable for `archive_path`'s format.

        Raises `NotImplementedError` if archive format is not supported.
        """

        from .rar import RARArchive
        from .sevenzip import SevenZipArchive
        from .zip import ZIPARchive

        match archive_path.suffix.lower():
            case ".rar":
                return RARArchive(archive_path)
            case ".7z":
                return SevenZipArchive(archive_path)
            case ".zip":
                return ZIPARchive(archive_path)
            case suffix:
                raise NotImplementedError(
                    f"Archive format {suffix!r} not yet supported!"
                )
