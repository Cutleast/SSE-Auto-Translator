"""
Copyright (c) Cutleast
"""

from typing import Annotated

from pydantic import Field

from .cdt_api.cdt_id import CdtModId
from .nm_api.nxm_id import NxmModId

type ModId = Annotated[NxmModId | CdtModId, Field(discriminator="source")]
"""Type alias for mod ids."""
