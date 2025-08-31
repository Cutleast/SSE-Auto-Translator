"""
Copyright (c) Cutleast
"""

from typing import Any, Callable, Iterable, Optional, TypeVar

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


def unique(iterable: Iterable[T], key: Optional[Callable[[T], Any]] = None) -> list[T]:
    """
    Removes all duplicates from an iterable.

    Args:
        iterable (Iterable[T]): Iterable with duplicates.
        key (Optional[Callable[[T], Any]], optional):
            Key function to identify unique elements. Defaults to None.

    Returns:
        list[T]: List without duplicates.
    """

    if key is None:
        return list(set(iterable))

    else:
        return list({key(item): item for item in iterable}.values())


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
