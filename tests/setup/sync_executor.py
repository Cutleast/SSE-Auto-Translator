"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from concurrent.futures import Future
from types import TracebackType
from typing import Any, Optional, Self

type ExecutorPatcher = Callable[[object], SynchronousExecutor]
"""Patches ThreadPoolExecutor in the module of an object."""


class SynchronousExecutor:
    """
    Executor replacement for tests: Runs submitted callables synchronously.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D107
        pass

    def submit[T](self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:  # noqa: D102
        future = Future()

        try:
            result = fn(lambda *_: None, *args, **kwargs)
            future.set_result(result)
        except Exception as exc:  # noqa: BLE001
            future.set_exception(exc)

        return future

    def set_main_progress_text(self, text: str) -> None:  # noqa: D102
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        return False
