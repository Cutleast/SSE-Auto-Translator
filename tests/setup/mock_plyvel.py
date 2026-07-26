"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from types import TracebackType
from typing import Optional, Self


class MockPlyvelDB:
    """
    Mock implementation of plyvel.DB to use JSON for storage instead of LevelDB.
    """

    __data: dict[bytes, bytes]

    def __init__(self, data: Optional[dict[bytes, bytes]] = None) -> None:
        """
        Args:
            data (Optional[dict[bytes, bytes]], optional):
                The initial data as a flat dict of bytes keys and values. Defaults to
                None.
        """

        if data is None:
            data = {}

        self.__data = data

    def iterator(  # noqa: D102
        self, prefix: Optional[bytes] = None
    ) -> Generator[tuple[bytes, bytes], None, None]:
        for key, value in self.__data.items():
            if not prefix or key.startswith(prefix):
                yield key, value

    def put(self, key: bytes, value: bytes) -> None:  # noqa: D102
        self.__data[key] = value

    def get(self, key: bytes) -> Optional[bytes]:  # noqa: D102
        if key in self.__data:
            return self.__data[key]

        return None

    def write_batch(self) -> Self:  # noqa: D102
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        pass
