"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import BinaryIO, cast, override

from cutleast_core_lib.core.archive.archive import Archive
from cutleast_core_lib.core.cache.function_cache import FunctionCache
from sse_bsa import BSAArchive

from core.file_source.archive_file_source import ArchiveFileSource


class BsaFileSource(ArchiveFileSource):
    """
    File source for files that are in BSA archives.
    """

    class BsaWrapper(Archive):
        """
        Class wrapping the `sse_bsa.BSAArchive` class in the
        `cutleast_core_lib.core.archive.archive.Archive` interface.
        """

        __bsa_archive: BSAArchive

        def __init__(self, path: Path) -> None:
            super().__init__(path)

            self.__bsa_archive = BsaFileSource.BsaWrapper.__init_bsa(path)

        @property
        @override
        def files(self) -> list[str]:
            return list(map(str, self.__bsa_archive.files))

        @override
        def extract_all(self, dest: Path, full_paths: bool = True) -> None:
            self.__bsa_archive.extract(dest)

        @override
        def extract(self, filename: str, dest: Path, full_paths: bool = True) -> None:
            self.__bsa_archive.extract_file(filename, dest)

        @override
        def extract_files(
            self, filenames: list[str], dest: Path, full_paths: bool = True
        ) -> None:
            for file in filenames:
                self.__bsa_archive.extract_file(file, dest)

        def get_file_stream(self, filename: Path) -> BinaryIO:
            return self.__bsa_archive.get_file_stream(filename)

        @staticmethod
        @FunctionCache.cache
        def __init_bsa(path: Path) -> BSAArchive:
            return BSAArchive(path)

    @override
    def _init_archive(self) -> Archive:
        return BsaFileSource.BsaWrapper(self._archive_path)

    @override
    def get_file_stream(self) -> BinaryIO:
        return cast(BsaFileSource.BsaWrapper, self._archive).get_file_stream(
            self._file_path
        )

    @override
    @classmethod
    def get_supported_suffixes(cls) -> list[str]:
        return [".bsa"]
