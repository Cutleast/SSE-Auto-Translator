"""
Copyright (c) Cutleast
"""

from core.cache.function_cache import FunctionCache

from ..core_test import CoreTest


class TestFunctionCache(CoreTest):
    """
    Tests `core.cache.function_cache.FunctionCache`.
    """

    def test_with_unhashable_param(self) -> None:
        """
        Tests the `FunctionCache.cache`-decorator on a function with an unhashable
        argument.
        """

        # given
        calls: list[int] = []

        @FunctionCache.cache
        def func(arg: dict[str, int]) -> None:
            calls.append(len(arg))

        # when
        func({"a": 1, "b": 2})

        # then
        assert calls == [2]

        # when
        func({"a": 1, "b": 2})

        # then
        assert calls == [2]
