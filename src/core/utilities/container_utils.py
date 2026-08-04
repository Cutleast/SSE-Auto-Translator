"""
Copyright (c) Cutleast
"""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


def join_lists(*iterables: Iterable[T]) -> list[T]:
    """
    Joins multiple iterables into a single list.

    Convenience function for
        `[item for iterable in iterables for item in iterable]`.

    Args:
        iterables (Iterable[T]): Iterables to join.

    Returns:
        list[T]: Joined list.
    """

    return [item for iterable in iterables for item in iterable]


def join_dicts(*dicts: dict[K, V]) -> dict[K, V]:
    """
    Joins multiple dicts into a single dict.

    Convenience function for
        `{k: v for d in dicts for k, v in d.items()}`

    Args:
        dicts (dict[K, V]): Dicts to join.

    Returns:
        dict[K, V]: Joined dict.
    """

    return {k: v for d in dicts for k, v in d.items()}
