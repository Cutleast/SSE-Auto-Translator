"""
Copyright (c) Cutleast
"""

from typing import Literal

from cutleast_core_lib.core.utilities.pydantic_utils import include_literal_defaults

from ..base_mod_id import BaseModId
from ..source import Source


@include_literal_defaults
class CdtModId(BaseModId, frozen=True):
    """
    Model for mod ids from the CDT.
    """

    mod_id: int
    """The id of the translation mod."""

    nm_mod_id: int
    """The id of the original mod on Nexus Mods."""

    source: Literal[Source.Confrerie] = Source.Confrerie
