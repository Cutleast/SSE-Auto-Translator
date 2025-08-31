"""
Copyright (c) Cutleast
"""

from pathlib import Path

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.utilities.filesystem import get_file_identifier, glob
from sse_bsa import BSAArchive


class BsaFileProvider:
    """
    Utility class for providing files from BSA archives.
    """

    @staticmethod
    @Cache.persistent_cache(
        cache_subfolder=Path("bsa_cache"),
        id_generator=lambda bsa_archive_path: get_file_identifier(bsa_archive_path),
    )
    def get_file_list(bsa_archive_path: Path) -> list[Path]:
        """
        Gets a list of all files in the specified BSA archive.

        Args:
            bsa_archive_path (Path): Path to the BSA archive.

        Returns:
            list[Path]: List of file paths.
        """

        archive = BSAArchive(bsa_archive_path)
        return [Path(f) for f in archive.files]

    @staticmethod
    def glob(pattern: str, bsa_archive_path: Path) -> list[Path]:
        """
        Scans a BSA archive for files matching the specified pattern.

        Args:
            pattern (str): Glob pattern.
            bsa_archive_path (Path): Path to the BSA archive.

        Returns:
            list[Path]: List of file paths.
        """

        files: list[Path] = BsaFileProvider.get_file_list(bsa_archive_path)
        return glob(pattern, files)
