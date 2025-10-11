"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from pydantic import BaseModel, Field


class NmFile(BaseModel, frozen=True):
    """
    Model for mod file objects returned by the Nexus Mods API "files" endpoint.

    **Example response:**
    ```
    {
        "id": [
            405401,
            1704
        ],
        "uid": 7318624677785,
        "file_id": 405401,
        "name": "TESL Loading Screens - German",
        "version": "v2.1.1",
        "category_id": 1,
        "category_name": "MAIN",
        "is_primary": true,
        "size": 15,
        "file_name": "TESL Loading Screens - German-73920-v2-1-1-1688886211.7z",
        "uploaded_timestamp": 1688886211,
        "uploaded_time": "2023-07-09T07:03:31.000+00:00",
        "mod_version": "v2.1.1",
        "external_virus_scan_url": "https://www.virustotal.com/gui/file/e5acb9d2f7cc5b7decc62ad5421f281c294ed27390dfa40570d7f73826e4dcba/detection/f-e5acb9d2f7cc5b7decc62ad5421f281c294ed27390dfa40570d7f73826e4dcba-1688886216",
        "description": "Die Original-Mod wird zwingend benötigt!!!",
        "size_kb": 15,
        "size_in_bytes": 15269,
        "changelog_html": null,
        "content_preview_link": "https://file-metadata.nexusmods.com/file/nexus-files-s3-meta/1704/73920/TESL Loading Screens - German-73920-v2-1-1-1688886211.7z.json"
    }
    ```
    """

    id: tuple[int, int]
    """Tuple of file id and internal game id (1704 = Skyrim SE)."""

    file_id: int
    """The file id."""

    name: str
    """The display name of the file."""

    version: str
    """The version of the file."""

    category_name: Optional[str]
    """The file category (eg. 'MAIN')."""

    is_primary: bool
    """Whether the file is the primary file."""

    size: Optional[int] = Field(alias="size_in_bytes")
    """The file size in bytes."""

    file_name: str
    """The full name of the downloaded mod file."""

    uploaded_timestamp: int
    """The UTC timestamp when the file was uploaded."""

    mod_version: str
    """The current version of the mod the file belongs to."""

    content_preview_link: str
    """URL to a JSON file containing a preview of the file's content."""

    @override
    def __hash__(self) -> int:
        return hash((self.id, self.name))
