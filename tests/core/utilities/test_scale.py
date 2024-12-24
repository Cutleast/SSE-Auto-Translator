"""
Copyright (c) Cutleast
"""

from src.core.utilities.scale import scale_value


class TestScale:
    """
    Tests `core.utilities.scale`.
    """

    def test_scale_value_simple(self) -> None:
        """
        Tests `core.utilities.scale.scale_value()` on a simple value.
        """

        # given
        input_value: float = 1234567.89
        expected_output: str = "1.18 MB"

        # when
        real_output: str = scale_value(input_value)

        # then
        assert expected_output == real_output

    def test_scale_value_negative(self) -> None:
        """
        Tests `core.utilities.scale.scale_value()` on a negative value.
        """

        # given
        input_value: float = -1234567.89
        expected_output: str = "-1.18 MB"

        # when
        real_output: str = scale_value(input_value)

        # then
        assert expected_output == real_output

    def test_scale_value_small(self) -> None:
        """
        Tests `core.utilities.scale.scale_value()` on a value smaller than the factor.
        """

        # given
        input_value: float = 123.00
        expected_output: str = "123 B"

        # when
        real_output: str = scale_value(input_value)

        # then
        assert expected_output == real_output
