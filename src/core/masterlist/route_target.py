"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic import BaseModel

from core.translation_provider.source import Source


class RouteTarget(BaseModel, frozen=True):
    """
    Class for route targets.
    """

    mod_id: int
    """
    The mod id of the target.
    """

    file_id: Optional[int] = None
    """
    The file id of the target.
    """

    source: Source = Source.NexusMods
    """
    The source of the target.
    """
