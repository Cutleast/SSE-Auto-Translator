"""
Copyright (c) Cutleast
"""

from pathlib import Path

from .archive_file_source import ArchiveFileSource
from .bsa_file_source import BsaFileSource
from .file_source import FileSource
from .local_file_source import LocalFileSource


class FileSourceFactory:
    """
    Factory for creating file sources.
    """

    @staticmethod
    def for_file_path(file_path: Path) -> FileSource:
        """
        Creates a file source suited for accessing a given file.

        Args:
            file_path (Path): Path to the file.

        Returns:
            FileSource: File source for the file.
        """

        if BsaFileSource.can_handle(file_path):
            return BsaFileSource(file_path)
        if ArchiveFileSource.can_handle(file_path):
            return ArchiveFileSource(file_path)

        return LocalFileSource(file_path)
