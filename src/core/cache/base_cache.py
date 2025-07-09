"""
Copyright (c) Cutleast
"""

import hashlib
import logging
import pickle
import time
from abc import ABCMeta, abstractmethod
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Optional

from app_context import AppContext
from core.database.string import String


class BaseCache(metaclass=ABCMeta):
    """
    Abstract base class for app cache.
    """

    log: logging.Logger = logging.getLogger("Cache")

    @abstractmethod
    def get_strings_from_file_path(self, modfile_path: Path) -> Optional[list[String]]:
        """
        Returns cached strings of the specified mod file.

        Args:
            modfile_path (Path): Path to the mod file

        Returns:
            Optional[list[String]]: List of strings or None if the file is not cached
        """

    @abstractmethod
    def set_strings_for_file_path(
        self, modfile_path: Path, strings: list[String]
    ) -> None:
        """
        Sets cached strings for a mod file.

        Args:
            modfile_path (Path): Path to the mod file.
            strings (list[String]): List of strings from this file.
        """

    @staticmethod
    def get_func_identifier(
        func: Callable,
        params: Optional[tuple[tuple[object, ...], dict[str, Any]]] = None,
    ) -> str:
        """
        Get a unique identifier for a function by hashing the function's name and code.

        Args:
            func (Callable): The function to get the identifier for.
            params (Optional[tuple[tuple[object, ...], dict[str, Any]]]):
                The parameters of the function.

        Returns:
            str: A unique identifier for the function.
        """

        function_data: bytes = func.__name__.encode() + func.__code__.co_code
        if params is not None:
            function_data += pickle.dumps(params)

        return hashlib.sha256(function_data).hexdigest()[:8]

    @classmethod
    @lru_cache
    def get_from_cache(cls, cache_file_path: Path) -> Any:
        with cache_file_path.open("rb") as file:
            return pickle.load(file)

    @classmethod
    def save_to_cache(cls, cache_file_path: Path, data: Any) -> None:
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_file_path.open("wb") as file:
            pickle.dump(data, file)

    @classmethod
    def persistent_cache[**P, R](
        cls,
        *,
        cache_subfolder: Optional[Path] = None,
        id_generator: Optional[Callable[P, str]] = None,
        max_age: Optional[float] = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Caches the result of a function in a specified cache folder using pickle.
        Deletes old cache files from the cache folder if `max_age` is specified.

        **Please note:**
            The type hints of the original function params may get lost when decorated.
            TODO: Find a way to preserve the type hints.

        Args:
            cache_subfolder (Optional[Path]):
                The subfolder within the cache folder to store the cache files.
                Defaults to None.
            id_generator (Optional[Callable[P, str]]):
                A function that generates a unique identifier for the cache file.
                Defaults to `Cache.get_func_identifier()`.
            max_age (Optional[float]):
                The maximum age of the cache file in seconds. Defaults to None.

        Returns:
            Callable[P, R]: The wrapped function with caching enabled.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                cache_path: Path = AppContext.get_app().cache.path

                cache_folder: Path
                if cache_subfolder is None:
                    cache_folder = cache_path / "function_cache"
                else:
                    cache_folder = cache_path / cache_subfolder

                cache_file_name: str
                if id_generator is None:
                    cache_file_name = BaseCache.get_func_identifier(
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
