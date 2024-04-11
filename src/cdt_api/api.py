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

from main import MainApp


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
    cache: dict[str, req.Response] = {}
    """
    Cache for Web and API requests.

    `{url: response}`
    """

    scraper: cs.CloudScraper = None

    log = logging.getLogger("CDTApi")

    def get_mod_details(self, nm_mod_id: int) -> dict | None:
        """
        Requests details for translation for `nm_mod_id`
        and returns it as `dict`.
        """

        self.log.info(f"Requesting translation info for mod {nm_mod_id}...")

        url = f"https://www.confrerie-des-traducteurs.fr/api/skyrim/sse-at/{nm_mod_id}"

        if url not in self.cache:
            res = req.get(url, headers={"User-Agent": self.user_agent})

            self.cache[url] = res
        else:
            res = self.cache[url]

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

    def get_download_link(self, nm_mod_id: int) -> str | None:
        """
        Returns direct download URL for translation for `nm_mod_id`.
        """

        mod_details = self.get_mod_details(nm_mod_id)

        if mod_details is not None:
            return mod_details["DownloadLink"]
