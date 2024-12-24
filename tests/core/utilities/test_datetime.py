"""
Copyright (c) Cutleast
"""

import pytest

from src.core.utilities.datetime import datetime_format_to_regex, get_diff


class TestDatetime:
    """
    Tests `core.utilities.datetime`.
    """

    def test_datetime_format_to_regex_1(self) -> None:
        """
        Tests `core.utilities.datetime.datetime_format_to_regex()`.
        """

        # given
        input_value: str = "%d.%m.%Y-%H.%M.%S.log"
        expected_output: str = r"^\d{2}\.\d{2}\.\d{4}\-\d{2}\.\d{2}\.\d{2}\.log$"

        # when
        real_output: str = datetime_format_to_regex(input_value)

        # then
        assert expected_output == real_output

    def test_datetime_format_to_regex_2(self) -> None:
        """
        Tests `core.utilities.datetime.datetime_format_to_regex()`.
        """

        # given
        input_value: str = "%d-%m-%Y-%H-%M-%S.log"
        expected_output: str = r"^\d{2}\-\d{2}\-\d{4}\-\d{2}\-\d{2}\-\d{2}\.log$"

        # when
        real_output: str = datetime_format_to_regex(input_value)

        # then
        assert expected_output == real_output

    def test_get_diff(self) -> None:
        """
        Tests `core.utilities.datetime.get_diff()`.
        """

        # given
        start_time: str = "10:00:00"
        end_time: str = "11:00:00"
        expected_output: str = "1:00:00"

        # when
        real_output: str = get_diff(start_time, end_time)

        # then
        assert expected_output == real_output

    @pytest.mark.skip
    def test_get_diff_with_custom_format(self) -> None:
        """
        Tests `core.utilities.datetime.get_diff()` with a custom format.

        TODO: Fix this test
        """

        # given
        start_time: str = "10:00"
        end_time: str = "11:00"
        str_format: str = "%H:%M"
        expected_output: str = "1:00"

        # when
        real_output: str = get_diff(start_time, end_time, str_format)

        # then
        assert expected_output == real_output
