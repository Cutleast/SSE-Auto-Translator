"""
Copyright (c) Cutleast
"""

from concurrent.futures import Future
from typing import Any, Callable, Self

type ExecutorPatcher = Callable[[object], SynchronousExecutor]
"""Patches ThreadPoolExecutor in the module of an object."""


class SynchronousExecutor:
    """
    Executor replacement for tests: Runs submitted callables synchronously.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def submit[T](self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:
        future = Future()

        try:
            result = fn(*args, **kwargs)
            future.set_result(result)
        except Exception as exc:
            future.set_exception(exc)

        return future

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False
