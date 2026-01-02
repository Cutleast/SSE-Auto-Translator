"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import override

from pydantic import BaseModel

from core.translation_provider.mod_details import ModDetails
from core.translation_provider.source import Source


class FileDownload(BaseModel):
    """
    Class for single file downloads.
    """

    mod_details: ModDetails
    """Metadata of the downloaded mod file."""

    source: Source
    """Source the download is from."""

    stale: bool = False
    """
    Whether the download is stale and should be removed as soon as a thread picks it up.
    """

    @override
    def __hash__(self) -> int:
        return hash(
            (self.source.name, self.mod_details.mod_id, self.mod_details.file_name)
        )
