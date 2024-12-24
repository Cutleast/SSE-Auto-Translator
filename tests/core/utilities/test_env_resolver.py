"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path

from src.core.utilities.env_resolver import resolve


class TestEnvResolver:
    """
    Tests `core.utilities.env_resolver`.
    """

    def test_resolve_path_temp(self) -> None:
        """
        Tests `core.utilities.env_resolver.resolve()` on a path containing `%temp%`.
        """

        # given
        input_value: Path = Path("%TEmp%") / "test"
        expected_output: Path = Path(os.getenv("temp")) / "test"  # type: ignore[arg-type]

        # when
        real_output: Path = resolve(input_value)

        # then
        assert expected_output == real_output

    def test_resolve_path_custom(self) -> None:
        """
        Tests `core.utilities.env_resolver.resolve()` on a custom variable `%game%`.
        """

        # given
        input_value: Path = Path("%gAmE%") / "test"
        expected_output: Path = Path("C:\\Modding\\game") / "test"
        vars: dict[str, str] = {"game": "C:\\Modding\\game"}

        # when
        real_output: Path = resolve(input_value, **vars)

        # then
        assert expected_output == real_output

    def test_resolve_str_path(self) -> None:
        """
        Tests `core.utilities.env_resolver.resolve()` on a string containing `%path%`.
        """

        # given
        input_value: str = "PATH Variable is as follows: %path%"
        expected_output: str = "PATH Variable is as follows: " + os.getenv("path")  # type: ignore[operator]

        # when
        real_output: str = resolve(input_value)

        # then
        assert expected_output == real_output

    def test_resolve_str_custom(self) -> None:
        """
        Tests `core.utilities.env_resolver.resolve()` on a custom variable `%game%`.
        """

        # given
        input_value: str = "Game is installed here: %GAME%"
        expected_output: str = (
            "Game is installed here: C:\\Modding\\DbGd-Installer-Test\\game"
        )
        vars: dict[str, str] = {"game": "C:\\Modding\\DbGd-Installer-Test\\game"}

        # when
        real_output: str = resolve(input_value, **vars)

        # then
        assert expected_output == real_output

    def test_resolve_path_no_vars(self) -> None:
        """
        Tests `core.utilities.env_resolver.resolve()` on a path containing no valid variable.
        """

        # given
        input_value: Path = Path("%test%") / "test"
        expected_output: Path = Path("%test%") / "test"

        # when
        real_output: Path = resolve(input_value)

        # then
        assert expected_output == real_output
