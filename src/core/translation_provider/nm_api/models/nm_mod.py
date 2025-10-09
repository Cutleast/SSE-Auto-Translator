"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel, Field


class NmMod(BaseModel, frozen=True):
    """
    Model for mod details returned by the Nexus Mods API "mods" endpoint.

    **Example response:**
    ```
    {
        "name": "TESL - Loading Screens - German",
        "summary": "Eine deutsche Übersetzung der Mod The Elder Scrolls Legends - Loading Screens von Jampion.",
        "description": "...",
        "picture_url": "https://staticdelivery.nexusmods.com/mods/1704/images/73920/73920-1661277111-1914574655.png",
        "mod_downloads": 1278,
        "mod_unique_downloads": 674,
        "uid": 7318624346304,
        "mod_id": 73920,
        "game_id": 1704,
        "allow_rating": true,
        "domain_name": "skyrimspecialedition",
        "category_id": 42,
        "version": "v2.1.1",
        "endorsement_count": 46,
        "created_timestamp": 1661277660,
        "created_time": "2022-08-23T18:01:00.000+00:00",
        "updated_timestamp": 1688886211,
        "updated_time": "2023-07-09T07:03:31.000+00:00",
        "author": "Cutleast",
        "uploaded_by": "Cutleast",
        "uploaded_users_profile_url": "https://nexusmods.com/users/65733731",
        "contains_adult_content": false,
        "status": "published",
        "available": true,
        "user": {
            "member_id": 65733731,
            "member_group_id": 27,
            "name": "Cutleast"
        },
        "endorsement": {
            "endorse_status": "Undecided",
            "timestamp": null,
            "version": null
        }
    }
    ```
    """

    name: str
    """The display name of the mod."""

    summary: str
    """The short description of the mod."""

    mod_id: int
    """The mod id."""

    game_id: int
    """The internal game id (1704 = Skyrim SE)."""

    version: str
    """The current version of the mod."""

    updated_timestamp: int
    """The UTC timestamp when the mod was last updated."""

    author: str
    """The author of the mod."""

    uploader: str = Field(alias="uploaded_by")
    """The uploader of the mod."""
