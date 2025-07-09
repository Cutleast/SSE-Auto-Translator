"""
Copyright (c) Cutleast
"""

import time
from pathlib import Path

from app import App
from core.cache.cache import Cache

from ..core_test import CoreTest


class TestCache(CoreTest):
    """
    Tests `core.cache.cache.Cache`.
    """

    def test_persistent_cache(self, app_context: App) -> None:
        """
        Tests the `core.cache.cache.Cache.persistent_cache`-decorator function.
        """

        # given
        cache: Cache = app_context.cache
        cache_file_name: str = "test_cache_file"
        cache_subfolder: Path = Path("test_cache")
        calls: list[int] = []

        def sum_(x: int, y: int) -> int:
            result: int = x + y
            calls.append(result)
            return result

        @Cache.persistent_cache(
            cache_subfolder=cache_subfolder, id_generator=lambda x, y: cache_file_name
        )
        def test_function(x: int, y: int) -> int:
            return sum_(x, y)

        # when
        result1: int = test_function(1, 2)
        result2: int = test_function(1, 2)

        # then
        assert calls == [3]
        assert result1 == result2 == 3
        assert (cache.path / cache_subfolder / (cache_file_name + ".cache")).is_file()

    def test_persistence_cache_with_max_age(self, app_context: App) -> None:
        """
        Tests the `core.cache.cache.Cache.persistent_cache`-decorator function with a
        `max_age` parameter.
        """

        # given
        cache: Cache = app_context.cache
        cache_file_name: str = "test_cache_file"
        cache_subfolder: Path = Path("test_cache_with_max_age")
        calls: list[int] = []

        def sum_(x: int, y: int) -> int:
            result: int = x + y
            calls.append(result)
            return result

        @Cache.persistent_cache(
            cache_subfolder=cache_subfolder,
            id_generator=lambda x, y: cache_file_name,
            max_age=1,
        )
        def test_function(x: int, y: int) -> int:
            return sum_(x, y)

        # when
        result1: int = test_function(1, 2)
        time.sleep(1)
        result2: int = test_function(1, 2)
        result3: int = test_function(1, 2)

        # then
        assert calls == [3, 3]
        assert result1 == result2 == result3 == 3
        assert (cache.path / cache_subfolder / (cache_file_name + ".cache")).is_file()
