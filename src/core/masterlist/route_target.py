"""
Copyright (c) Cutleast
"""

from dataclasses import field
from typing import Optional

from pydantic.dataclasses import dataclass

from core.translation_provider.source import Source


@dataclass
class RouteTarget:
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

    source: Source = field(default=Source.NexusMods)
    """
    The source of the target.
    """
