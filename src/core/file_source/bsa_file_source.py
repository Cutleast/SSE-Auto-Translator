"""
Copyright (c) Cutleast
"""

import hashlib
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, override

from cutleast_core_lib.core.cache.function_cache import FunctionCache
from cutleast_core_lib.core.utilities.filesystem import get_file_identifier
from sse_bsa import BSAArchive

from core.utilities.filesystem import split_path_with_bsa

from .file_source import FileSource


class BsaFileSource(FileSource):
    """
    File source for files that are in BSA archives.
    """

    __bsa_archive: BSAArchive

    __bsa_archive_path: Path
    """Path to the BSA archive."""

    __bsa_file_path: Path
    """Relative path to the file within the BSA archive."""

    def __init__(self, file_path: Path) -> None:
        super().__init__(file_path)

        bsa_archive_path: Optional[Path]
        bsa_file_path: Optional[Path]

        bsa_archive_path, bsa_file_path = split_path_with_bsa(file_path)

        if bsa_archive_path is None or bsa_file_path is None:
            raise ValueError(f"File {file_path} is not in a BSA archive!")

        self.__bsa_archive = BSAArchive(bsa_archive_path)
        self.__bsa_archive_path = bsa_archive_path
        self.__bsa_file_path = bsa_file_path

    @override
    def get_file_stream(self) -> BinaryIO:
        return self.__bsa_archive.get_file_stream(self.__bsa_file_path)

    @override
    @FunctionCache.cache
    def get_real_file(self) -> Path:
        tempdir = Path(tempfile.mkdtemp(prefix="SSE-AT_file_source-"))
        self.__bsa_archive.extract_file(self.__bsa_file_path, tempdir)

        return tempdir / self.__bsa_file_path

    @override
    def is_real_file(self) -> bool:
        return False

    @override
    def get_file_identifier(self) -> str:
        # we need to include the file path, because the base identifier of the BSA would
        # apply to all files within
        base_id = int(get_file_identifier(self.__bsa_file_path), base=16)
        file_id = int(
            hashlib.blake2b(
                str(self.__bsa_file_path).encode(), digest_size=8
            ).hexdigest()[:8],
            base=16,
        )

        return hex(base_id + file_id)[2:11]

    def get_bsa_path(self) -> Path:
        """
        Returns:
            Path: Path to the BSA archive.
        """

        return self.__bsa_archive_path

    @override
    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        bsa_archive_path: Optional[Path]
        bsa_archive_path, _ = split_path_with_bsa(file_path)

        return bsa_archive_path is not None and bsa_archive_path.is_file()
