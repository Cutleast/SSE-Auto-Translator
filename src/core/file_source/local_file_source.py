"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import BinaryIO, override

from cutleast_core_lib.core.utilities.filesystem import get_file_identifier

from .file_source import FileSource


class LocalFileSource(FileSource):
    """
    File source for local files that are accessible on the file system.
    """

    def __init__(self, file_path: Path) -> None:
        super().__init__(file_path)

        if not file_path.is_file():
            raise FileNotFoundError(f"File {file_path} does not exist!")

    @override
    def get_file_stream(self) -> BinaryIO:
        return self._file_path.open("rb")

    @override
    def get_real_file(self) -> Path:
        return self._file_path

    @override
    def is_real_file(self) -> bool:
        return True

    @override
    def get_file_identifier(self) -> str:
        return get_file_identifier(self._file_path)

    @override
    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        return file_path.is_file()
