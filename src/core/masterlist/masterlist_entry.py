"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic.dataclasses import dataclass

from core.utilities.base_enum import BaseEnum

from .route_target import RouteTarget


@dataclass
class MasterlistEntry:
    """
    Class for masterlist entries.
    """

    class Type(BaseEnum):
        """
        Masterlist entry types.
        """

        Ignore = "ignore"
        """
        The file should be ignored.
        """

        Route = "route"
        """
        A translation is available although it cannot be found by the online scan.
        """

    type: Type
    """
    Type of the entry.
    """

    targets: Optional[list[RouteTarget]] = None
    """
    List of route targets for this entry.
    None if the entry is not a route.
    """
