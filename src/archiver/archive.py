"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import subprocess
from fnmatch import fnmatch
from pathlib import Path

from virtual_glob import InMemoryPath, glob


class Archive:
    """
    Base class for archives.

    #### Do not instantiate directly, use Archive.load_archive() instead!
    """

    log = logging.getLogger("Archiver")

    __files: list[str] = None

    def __init__(self, path: Path):
        self.path = path

    @property
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

    def extract_all(self, dest: Path):
        """
        Extracts all files to `dest`.
        """

        cmd = ["7z.exe", "x", str(self.path), f"-o{dest}", "-aoa", "-y"]

        with subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf8",
            errors="ignore",
        ) as process:
            output = process.stderr.read()

        if process.returncode:
            self.log.debug(f"Command: {cmd}")
            self.log.error(output)
            raise Exception("Unpacking command failed!")

    def extract(self, filename: str, dest: Path):
        """
        Extracts `filename` from archive to `dest`.
        """

        cmd = ["7z.exe", "x", f"-o{dest}", "-aoa", "-y", "--", str(self.path), filename]

        with subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf8",
            errors="ignore",
        ) as process:
            output = process.stderr.read()

        if process.returncode:
            self.log.debug(f"Command: {cmd}")
            self.log.error(output)
            raise Exception("Unpacking command failed!")

    def extract_files(self, filenames: list[str], dest: Path):
        """
        Extracts `filenames` from archive to `dest`.
        """

        if not len(filenames):
            return

        cmd = [
            "7z.exe",
            "x",
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

        with subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf8",
            errors="ignore",
        ) as process:
            output = process.stderr.read()

        if process.returncode:
            self.log.debug(f"Command: {cmd}")
            self.log.error(output)
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

    def glob(self, pattern: str) -> list[str]:
        """
        Returns a list of file paths that
        match the <pattern>.

        Parameters:
            pattern: str, everything that fnmatch supports

        Returns:
            list of matching filenames
        """

        # Workaround case-sensitivity
        files: dict[str, str] = {file.lower(): file for file in self.files}

        fs = InMemoryPath.from_list(list(files.keys()))
        matches = [files[p.path] for p in glob(fs, pattern)]

        return matches

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
