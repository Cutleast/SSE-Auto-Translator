"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Optional, TypeAlias


@dataclass
class ProgressUpdate:
    """
    Progress update item to be passed via `QtCore.Signal`.
    """

    current: int
    """
    Current progress.
    """

    maximum: int
    """
    Maximum progress (for eg. total file size).
    """

    status_text: Optional[str] = None
    """
    Status text to be displayed, if any.
    """

    class Status(StrEnum):
        """
        Various status codes that are not visible.
        """

        UserActionRequired = "user_action_required"
        """
        Process cannot continue without user action.
        """

        Finished = "finished"
        """
        Process is finished and item can be removed from GUI.
        """

    speed: Optional[int] = None
    """
    Measured download speed in bytes per second, if any.
    """


ProgressCallback: TypeAlias = Callable[[ProgressUpdate], None]
"""
Function or method that takes a `ProgressUpdate` as positional argument.
"""


def safe_run_callback(
    progress_callback: Optional[ProgressCallback], arg: ProgressUpdate
) -> None:
    """
    Function to call a progress callback or do nothing if it is None.

    Args:
        progress_callback (Optional[ProgressCallback]): Progress callback to call or None.
        arg (ProgressUpdate): Argument to pass to progress callback.
    """

    if progress_callback is not None:
        progress_callback(arg)
