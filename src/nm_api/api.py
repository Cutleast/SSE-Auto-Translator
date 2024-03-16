"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import platform
import urllib.parse
from uuid import uuid4

import bs4
import cloudscraper as cs
import jstyleson as json
import requests as req
import websocket

import utilities as utils
from main import MainApp


class NexusModsApi:
    """
    Class for communication with Nexus Mods API.
    """

    api_key: str = None
    premium: bool = None
    user_agent = f"\
{MainApp.name}/{MainApp.version} \
(\
{platform.system()} \
{platform.version()}; \
{platform.architecture()[0]}\
)"

    application_slug: str = "sse-at"

    game_ids = {
        "skyrimspecialedition": 1704,
    }

    rem_hreq: int = None  # Remaining API requests at current hour
    rem_dreq: int = None  # Remaining API requests at current day

    cache: dict[str, req.Response] = {}
    """
    Cache for Web and API requests.

    `{url: response}`
    """

    scraper: cs.CloudScraper = None

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.log = logging.getLogger("NexusModsApi")

    def __repr__(self):
        return "NexusModsApi"

    def check_api_key(self):
        """
        Checks if API key is valid.
        """

        self.log.info("Checking API Key...")

        res = self.request("users/validate.json", cache_result=False)
        data: dict = json.loads(res.content.decode("utf8"))
        self.premium: bool = data.get("is_premium", False)
        api_key_valid = res.status_code == 200

        rem_hreq = res.headers.get("X-RL-Hourly-Remaining", "0")
        rem_dreq = res.headers.get("X-RL-Daily-Remaining", "0")

        if rem_hreq.isnumeric():
            self.rem_hreq = int(rem_hreq)
        if rem_dreq.isnumeric():
            self.rem_dreq = int(rem_dreq)

        self.log.info(f"API Key valid: {api_key_valid}")

        return api_key_valid

    def request(self, path: str, cache_result: bool = True):
        """
        Sends request to `path` and returns response.

        Caches result for avoiding redundant requests if `cache_result` is `True`.
        """

        url = "https://api.nexusmods.com/v1/" + path

        if url not in self.cache or not cache_result:
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

            if cache_result:
                self.cache[url] = res
            else:
                return res
        else:
            self.log.debug(f"Got cached API response for {url!r}.")

        return self.cache[url]

    def get_mod_details(self, game_id: str, mod_id: int) -> dict:
        """
        Gets mod details from `mod_id` in `game_id`.
        """

        self.log.info(f"Requesting mod info for {mod_id!r}...")
        res = self.request(f"games/{game_id}/mods/{mod_id}.json")
        data: dict = json.loads(res.content.decode("utf8"))
        self.log.info("Request successful.")

        return data

    def get_mod_files(self, game_id: str, mod_id: int) -> list[dict]:
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
            mod_files: list[dict] = json.loads(res.content.decode())["files"]
            return mod_files
        else:
            self.log.error(f"Failed to get mod files! Status code: {res.status_code}")
            return []

    def get_file_contents(self, game_id: str, mod_id: int, file_name: str):
        """
        Gets contents of `file_name` from `mod_id` in `game_id` and returns paths in a list.
        """

        game_id = self.game_ids[game_id]

        url = f"https://file-metadata.nexusmods.com/file/nexus-files-s3-meta/{game_id}/{mod_id}/{urllib.parse.quote(file_name)}.json"

        if url not in self.cache:
            res = req.get(url)
            self.cache[url] = res
        else:
            self.log.debug(f"Got cached Web response for {url!r}.")

        res = self.cache[url]

        if res.status_code == 200:
            data = res.content.decode()
            json_data: dict = json.loads(data)
            return utils.extract_file_paths(json_data)

        else:
            self.log.error(
                f"Failed to get file contents! Status code: {res.status_code}"
            )
            self.log.debug(f"Request URL: {url}")
            return

    def scan_mod_for_filename(
        self, game_id: str, mod_id: int, file_name: str
    ) -> list[int] | None:
        """
        Scans modpage for Files that contain `file_name` and returns their file ids.
        """

        self.log.debug(f"Scanning mod {mod_id} for file {file_name!r}...")

        mod_files: list[dict] = self.get_mod_files(game_id, mod_id)

        matches: list[int] = []

        # Check main files first
        for mod_file in mod_files.copy():
            if mod_file["category_name"] == "MAIN":
                mod_file_name: str = mod_file["file_name"]
                self.log.debug(f"Scanning mod file {mod_file_name!r}...")
                files = self.get_file_contents(game_id, mod_id, mod_file_name)

                if files is None:
                    self.log.debug(f"Failed to get file contents of {mod_file_name!r}!")
                    continue

                if any(
                    file.lower().strip().endswith(file_name.lower().strip())
                    or f"skse/plugins/dynamicstringdistributor/{file_name.lower().strip()}"
                    in file.lower()
                    for file in files
                ):
                    self.log.debug(f"Found {file_name!r} in file {mod_file_name!r}.")
                    matches.append(mod_file["file_id"])

                mod_files.remove(mod_file)

        if len(matches):
            return matches

        # Then check rest of files
        for mod_file in mod_files:
            mod_file_name: str = mod_file["file_name"]
            self.log.debug(f"Scanning mod file {mod_file_name!r}...")
            files = self.get_file_contents(game_id, mod_id, mod_file_name)

            if files is None:
                self.log.debug(f"Failed to get file contents of {mod_file_name!r}!")
                continue

            if any(
                file.lower().strip().endswith(file_name.lower().strip())
                for file in files
            ):
                self.log.debug(f"Found {file_name!r} in file {mod_file_name!r}.")
                matches.append(mod_file["file_id"])

        if len(matches):
            return matches[::-1]
        else:
            self.log.error(f"File {file_name!r} not found in mod {mod_id}!")
            return

    def get_modname_of_id(self, game_id: str, mod_id: int) -> str | None:
        """
        Gets modname for `mod_id`.
        """

        return self.get_mod_details(game_id, mod_id)["name"]

    def get_filename_of_id(
        self, game_id: str, mod_id: int, file_id: int, full_name: bool = False
    ) -> str | None:
        """
        Gets filename for `file_id` in `mod_id`.
        """

        mod_files = self.get_mod_files(game_id, mod_id)

        for file in mod_files:
            if file["file_id"] == file_id:
                return file["file_name"] if full_name else file["name"]

    def get_timestamp_of_file(
        self, game_id: str, mod_id: int, file_id: int
    ) -> int | None:
        """
        Gets upload timestamp (seconds since epoch) for `file_id` in `mod_id`.
        """

        mod_files = self.get_mod_files(game_id, mod_id)

        for file in mod_files:
            if file["file_id"] == file_id:
                return file["uploaded_timestamp"]

    def get_mod_translations(self, game_id: str, mod_id: int) -> dict[str, list[str]]:
        """
        Requests modpage and extracts translations from HTML code
        because official API does not include translations in its response.

        Permission granted by Pickysaurus (Nexus Mods Moderator).
        """

        if not mod_id:
            return {}

        url = f"https://www.nexusmods.com/{game_id}/mods/{mod_id}"

        if url not in self.cache:
            if self.scraper is None:
                self.scraper = cs.CloudScraper()

            headers = {
                "User-Agent": self.user_agent,
            }

            res = self.scraper.get(url, headers=headers)
            self.cache[url] = res
        else:
            self.log.debug(f"Got cached Web response for {url!r}")

        res = self.cache[url]

        if res.status_code != 200:
            self.log.error(f"Failed to scan modpage! Status Code: {res.status_code}")
            return {}

        html = res.content.decode()
        parsed = bs4.BeautifulSoup(html, features="html.parser")

        translation_list = parsed.find("ul", {"class": "translations"})
        if translation_list is None:
            return {}

        available_translations: dict[str, list[str]] = {}

        for tag in translation_list.children:
            if tag.text == "\n":
                continue

            tags = parsed.find_all("a", {"class": f"sortme flag flag-{tag.text}"})
            urls: list[str] = [tag["href"] for tag in tags]

            language = tag.text

            available_translations[language] = urls

        return available_translations

    def get_sso_key(self):
        """
        Initializes SSO process and waits for API key from server.

        Follows instructions from here: https://github.com/Nexus-Mods/sso-integration-demo
        """

        self.log.info("Starting SSO process...")

        self.log.debug("Connecting to Nexus Mods SSO webserver...")
        connection = websocket.create_connection("wss://sso.nexusmods.com")

        self.log.debug("Generating UUID v4...")
        uuid = str(uuid4())
        self.log.debug(f"UUID: {uuid}")

        self.log.debug("Requesting SSO token...")
        token: str = None
        data = {
            "id": uuid,
            "token": token,
            "protocol": 2,
        }
        connection.send(json.dumps(data).encode())

        response = connection.recv()
        if isinstance(response, bytes):
            response = response.decode()
        data = json.loads(response)
        token = data["data"]["connection_token"]

        self.log.debug("Opening page in Web Browser...")
        url = f"https://www.nexusmods.com/sso?id={uuid}&application={self.application_slug}"
        os.startfile(url)

        self.log.info("Waiting for User to sign in...")
        connection.settimeout(600)  # Timeout of 5 minutes
        response = connection.recv()
        if isinstance(response, bytes):
            response = response.decode()
        data = json.loads(response)
        api_key: str = data["data"]["api_key"]
        self.log.debug("Received API key.")

        connection.close()
        self.log.debug("Connection closed.")

        self.api_key = api_key
        self.log.info("SSO process successful.")

        return self.api_key
