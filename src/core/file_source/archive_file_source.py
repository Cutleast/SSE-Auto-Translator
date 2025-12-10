"""
Copyright (c) Cutleast
"""

import hashlib
import logging
from pathlib import Path
from typing import BinaryIO, Optional, override

from cutleast_core_lib.core.archive.archive import Archive
from cutleast_core_lib.core.cache.function_cache import FunctionCache
from cutleast_core_lib.core.filesystem.utils import get_file_identifier

from core.utilities.temp_folder_provider import TempFolderProvider

from .file_source import FileSource


class ArchiveFileSource(FileSource):
    """
    File source for files in regular archives like .7z, .zip, .rar.
    """

    _archive: Archive

    _archive_path: Path
    """Path to the archive."""

    _file_path: Path
    """Path to the file in the archive."""

    __extracted_file: Optional[Path] = None
    """Path to the extracted file. None if not extracted yet."""

    def __init__(self, file_path: Path) -> None:
        super().__init__(file_path)

        archive_path: Optional[Path]
        archive_file_path: Optional[Path]

        archive_path, archive_file_path = self.split_path_with_archive(file_path)

        if archive_path is None or archive_file_path is None:
            raise ValueError(f"File {file_path} is not in an archive!")

        self._archive_path = archive_path
        self._file_path = archive_file_path

        self._archive = self._init_archive()

    def _init_archive(self) -> Archive:
        return FunctionCache.cache(Archive.load_archive)(self._archive_path)

    @override
    def get_file_stream(self) -> BinaryIO:
        return self.get_real_file().open("rb")

    @override
    def get_real_file(self) -> Path:
        if self.__extracted_file is None or not self.__extracted_file.is_file():
            output_folder: Path = TempFolderProvider.get().get_temp_folder()
            output_folder /= get_file_identifier(self._archive_path)
            output_folder.mkdir(parents=True, exist_ok=True)

            logging.info(
                f"Extracting file '{self._file_path}' from '{self._archive_path}' to "
                f"'{output_folder}'..."
            )
            self._archive.extract_files([str(self._file_path)], output_folder)
            self.__extracted_file = output_folder / self._file_path

        return self.__extracted_file

    @override
    def is_real_file(self) -> bool:
        return False

    @override
    def get_file_identifier(self) -> str:
        # we need to include the file path, because the base identifier of the archive
        # would apply to all files within
        base_id = int(get_file_identifier(self._archive_path), base=16)
        file_id = int(
            hashlib.blake2b(str(self._file_path).encode(), digest_size=8).hexdigest()[
                :8
            ],
            base=16,
        )

        return hex(base_id + file_id)[2:11]

    @override
    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        archive_path: Optional[Path]
        archive_path, _ = cls.split_path_with_archive(file_path)

        return archive_path is not None and archive_path.is_file()

    def get_archive_path(self) -> Path:
        """
        Returns:
            Path: Path to the archive.
        """

        return self._archive_path

    @classmethod
    def get_supported_suffixes(cls) -> list[str]:
        """
        Returns:
            list[str]: A list of file types that are supported by this class.
        """

        return [".7z", ".zip", ".rar"]

    @classmethod
    def split_path_with_archive(
        cls, path: Path
    ) -> tuple[Optional[Path], Optional[Path]]:
        """
        Splits a path that may contain an archive file supported by this class.

        1. The first returned value is the path to the archive file, if any. It is None if
        the path does not contain an archive file.
        2. The second returned value is the path to the file in the archive, if any. It is
        None if the path ends at an archive file.

        Args:
            path (Path): The path to split.

        Returns:
            tuple[Optional[Path], Optional[Path]]: See above.
        """

        archive_path: Optional[Path] = None
        file_path: Optional[Path] = None

        parts: list[str] = []
        for part in path.parts:
            parts.append(part)

            if Path(part).suffix.lower() in cls.get_supported_suffixes():
                archive_path = Path(*parts)
                parts.clear()

        if parts:
            file_path = Path(*parts)

        return archive_path, file_path
