"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import platform
from datetime import datetime

import cloudscraper as cs
import jstyleson as json
import pytz
import requests as req

from app import MainApp
from core.cacher.cacher import Cacher


class CDTApi:
    """
    Class for communication with Confrérie des Traducteurs API.
    """

    user_agent = f"\
{MainApp.name}/{MainApp.version} \
(\
{platform.system()} \
{platform.version()}; \
{platform.architecture()[0]}\
)"

    cacher: Cacher = None

    scraper: cs.CloudScraper = None

    log = logging.getLogger("CDTApi")

    def __init__(self, cacher: Cacher):
        self.cacher = cacher

    def get_mod_details(self, nm_mod_id: int) -> dict | None:
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
            return

        url = f"https://www.confrerie-des-traducteurs.fr/api/skyrim/sse-at/{nm_mod_id}"

        cached = self.cacher.get_from_web_cache(url)

        if cached is None:
            res = req.get(url, headers={"User-Agent": self.user_agent})
            self.cacher.add_to_web_cache(url, res)
        else:
            res = cached
            self.log.debug(f"Got cached API response for {url!r}.")

        if res.status_code == 200:
            data: dict = json.loads(res.content.decode())
        else:
            self.log.error(f"Request failed! Status code: {res.status_code}")
            self.log.debug(f"Request URL: {url}")
            return

        return data

    def get_modname_of_id(self, nm_mod_id: int) -> str | None:
        """
        Gets modname for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

        if mod_details is not None:
            return mod_details["FrenchName"]

    def has_translation(self, nm_mod_id: int) -> bool:
        """
        Checks if CDT has a translation for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

        return mod_details is not None

    def get_timestamp_of_file(self, nm_mod_id: int) -> int | None:
        """
        Gets upload timestamp (seconds since epoch) for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

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

    def get_modpage_link(self, nm_mod_id: int) -> str | None:
        """
        Returns modpage URL for translation for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

        if mod_details is not None:
            dl_url: str = mod_details["DownloadLink"]
            cdt_id = dl_url.rsplit("/", 2)[1]
            url = f"https://www.confrerie-des-traducteurs.fr/skyrim/mods/{cdt_id}"

            return url

    def get_download_link(self, nm_mod_id: int) -> str | None:
        """
        Returns direct download URL for translation for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

        if mod_details is not None:
            return mod_details["DownloadLink"]

    def get_filename_of_id(self, nm_mod_id: int) -> str | None:
        """
        Gets filename for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

        if mod_details is not None:
            return mod_details["Filename"]
