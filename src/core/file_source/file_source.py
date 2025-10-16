"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import BinaryIO, override

from cutleast_core_lib.core.cache.function_cache import FunctionCache


class FileSource(metaclass=ABCMeta):
    """
    Abstract base class for file sources.

    File sources are used to access files independently from their location (filesystem
    or e.g. in a BSA archive) with a common interface.

    Use `from_file` to get a file source for a given file.
    """

    _file_path: Path

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    @override
    def __hash__(self) -> int:
        return hash(self._file_path)

    @abstractmethod
    def get_file_stream(self) -> BinaryIO:
        """
        Returns a stream to the file.

        Returns:
            BinaryIO: Stream to the file.
        """

    @abstractmethod
    def get_real_file(self) -> Path:
        """
        Returns a real existing path to the file. If the file is on the file system, its
        path is just returned. If the file is in a archive, it gets extracted to a temp
        folder and the path to the extracted file is returned.

        Returns:
            Path: Path to a real version of the file.
        """

    @abstractmethod
    def is_real_file(self) -> bool:
        """
        Checks if the file is real and accessible on the file system.

        Returns:
            bool: `True` if the file is real, `False` if it is in an archive.
        """

    @abstractmethod
    def get_file_identifier(self) -> str:
        """
        Generates a unique identifier for this file.

        Returns:
            str: Unique identifier.
        """

    @classmethod
    @abstractmethod
    def can_handle(cls, file_path: Path) -> bool:
        """
        Checks if the file source can handle a given file.

        Args:
            file_path (Path): Path to the file.

        Returns:
            bool: `True` if the file source can handle the file, `False` otherwise.
        """

    @staticmethod
    @FunctionCache.cache
    def from_file(file_path: Path) -> FileSource:
        """
        Returns a file source suited for accessing a given file.

        Args:
            file_path (Path): Path to the file.

        Returns:
            FileSource: File source for the file.
        """

        from .bsa_file_source import BsaFileSource
        from .local_file_source import LocalFileSource

        if BsaFileSource.can_handle(file_path):
            return BsaFileSource(file_path)

        return LocalFileSource(file_path)
