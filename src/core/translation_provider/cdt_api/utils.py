"""
Copyright (c) Cutleast
"""

from datetime import datetime
from typing import TypedDict

import pytz


class TimestampData(TypedDict):
    """
    Type for the timestamp data returned by the CDT API.
    """

    date: str
    """Date of the format "2026-01-08 14:46:05.000000"."""

    timezone_type: int
    """The numeric timezone type."""

    timezone: str
    """The tz name of the timezone."""


def get_unix_timestamp_from_timestamp_data(timestamp_data: TimestampData) -> int:
    """
    Extracts the upload timestamp from the timestamp data returned by the CDT API.

    Args:
        response_data (TimestampData): Raw timestamp data.

    Returns:
        int: Upload timestamp as Unix timestamp
    """

    date: str = timestamp_data["date"]
    timezone: str = timestamp_data["timezone"]

    date_obj: datetime = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
    date_obj_utc: datetime = date_obj.replace(
        tzinfo=pytz.timezone(timezone)
    ).astimezone(pytz.utc)
    timestamp = int(date_obj_utc.timestamp())

    return timestamp
