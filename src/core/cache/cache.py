"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import functools
import logging
import os
import pickle
import shutil
import time
from pathlib import Path
from typing import Any, Callable, Optional, ParamSpec, TypeVar

from semantic_version import Version

from .function_cache import FunctionCache

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
C = TypeVar("C", bound="Cache")


class Cache:
    """
    Class for application cache.

    The class provides the singleton getter `Cache.get()` and can only be instantiated
    once.
    """

    path: Path
    """Path to the cache folder."""

    __cache_version_file: Path
    """Path to the file specifying the cache's version."""

    __instance: Optional[Cache] = None
    """Singleton cache instance."""

    log: logging.Logger = logging.getLogger("Cache")

    def __init__(self, cache_path: Path, app_version: str) -> None:
        """
        Args:
            cache_path (Path): Path to the cache folder.
            app_version (str):
                Application version, used for invalidating caches from older versions.

        Raises:
            ValueError: If a cache instance already exists.
        """

        if Cache.__instance is not None:
            raise ValueError("A cache instance already exists!")

        Cache.__instance = self

        self.path = cache_path
        self.__cache_version_file = self.path / "version"

        if self.__cache_version_file.is_file():
            cache_version: str = self.__cache_version_file.read_text().strip()

            if app_version != "development" and (
                Version(cache_version) < Version(app_version)
            ):
                self.clear_caches()
                self.log.info("Cleared caches due to outdated cache version.")

        elif self.path.is_dir() and os.listdir(self.path):
            self.clear_caches()
            self.log.info("Cleared caches due to missing cache version file.")

        self.path.mkdir(parents=True, exist_ok=True)
        self.__cache_version_file.write_text(app_version)

    def clear_caches(self) -> None:
        """
        Clears all caches.
        """

        shutil.rmtree(self.path, ignore_errors=True)
        self.log.info("Caches cleared.")

    @classmethod
    def get(cls: type[C]) -> Optional[C]:
        """
        Returns the singleton cache instance or `None` if it doesn't exist.

        Returns:
            Optional[C]: The singleton cache instance or `None` if it doesn't exist.
        """

        return cls.__instance  # pyright: ignore[reportReturnType]

    @classmethod
    @FunctionCache.cache
    def get_from_cache(
        cls, cache_file_path: Path, default: Optional[T] = None
    ) -> Any | T:
        """
        Gets the content of a cache file and deserializes it with pickle.
        The data is only read once and then cached in-memory.

        Args:
            cache_file_path (Path):
                The path to the cache file, relative to the cache folder.
            default (Optional[T], optional):
                The default value to return if the cache file does not exist. Defaults
                to None.

        Raises:
            FileNotFoundError:
                When the cache file does not exist and `default` is None.

        Returns:
            Any: The deserialized content of the cache file.
        """

        cache: Optional[Cache] = cls.get()
        if cache is not None:
            cache_file_path = cache.path / cache_file_path

        if not cache_file_path.is_file() and default is not None:
            return default

        with cache_file_path.open("rb") as file:
            return pickle.load(file)

    @classmethod
    def save_to_cache(cls, cache_file_path: Path, data: Any) -> None:
        """
        Serializes data with pickle and saves it to a cache file.
        **Does nothing if there is no cache instance.**

        Args:
            cache_file_path (Path):
                The path to the cache file, relative to the cache folder.
            data (Any): The data to serialize and save to the cache file.
        """

        cache: Optional[Cache] = cls.get()
        if cache is None:
            return

        cache_file_path = cache.path / cache_file_path
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_file_path.open("wb") as file:
            pickle.dump(data, file)

    @classmethod
    def persistent_cache(
        cls,
        *,
        cache_subfolder: Optional[Path] = None,
        id_generator: Optional[Callable[..., str]] = None,
        max_age: Optional[float] = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Caches the result of a function in a specified cache folder using pickle.
        Deletes old cache files from the cache folder if `max_age` is specified.

        Args:
            cache_subfolder (Optional[Path]):
                The subfolder within the cache folder to store the cache files.
                Defaults to None.
            id_generator (Optional[Callable[..., str]]):
                A function that is called with the decorated function's parameters and
                returns a unique identifier for the cache file. Defaults to
                `Cache.get_func_identifier()`.
            max_age (Optional[float]):
                The maximum age of the cache file in seconds. Defaults to None.

        Returns:
            Callable[P, R]: The wrapped function with caching enabled.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                cache: Optional[Cache] = cls.get()

                if cache is None:
                    cls.log.warning("No cache available!")
                    return func(*args, **kwargs)

                cache_path: Path = cache.path

                cache_folder: Path
                if cache_subfolder is None:
                    cache_folder = cache_path / "function_cache"
                else:
                    cache_folder = cache_path / cache_subfolder

                cache_file_name: str
                if id_generator is None:
                    cache_file_name = FunctionCache.get_func_identifier(
                        func, (args, kwargs)
                    )
                else:
                    cache_file_name = id_generator(*args, **kwargs)
                cache_file_path: Path = cache_folder / (cache_file_name + ".cache")

                result: R
                if cache_file_path.is_file() and (
                    max_age is None
                    or (time.time() - cache_file_path.stat().st_mtime) < max_age
                ):
                    result = cls.get_from_cache(cache_file_path)

                    cls.log.debug(f"Loaded result from cache for '{func.__name__}'.")

                else:
                    result = func(*args, **kwargs)

                    if cache_file_path.is_file():
                        cls.log.debug(
                            f"Overwriting result in cache for '{func.__name__}'..."
                        )

                    cls.save_to_cache(cache_file_path, result)

                return result

            return wrapper

        return decorator
