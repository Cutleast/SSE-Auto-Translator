"""
Copyright (c) Cutleast
"""

import re
import time
from datetime import datetime
from fnmatch import fnmatch


def datetime_format_to_regex(format_string: str) -> str:
    """
    Creates a regex pattern of a datetime format string.

    Args:
        format_string (str): Datetime format string, for example `%d.%m.%Y-%H.%M.%S.log`.

    Returns:
        str: Regex matching the datetime format,
            for example `[\\d]{2}\\.[\\d]{2}\\.-[\\d]{2}\\.[\\d]{2}\\.[\\d]{2}\\.log`.
    """

    # Mapping of datetime format codes to regex patterns
    format_mappings: dict[str, str] = {
        "%d": r"\d{2}",
        "%m": r"\d{2}",
        "%Y": r"\d{4}",
        "%H": r"\d{2}",
        "%M": r"\d{2}",
        "%S": r"\d{2}",
        "%f": r"\d{6}",
    }

    # Escape any characters in the format string that are not format codes
    escaped_string: str = re.escape(format_string)

    # Replace format codes with regex patterns
    for format_code, regex_pattern in format_mappings.items():
        escaped_string = escaped_string.replace(re.escape(format_code), regex_pattern)

    return "^" + escaped_string + "$"


def get_diff(start_time: str, end_time: str, str_format: str = "%H:%M:%S") -> str:
    """
    Calculate the difference between two given times.

    Args:
        start_time (str): Start time.
        end_time (str): End time.
        str_format (str, optional): Format of the time strings. Defaults to "%H:%M:%S".

    Returns:
        str: Time difference in the same format as str_format.

    TODO: Fix
    """

    return str(
        datetime.strptime(end_time, str_format)
        - datetime.strptime(start_time, str_format)
    )


def fmt_timestamp(timestamp: int | float, fmt: str = "%d.%m.%Y %H:%M:%S") -> str:
    """
    Creates a time string from a UNIX timestamp.
    """

    return time.strftime(fmt, time.localtime(timestamp))


def to_timestamp(time_string: str) -> float:
    """
    Converts `time_string` into a UNIX timestamp.
    """

    if fnmatch(time_string, "*.*.* *:*"):
        return time.mktime(time.strptime(time_string, "%d.%m.%Y %H:%M"))
    else:
        return time.mktime(time.strptime(time_string, "%d.%m.%Y"))
