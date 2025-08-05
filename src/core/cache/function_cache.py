"""
Copyright (c) Cutleast
"""

import functools
import hashlib
import pickle
from typing import Any, Callable, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class FunctionCache:
    """
    Class for caching pairs of function parameters and results.
    """

    __cache: dict[str, Any] = {}

    @classmethod
    def cache(cls, func: Callable[P, R]) -> Callable[P, R]:
        """
        `functools.cache`-like decorator but the parameters don't have to be hashable.

        Args:
            func (Callable[P, R]): The function to cache.

        Returns:
            Callable[P, R]: The cached function.
        """

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = cls.get_func_identifier(func, (args, kwargs))
            if key in cls.__cache:
                return cls.__cache[key]

            result = func(*args, **kwargs)
            cls.__cache[key] = result

            return result

        return wrapper

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
