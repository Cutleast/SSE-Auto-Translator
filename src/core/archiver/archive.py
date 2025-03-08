"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from abc import abstractmethod
from fnmatch import fnmatch
from typing import Optional

from core.utilities.filesystem import glob
from core.utilities.path import Path
from core.utilities.process_runner import run_process


class Archive:
    """
    Base class for archives.

    #### Do not instantiate directly, use Archive.load_archive() instead!
    """

    log = logging.getLogger("Archiver")

    __files: Optional[list[str]] = None

    def __init__(self, path: Path):
        self.path = path

    @property
    @abstractmethod
    def files(self) -> list[str]:
        """
        Returns a list of filenames in archive.
        """

        raise NotImplementedError

    def get_files(self) -> list[str]:
        """
        Alias method for `files` property.
        """

        return self.files

    def extract_all(self, dest: Path, full_paths: bool = True) -> None:
        """
        Extracts all files to `dest`.
        """

        cmd = [
            "7z.exe",
            "x" if full_paths else "e",
            str(self.path),
            f"-o{dest}",
            "-aoa",
            "-y",
        ]

        try:
            run_process(cmd)
        except RuntimeError:
            raise Exception("Unpacking command failed!")

    def extract(self, filename: str, dest: Path, full_paths: bool = True) -> None:
        """
        Extracts `filename` from archive to `dest`.
        """

        cmd = [
            "7z.exe",
            "x" if full_paths else "e",
            f"-o{dest}",
            "-aoa",
            "-y",
            "--",
            str(self.path),
            filename,
        ]

        try:
            run_process(cmd)
        except RuntimeError:
            raise Exception("Unpacking command failed!")

    def extract_files(
        self, filenames: list[str], dest: Path, full_paths: bool = True
    ) -> None:
        """
        Extracts `filenames` from archive to `dest`.
        """

        if not len(filenames):
            return

        cmd = [
            "7z.exe",
            "x" if full_paths else "e",
            f"-o{dest}",
            "-aoa",
            "-y",
            str(self.path),
        ]

        # Write filenames to a txt file to workaround commandline length limit
        filenames_txt = self.path.with_suffix(".txt")
        with open(filenames_txt, "w", encoding="utf8") as file:
            file.write("\n".join(filenames))
        cmd.append(f"@{filenames_txt}")

        try:
            run_process(cmd)
        except RuntimeError:
            raise Exception("Unpacking command failed!")
        else:
            os.remove(filenames_txt)

    def add_files(self, files: list[Path]) -> None:
        """
        Adds `files` to archive.
        """

        if not len(files):
            return

        cmd: list[str] = [
            "7z.exe",
            "a",
            str(self.path),
        ]

        # Write filenames to a txt file to workaround commandline length limit
        filenames_txt_path: Path = self.path.with_suffix(".txt")
        with filenames_txt_path.open("w", encoding="utf8") as filenames_txt_file:
            filenames_txt_file.write("\n".join([str(f) for f in files]))
        cmd.append(f"@{filenames_txt_path}")

        try:
            run_process(cmd)
        except RuntimeError:
            raise Exception("Packing command failed!")
        else:
            os.remove(filenames_txt_path)

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

    def glob(self, pattern: str, case_sensitive: bool = False) -> list[str]:
        """
        Returns a list of file paths that match a specified glob pattern.

        Args:
            pattern (str): Glob pattern.
            case_sensitive (bool, optional): Case sensitive. Defaults to False.

        Returns:
            list[str]: List of matching filenames
        """

        return glob(pattern, self.files, case_sensitive)

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
