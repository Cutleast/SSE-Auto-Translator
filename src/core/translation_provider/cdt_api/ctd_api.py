"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import platform
from datetime import datetime
from typing import Any, Optional

import jstyleson as json
import pytz
import requests as req

from app_context import AppContext
from core.cache.cache import Cache


class CDTApi:
    """
    Class for communication with Confrérie des Traducteurs API.
    """

    user_agent: str
    cache: Cache

    log = logging.getLogger("CDTApi")

    def __init__(self, cache: Cache):
        self.cache = cache

        self.user_agent = (
            f"{AppContext.get_app_type().APP_NAME}/"
            f"{AppContext.get_app_type().APP_VERSION} "
            f"({platform.system()} {platform.version()}; "
            f"{platform.architecture()[0]})"
        )

    def get_mod_details(self, nm_mod_id: int) -> Optional[dict[str, Any]]:
        """
        Requests details for translation for `nm_mod_id`
        and returns it as `dict`.

        Example response:
        ```
        {
            "NexusModId": 24595,
            "FrenchName": "Observateurs et Veilleurs",
            "Version": "6",
            "Filename": "observateurs_et_veilleurs_6_sse.7z",
            "DownloadLink": "https://www.confrerie-des-traducteurs.fr/skyrim/telechargement_se/4228/sse?fromSseAtAPI=1",
            "LastArchiveUpdateDate": {
                "date": "2024-03-22 21:16:32.000000",
                "timezone_type": 3,
                "timezone": "Europe/Paris"
            }
        }
        ```
        """

        if not nm_mod_id:
            return None

        url = f"https://www.confrerie-des-traducteurs.fr/api/skyrim/sse-at/{nm_mod_id}"

        cached = self.cache.get_from_web_cache(url)

        if cached is None:
            res = req.get(url, headers={"User-Agent": self.user_agent})
            self.cache.add_to_web_cache(url, res)
        else:
            res = cached
            self.log.debug(f"Got cached API response for {url!r}.")

        if res.status_code == 200:
            data: dict[str, Any] = json.loads(res.content.decode())
        else:
            self.log.error(f"Request failed! Status code: {res.status_code}")
            self.log.debug(f"Request URL: {url}")
            return None

        return data

    def get_modname_of_id(self, nm_mod_id: int) -> Optional[str]:
        """
        Gets modname for `nm_mod_id`.
        """

        mod_details: Optional[dict[str, Any]] = self.get_mod_details(nm_mod_id)
        mod_name: Optional[str] = None

        if mod_details is not None:
            mod_name = mod_details["FrenchName"]

        return mod_name

    def has_translation(self, nm_mod_id: int) -> bool:
        """
        Checks if CDT has a translation for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

        return mod_details is not None

    def get_timestamp_of_file(self, nm_mod_id: int) -> Optional[int]:
        """
        Gets upload timestamp (seconds since epoch) for `nm_mod_id`.
        """

        mod_details: Optional[dict[str, Any]] = self.get_mod_details(nm_mod_id)
        timestamp: Optional[int] = None

        if mod_details is not None:
            upload_details = mod_details["LastArchiveUpdateDate"]
            date = upload_details["date"]
            timezone = upload_details["timezone"]

            date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            date_obj_utc = date_obj.replace(tzinfo=pytz.timezone(timezone)).astimezone(
                pytz.utc
            )
            timestamp = int(date_obj_utc.timestamp())

        return timestamp

    def get_modpage_link(self, nm_mod_id: int) -> Optional[str]:
        """
        Returns modpage URL for translation for `nm_mod_id`.
        """

        mod_details: Optional[dict[str, Any]] = self.get_mod_details(nm_mod_id)
        url: Optional[str] = None

        if mod_details is not None:
            dl_url: str = mod_details["DownloadLink"]
            cdt_id = dl_url.rsplit("/", 2)[1]
            url = f"https://www.confrerie-des-traducteurs.fr/skyrim/mods/{cdt_id}"

        return url

    def get_download_link(self, nm_mod_id: int) -> Optional[str]:
        """
        Returns direct download URL for translation for `nm_mod_id`.
        """

        mod_details: Optional[dict[str, Any]] = self.get_mod_details(nm_mod_id)
        url: Optional[str] = None

        if mod_details is not None:
            url = mod_details["DownloadLink"]
        else:
            raise FileNotFoundError(f"Translation for {nm_mod_id} not found!")

        return url

    def get_filename_of_id(self, nm_mod_id: int) -> Optional[str]:
        """
        Gets filename for `nm_mod_id`.
        """

        mod_details: Optional[dict[str, Any]] = self.get_mod_details(nm_mod_id)
        filename: Optional[str] = None

        if mod_details is not None:
            filename = mod_details["Filename"]

        return filename
