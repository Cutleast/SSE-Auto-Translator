"""
Copyright (c) Cutleast
"""

import pytest

from src.core.translation_provider.exceptions import RequestError
from src.core.utilities.exceptions import (
    ExceptionBase,
    InstallationFailedError,
)


class TestExceptionBase:
    """
    Tests `core.utilities.exceptions.ExceptionBase`.
    """

    def test_wrap(self) -> None:
        # given
        @ExceptionBase.wrap
        def func() -> None:
            raise RuntimeError("Test")

        # when
        with pytest.raises(ExceptionBase) as exc:
            func()

        # then
        isinstance(exc.value.__cause__, RuntimeError)

    def test_wrap_with_subclass(self) -> None:
        # given
        @RequestError.wrap
        def func() -> None:
            raise RuntimeError("Test")

        # when
        with pytest.raises(RequestError) as exc:
            func()

        # then
        isinstance(exc.value.__cause__, RuntimeError)

    def test_wrap_with_params(self) -> None:
        # given
        @InstallationFailedError.wrap
        def func(x: int) -> int:
            assert x == 1
            raise RuntimeError("Test")

        # when
        with pytest.raises(InstallationFailedError) as exc:
            func(1)

        # then
        isinstance(exc.value.__cause__, RuntimeError)
