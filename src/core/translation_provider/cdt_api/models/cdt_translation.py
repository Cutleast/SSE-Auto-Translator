"""
Copyright (c) Cutleast
"""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from ..utils import get_unix_timestamp_from_timestamp_data


class CdtTranslation(BaseModel, frozen=True):
    """
    Model for translation details returned by the CDT SSE-AT API endpoint.

    **Example response:**
    ```
    {
        "NexusModId": 49616,
        "FrenchName": "USMP - Compilation de correctifs",
        "Version": "2.6.7",
        "Filename": "usmp___compilation_de_correctifs_2.6.7_sse.7z",
        "DownloadLink": "https://www.confrerie-des-traducteurs.fr/skyrim/telechargement-se/3425?fromSseAtAPI=1",
        "LastArchiveUpdateDate": {
            "date": "2026-01-08 14:46:05.000000",
            "timezone_type": 3,
            "timezone": "Europe/Paris"
        }
    }
    ```
    """

    nexus_mods_id: int = Field(alias="NexusModId")
    """The id of the original mod at Nexus Mods."""

    name: str = Field(alias="FrenchName")
    """The name of the translation."""

    version: str = Field(alias="Version")
    """The version of the translation."""

    file_name: str = Field(alias="Filename")
    """The full name of the downloaded file."""

    download_link: str = Field(alias="DownloadLink")
    """Direct download URL to the translation."""

    timestamp: Annotated[
        int,
        BeforeValidator(
            lambda data: (
                get_unix_timestamp_from_timestamp_data(data)  # pyright: ignore[reportArgumentType]
                if isinstance(data, dict)
                else data
            )
        ),
    ] = Field(alias="LastArchiveUpdateDate")
    """The Unix timestamp of the last update of the translation."""
