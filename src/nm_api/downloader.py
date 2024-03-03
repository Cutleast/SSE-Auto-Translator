"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import urllib.parse
from pathlib import Path

import jstyleson as json

import utilities as utils

from .api import NexusModsApi
from .download import Download


class Downloader:
    """
    Class for downloading files from Nexus Mods.
    """

    api: NexusModsApi = None
    game_id: str = None
    server_id: str = None

    downloads: list["Download"] = None

    def __init__(self, api: NexusModsApi, game_id: str, server_id: str = "Nexus CDN"):
        self.api = api
        self.game_id = game_id
        self.server_id = server_id

        self.log = logging.getLogger("Downloader")

    def __repr__(self):
        return "Downloader"

    def get_premium_download_url(self, mod_id: int, file_id: int):
        """
        Generates premium download URL for `file_id` from `mod_id`.
        Uses `server` if specified.
        """

        path = f"games/{self.game_id}/mods/{mod_id}/files/{file_id}/download_link.json"

        res = self.api.request(path)

        match res.status_code:
            case 200:
                data: list[dict[str, str]] = json.loads(res.content.decode())

                for url_data in data:
                    if url_data["short_name"].lower() == self.server_id.lower():
                        return url_data["URI"]

                # Handle errors
                else:
                    raise utils.ApiInvalidServerError
            case 400:
                raise utils.ApiKeyInvalidError
            case 403:
                raise utils.ApiPermissionError
            case 404:
                raise FileNotFoundError
            case 410:
                raise utils.ApiExpiredError
            case _:
                raise utils.ApiException

    def get_download_url(self, mod_id: int, file_id: int, key: str, expires: int):
        """
        Generates non-premium download URL for `file_id` from `mod_id`
        by using `key` and `expires`.
        """

        path = f"games/{self.game_id}/mods/{mod_id}/files/{file_id}/download_link.json"
        path += f"?key={key}&expires={expires}"

        res = self.api.request(path)

        match res.status_code:
            case 200:
                data: list[dict[str, str]] = json.loads(res.content.decode())

                for url_data in data:
                    return url_data["URI"]
                else:
                    print(data)
                    raise utils.ApiException("No server in response!")

            case 400:
                raise utils.ApiKeyInvalidError
            case 403:
                raise utils.ApiPermissionError
            case 404:
                raise FileNotFoundError
            case 410:
                raise utils.ApiExpiredError
            case _:
                raise utils.ApiException

    def download_file(
        self,
        mod_id: int,
        file_id: int,
        dl_path: Path,
        key: str = None,
        expires: int = None,
    ):
        """
        Downloads `file_id` from `mod_id`.
        """

        if self.api.premium:
            self.log.info(f"Starting premium download...")

            url = self.get_premium_download_url(mod_id, file_id)

            filename = urllib.parse.urlparse(url).path
            filename = urllib.parse.unquote(filename)
            filename = os.path.basename(filename)
            dl_path = dl_path / filename

            return Download(url, dl_path)
        else:
            if key is None or expires is None:
                raise utils.ApiException("Key and/or expires timestamp is/are missing!")

            self.log.info(f"Starting non-premium download...")

            url = self.get_download_url(mod_id, file_id, key, expires)

            filename = urllib.parse.urlparse(url).path
            filename = urllib.parse.unquote(filename)
            filename = os.path.basename(filename)
            dl_path = dl_path / filename

            return Download(url, dl_path)
