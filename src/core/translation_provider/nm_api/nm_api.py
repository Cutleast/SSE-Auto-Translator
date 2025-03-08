"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import platform
import urllib.parse
from queue import Queue
from typing import Any, Optional
from uuid import uuid4

import bs4
import cloudscraper as cs
import jstyleson as json
import requests as req
import websocket

from app_context import AppContext
from core.cache.cache import Cache
from core.utilities.exceptions import (
    ApiException,
    ApiExpiredError,
    ApiInvalidServerError,
    ApiKeyInvalidError,
    ApiLimitReachedError,
    ApiPermissionError,
)
from core.utilities.filesystem import extract_file_paths
from core.utilities.path import Path

from .nxm_handler import NXMHandler


class NexusModsApi:
    """
    Class for communication with Nexus Mods API.

    TODO: Improve handling of errors caused by Nexus Mods
    """

    api_key: str
    premium: bool
    user_agent: str

    application_slug: str = "sse-at"

    game_ids: dict[str, int] = {
        "skyrimspecialedition": 1704,
    }
    language_overrides = {
        "Mandarin": "Chinese",
    }
    """
    Map for languages that are named differently on the Nexus Mods site.
    """

    rem_hreq: int = 0  # Remaining API requests at current hour
    rem_dreq: int = 0  # Remaining API requests at current day

    cache: Cache
    nxm_handler: NXMHandler

    scraper: Optional[cs.CloudScraper] = None

    log: logging.Logger = logging.getLogger("NexusModsAPI")

    def __init__(self, cache: Cache, api_key: str):
        self.cache = cache
        self.api_key = api_key

        self.user_agent = (
            f"{AppContext.get_app_type().APP_NAME}/"
            f"{AppContext.get_app_type().APP_VERSION} "
            f"({platform.system()} {platform.version()}; "
            f"{platform.architecture()[0]})"
        )

        AppContext.get_app().ready_signal.connect(self.__post_init)

    def __post_init(self) -> None:
        self.nxm_handler = AppContext.get_app().nxm_listener

    def check_api_key(self) -> bool:
        """
        Checks if API key is valid.
        """

        self.log.info("Checking API Key...")

        res = self.request("users/validate.json", cache_result=False)
        data: dict[str, Any] = json.loads(res.content.decode("utf8"))
        self.premium: bool = data.get("is_premium", False)
        api_key_valid: bool = res.status_code == 200

        rem_hreq = res.headers.get("X-RL-Hourly-Remaining", "0")
        rem_dreq = res.headers.get("X-RL-Daily-Remaining", "0")

        if rem_hreq.isnumeric():
            self.rem_hreq = int(rem_hreq)
        if rem_dreq.isnumeric():
            self.rem_dreq = int(rem_dreq)

        self.log.info(f"API Key valid: {api_key_valid}")

        return api_key_valid

    @staticmethod
    def is_api_key_valid(api_key: str) -> bool:
        """
        Checks if an API key is valid.

        Args:
            api_key (str): The API key to check.

        Returns:
            bool: Whether the API key is valid.
        """

        url = "https://api.nexusmods.com/v1/users/validate.json"
        user_agent = (
            f"{AppContext.get_app_type().APP_NAME}/"
            f"{AppContext.get_app_type().APP_VERSION} "
            f"({platform.system()} {platform.version()}; "
            f"{platform.architecture()[0]})"
        )
        headers = {
            "accept": "application/json",
            "apikey": api_key,
            "User-Agent": user_agent,
        }

        NexusModsApi.log.debug(f"Sending API request to {url!r}...")
        res = req.get(url, headers=headers)
        NexusModsApi.log.debug(f"Status Code: {res.status_code}")

        api_key_valid: bool = res.status_code == 200

        return api_key_valid

    def request(self, path: str, cache_result: bool = True) -> req.Response:
        """
        Sends request to `path` and returns response.

        Caches result for avoiding redundant requests if `cache_result` is `True`.
        """

        url = "https://api.nexusmods.com/v1/" + path

        if cache_result:
            cached = self.cache.get_from_web_cache(url)
        else:
            cached = None

        if cached is None or not cache_result:
            headers = {
                "accept": "application/json",
                "apikey": self.api_key,
                "User-Agent": self.user_agent,
            }

            self.log.debug(f"Sending API request to {url!r}...")
            res = req.get(url, headers=headers)
            self.log.debug(f"Status Code: {res.status_code}")

            rem_hreq = res.headers.get("X-RL-Hourly-Remaining", "0")
            rem_dreq = res.headers.get("X-RL-Daily-Remaining", "0")

            if rem_hreq.isnumeric():
                self.rem_hreq = int(rem_hreq)
            if rem_dreq.isnumeric():
                self.rem_dreq = int(rem_dreq)

            if res.status_code == 429:
                self.log.warning("API rate limit reached!")
                raise ApiLimitReachedError

            if cache_result:
                self.cache.add_to_web_cache(url, res)

            return res
        else:
            self.log.debug(f"Got cached API response for {url!r}.")

        return cached

    def get_mod_details(self, game_id: str, mod_id: int) -> Optional[dict[str, Any]]:
        """
        Gets mod details from `mod_id` in `game_id`.

        Example response:
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
            "allow_rating": True,
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
            "contains_adult_content": False,
            "status": "published",
            "available": True,
            "user": {
                "member_id": 65733731,
                "member_group_id": 27,
                "name": "Cutleast"
            },
            "endorsement": {
                "endorse_status": "Undecided",
                "timestamp": None,
                "version": None
            }
        }
        ```
        """

        if not mod_id:
            return None

        self.log.info(f"Requesting mod info for {mod_id!r}...")
        res = self.request(f"games/{game_id}/mods/{mod_id}.json")
        data: dict[str, Any] = json.loads(res.content.decode("utf8"))
        self.log.info("Request successful.")

        return data

    def get_mod_files(self, game_id: str, mod_id: int) -> list[dict[str, Any]]:
        """
        Requests a list of files a mod has at Nexus Mods.
        """

        categories = [
            "main",
            "update",
            "optional",
            "miscellaneous",
        ]
        category_filter = ",".join(categories)

        path = f"games/{game_id}/mods/{mod_id}/files.json?category={category_filter}"
        res = self.request(path)

        if res.status_code == 200:
            mod_files: list[dict[str, Any]] = json.loads(res.content.decode())["files"]
            return mod_files
        else:
            self.log.error(f"Failed to get mod files! Status code: {res.status_code}")
            return []

    def get_file_details(
        self, game_id: str, mod_id: int, file_id: int
    ) -> Optional[dict[str, Any]]:
        """
        Returns file details for `file_id` at `mod_id`.

        Example response:
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
            "is_primary": True,
            "size": 15,
            "file_name": "TESL Loading Screens - German-73920-v2-1-1-1688886211.7z",
            "uploaded_timestamp": 1688886211,
            "uploaded_time": "2023-07-09T07:03:31.000+00:00",
            "mod_version": "v2.1.1",
            "external_virus_scan_url": "https://www.virustotal.com/gui/file/e5acb9d2f7cc5b7decc62ad5421f281c294ed27390dfa40570d7f73826e4dcba/detection/f-e5acb9d2f7cc5b7decc62ad5421f281c294ed27390dfa40570d7f73826e4dcba-1688886216",
            "description": "Die Original-Mod wird zwingend benötigt!!!",
            "size_kb": 15,
            "size_in_bytes": 15269,
            "changelog_html": None,
            "content_preview_link": "https://file-metadata.nexusmods.com/file/nexus-files-s3-meta/1704/73920/TESL Loading Screens - German-73920-v2-1-1-1688886211.7z.json"
        }
        ```
        """

        if not mod_id or not file_id:
            return None

        path = f"/games/{game_id}/mods/{mod_id}/files/{file_id}.json"
        res = self.request(path)

        if res.status_code == 200:
            details: dict[str, Any] = json.loads(res.content.decode())
            return details
        else:
            self.log.error(
                f"Failed to get details for mod file! Status code: {res.status_code}"
            )
            raise ApiException

    def get_file_contents(
        self, game_id: str, mod_id: int, file_name: str
    ) -> Optional[list[str]]:
        """
        Gets contents of `file_name` from `mod_id` in `game_id` and returns paths in a list.
        """

        _game_id = self.game_ids[game_id]

        url = f"https://file-metadata.nexusmods.com/file/nexus-files-s3-meta/{_game_id}/{mod_id}/{urllib.parse.quote(file_name)}.json"

        cached = self.cache.get_from_web_cache(url)

        if cached is None:
            res = req.get(url)
            self.cache.add_to_web_cache(url, res)
        else:
            res = cached
            self.log.debug(f"Got cached Web response for {url!r}.")

        if res.status_code == 200:
            data = res.content.decode()
            json_data: dict[str, Any] = json.loads(data)
            return extract_file_paths(json_data)

        else:
            self.log.error(
                f"Failed to get file contents! Status code: {res.status_code}"
            )
            self.log.debug(f"Request URL: {url}")
            return None

    def scan_mod_for_filename(
        self, game_id: str, mod_id: int, file_name: str
    ) -> Optional[list[int]]:
        """
        Scans modpage for Files that contain `file_name` and returns their file ids.
        """

        self.log.debug(f"Scanning mod {mod_id} for file {file_name!r}...")

        mod_files: list[dict[str, Any]] = self.get_mod_files(game_id, mod_id)

        matches: list[int] = []

        # Check main files first
        mod_file_name: str
        for mod_file in mod_files.copy():
            if mod_file["category_name"] == "MAIN":
                mod_file_name = mod_file["file_name"]
                self.log.debug(f"Scanning mod file {mod_file_name!r}...")
                files = self.get_file_contents(game_id, mod_id, mod_file_name)

                if files is None:
                    self.log.debug(f"Failed to get file contents of {mod_file_name!r}!")
                    continue

                if any(
                    file.lower().strip().endswith(file_name.lower().strip())
                    or (
                        f"skse/plugins/dynamicstringdistributor/{file_name.lower().strip()}"
                        in file.lower()
                    )
                    for file in files
                ):
                    self.log.debug(f"Found {file_name!r} in file {mod_file_name!r}.")
                    matches.append(mod_file["file_id"])

                mod_files.remove(mod_file)

        if len(matches):
            return matches

        # Then check rest of files
        for mod_file in mod_files:
            mod_file_name = mod_file["file_name"]
            self.log.debug(f"Scanning mod file {mod_file_name!r}...")
            files = self.get_file_contents(game_id, mod_id, mod_file_name)

            if files is None:
                self.log.debug(f"Failed to get file contents of {mod_file_name!r}!")
                continue

            if any(
                file.lower().strip().endswith(file_name.lower().strip())
                or (
                    f"skse/plugins/dynamicstringdistributor/{file_name.lower().strip()}"
                    in file.lower()
                )
                for file in files
            ):
                self.log.debug(f"Found {file_name!r} in file {mod_file_name!r}.")
                matches.append(mod_file["file_id"])

        if len(matches):
            return matches[::-1]
        else:
            self.log.error(f"File {file_name!r} not found in mod {mod_id}!")
            return None

    def get_modname_of_id(self, game_id: str, mod_id: int) -> Optional[str]:
        """
        Gets modname for `mod_id`.
        """

        modname: Optional[str] = None
        mod_details: Optional[dict[str, Any]] = self.get_mod_details(game_id, mod_id)

        if mod_details is not None:
            modname = mod_details["name"]

        return modname

    def get_filename_of_id(
        self, game_id: str, mod_id: int, file_id: int, full_name: bool = False
    ) -> Optional[str]:
        """
        Gets filename for `file_id` in `mod_id`.
        """

        mod_files = self.get_mod_files(game_id, mod_id)
        file_name: Optional[str] = None

        for file in mod_files:
            if file["file_id"] == file_id:
                file_name = file["file_name"] if full_name else file["name"]
                break

        return file_name

    def get_timestamp_of_file(
        self, game_id: str, mod_id: int, file_id: int
    ) -> Optional[int]:
        """
        Gets upload timestamp (seconds since epoch) for `file_id` in `mod_id`.
        """

        mod_files = self.get_mod_files(game_id, mod_id)
        timestamp: Optional[int] = None

        for file in mod_files:
            if file["file_id"] == file_id:
                timestamp = file["uploaded_timestamp"]
                break

        return timestamp

    def get_mod_translations(self, game_id: str, mod_id: int) -> dict[str, list[str]]:
        """
        Requests modpage and extracts translations from HTML code
        because official API does not include translations in its response.

        Permission granted by Pickysaurus (Nexus Mods Moderator).
        """

        if not mod_id:
            return {}

        url = f"https://www.nexusmods.com/{game_id}/mods/{mod_id}"

        cached = self.cache.get_from_web_cache(url)

        if cached is None:
            if self.scraper is None:
                self.scraper = cs.CloudScraper()

            headers = {
                "User-Agent": self.user_agent,
            }

            res = self.scraper.get(url, headers=headers)
            self.cache.add_to_web_cache(url, res)
        else:
            res = cached
            self.log.debug(f"Got cached Web response for {url!r}")

        if res.status_code != 200:
            self.log.error(f"Failed to scan modpage! Status Code: {res.status_code}")
            return {}

        html = res.content.decode(errors="replace")
        parsed = bs4.BeautifulSoup(html, features="html.parser")

        translation_list = parsed.find("ul", {"class": "translations"})
        if translation_list is None:
            return {}

        available_translations: dict[str, list[str]] = {}

        for tag in translation_list.children:  # type: ignore[attr-defined]
            if tag.text == "\n":
                continue

            tags = parsed.find_all("a", {"class": f"sortme flag flag-{tag.text}"})
            urls: list[str] = [tag["href"] for tag in tags]  # type: ignore[misc,index]

            language = NexusModsApi.language_overrides.get(tag.text, tag.text)

            available_translations[language] = urls

        return available_translations

    def get_sso_key(self) -> str:
        """
        Initializes SSO process and waits for API key from server.

        Follows instructions from here: https://github.com/Nexus-Mods/sso-integration-demo
        """

        res_data: dict[str, Any]

        self.log.info("Starting SSO process...")

        self.log.debug("Connecting to Nexus Mods SSO webserver...")
        connection = websocket.create_connection("wss://sso.nexusmods.com")

        self.log.debug("Generating UUID v4...")
        uuid = str(uuid4())
        self.log.debug(f"UUID: {uuid}")

        self.log.debug("Requesting SSO token...")
        request_data = {
            "id": uuid,
            "token": None,
            "protocol": 2,
        }
        connection.send(json.dumps(request_data).encode())

        response = connection.recv()
        if isinstance(response, bytes):
            response = response.decode()
        res_data = json.loads(response)
        token: str = res_data["data"]["connection_token"]  # type: ignore  # noqa: F841

        self.log.debug("Opening page in Web Browser...")
        url = f"https://www.nexusmods.com/sso?id={uuid}&application={self.application_slug}"
        os.startfile(url)

        self.log.info("Waiting for User to sign in...")
        connection.settimeout(600)  # Timeout of 5 minutes
        response = connection.recv()
        if isinstance(response, bytes):
            response = response.decode()
        res_data = json.loads(response)
        api_key: str = res_data["data"]["api_key"]
        self.log.debug("Received API key.")

        connection.close()
        self.log.debug("Connection closed.")

        self.api_key = api_key
        self.log.info("SSO process successful.")

        return self.api_key

    def get_mod_updates(self, game_id: str, mod_id: int) -> dict[int, int]:
        """
        Gets mod updates from `mod_id` at `game_id`.

        Returns {old_file_id: new_file_id}.
        """

        self.log.info(f"Requesting mod updates for {mod_id!r}...")
        res = self.request(f"games/{game_id}/mods/{mod_id}/files.json")
        data: dict[str, Any] = json.loads(res.content.decode("utf8"))
        updates: list[dict[str, Any]] = data["file_updates"]
        self.log.info("Request successful.")

        return {update["old_file_id"]: update["new_file_id"] for update in updates}

    def __get_premium_download_url(
        self, game_id: str, mod_id: int, file_id: int, server_id: str = "Nexus CDN"
    ) -> str:
        """
        Generates premium download URL for `file_id` from `mod_id`.
        Uses `server` if specified.
        """

        path = f"games/{game_id}/mods/{mod_id}/files/{file_id}/download_link.json"

        res = self.request(path, cache_result=False)

        match res.status_code:
            case 200:
                data: list[dict[str, str]] = json.loads(res.content.decode())

                for url_data in data:
                    if url_data["short_name"].lower() == server_id.lower():
                        return url_data["URI"]

                # Handle errors
                else:
                    raise ApiInvalidServerError
            case 400:
                raise ApiKeyInvalidError
            case 403:
                raise ApiPermissionError
            case 404:
                raise FileNotFoundError
            case 410:
                raise ApiExpiredError
            case _:
                raise ApiException

    def __get_free_download_url(
        self, game_id: str, mod_id: int, file_id: int, key: str, expires: int
    ) -> str:
        """
        Generates non-premium download URL for `file_id` from `mod_id`
        by using `key` and `expires`.
        """

        path = f"games/{game_id}/mods/{mod_id}/files/{file_id}/download_link.json"
        path += f"?key={key}&expires={expires}"

        res = self.request(path, cache_result=False)

        match res.status_code:
            case 200:
                data: list[dict[str, str]] = json.loads(res.content.decode())

                for url_data in data:
                    return url_data["URI"]
                else:
                    print(data)
                    raise ApiException("No server in response!")

            case 400:
                raise ApiKeyInvalidError
            case 403:
                raise ApiPermissionError
            case 404:
                raise FileNotFoundError
            case 410:
                raise ApiExpiredError
            case _:
                raise ApiException

    def request_download(self, game_id: str, mod_id: int, file_id: int) -> str:
        """
        Requests direct download url for a mod file from Nexus Mods.
        Waits for a Mod Manager download if the user has no Premium
        so make sure that the user is able to start it.

        Args:
            game_id (str): Subdomain for game, normally "skyrimspecialedition"
            mod_id (int): ID of mod with file.
            file_id (int): ID of mod file to download.

        Returns:
            str: Download URL
        """

        if self.premium:
            self.log.info("Starting premium download...")

            url = self.__get_premium_download_url(game_id, mod_id, file_id)

        else:
            self.log.info("Waiting for non-premium download...")

            # Use a queue to get the download details in a thread-safe way
            queue: Queue[dict[str, Any]] = Queue(1)

            def process_url(url: str) -> None:
                download_details: dict[str, Any] = NexusModsApi.parse_nxm_url(url)

                if (
                    download_details["mod_id"] == mod_id
                    and download_details["file_id"] == file_id
                    and download_details["game"] == game_id
                ):
                    queue.put(download_details)

            self.nxm_handler.request_signal.connect(process_url)
            download_details: dict[str, Any] = queue.get()
            self.nxm_handler.request_signal.disconnect(process_url)

            key: str = download_details["key"]
            expires: int = download_details["expires"]

            url = self.__get_free_download_url(game_id, mod_id, file_id, key, expires)
            queue.task_done()

            self.log.info("Got non-premium download.")

        return url

    @staticmethod
    def create_nexus_mods_url(
        game_id: str,
        mod_id: int,
        file_id: Optional[int] = None,
        mod_manager: bool = False,
    ) -> str:
        """
        Creates URL to Nexus Mods page of `mod_id` in `game_id` nexus.

        `file_id` is optional and can be used to link directly to a file.
        """

        base_url = "https://www.nexusmods.com"

        if file_id is None:
            url = f"{base_url}/{game_id}/mods/{mod_id}"
        else:
            url = f"{base_url}/{game_id}/mods/{mod_id}?tab=files&file_id={file_id}"
            if mod_manager:
                url += "&nmm=1"

        return url

    @staticmethod
    def parse_nxm_url(url: str) -> dict[str, int | str]:
        """
        Parses an NXM Mod Manager Download URL.

        Args:
            url (str): NXM Download URL to parse.

        Returns:
            dict[str, int]:
                Download details (mod id, file id, key, expires and user id).
        """

        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)  # type: ignore

        path_parts = Path(path).parts
        game: str = netloc
        mod_id = int(path_parts[2])
        file_id = int(path_parts[4])

        parsed_query: dict[str, list[str]] = urllib.parse.parse_qs(query)

        key: str = parsed_query["key"][0]
        expires = int(parsed_query["expires"][0])
        user_id = int(parsed_query["user_id"][0])

        return {
            "game": game,
            "mod_id": mod_id,
            "file_id": file_id,
            "key": key,
            "expires": expires,
            "user_id": user_id,
        }
