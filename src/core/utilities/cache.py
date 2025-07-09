"""
Copyright (c) Cutleast
"""

import functools
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def cache(func: Callable[P, R]) -> Callable[P, R]:
    """
    Wrapper for `functools.cache` to maintain Python >3.12 type annotations for static
    type checkers.

    Returns:
        Callable[P, R]: wrapped function
    """

    wrapped: Callable[P, R] = functools.cache(func)  # type: ignore

    return wrapped
