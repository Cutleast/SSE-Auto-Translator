"""
Copyright (c) Cutleast
"""

import pytest

from src.core.utilities.exceptions import (
    ApiException,
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

        # then
        with pytest.raises(ExceptionBase) as exc:
            func()
            assert exc.group_contains(RuntimeError)

    def test_wrap_with_subclass(self) -> None:
        # given
        @ApiException.wrap
        def func() -> None:
            raise RuntimeError("Test")

        # then
        with pytest.raises(ApiException) as exc:
            func()
            assert exc.group_contains(RuntimeError)

    def test_wrap_with_params(self) -> None:
        # given
        @InstallationFailedError.wrap
        def func(x: int) -> int:
            assert x == 1
            raise RuntimeError("Test")

        # then
        with pytest.raises(InstallationFailedError) as exc:
            func(1)
            assert exc.group_contains(RuntimeError)
            assert not exc.group_contains(AssertionError)
