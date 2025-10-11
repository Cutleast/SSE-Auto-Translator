"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import re
import urllib.parse
import webbrowser
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from queue import Queue
from typing import Any, Optional, TypeVar, override
from uuid import uuid4

import bs4
import cloudscraper as cs
import jstyleson as json
import requests as req
import websocket
from cutleast_core_lib.core.cache.cache import Cache
from pydantic import BaseModel, ValidationError

from core.translation_provider.source import Source
from core.utilities.filesystem import extract_file_paths
from core.utilities.web_utils import get_url_identifier

from ..exceptions import (
    ApiInvalidServerError,
    ApiNoServerAvailableError,
    UnexpectedResponseError,
)
from ..mod_details import ModDetails
from ..mod_id import ModId
from ..provider_api import ProviderApi
from .models.file_update import FileUpdate
from .models.nm_file import NmFile
from .models.nm_files import NmFiles
from .models.nm_mod import NmMod
from .nxm_handler import NXMHandler
from .nxm_request import NxmRequest

M = TypeVar("M", bound=BaseModel)


class NexusModsApi(ProviderApi):
    """
    Class for communication with Nexus Mods API.
    """

    APP_SLUG: str = "sse-at"
    """Slug of the application used for the Single-Sign-On (SSO) flow."""

    GAME_IDS: dict[str, int] = {
        "skyrimspecialedition": 1704,
    }
    """Map of Nexus Mods game IDs."""

    LANG_OVERRIDES: dict[str, str] = {
        "Mandarin": "Chinese",
    }
    """Map for languages that are named differently on the Nexus Mods site."""

    MODPAGE_URL_PATTERN: re.Pattern[str] = re.compile(
        r"https://www\.nexusmods\.com/([a-z]+)/mods/([0-9]+)(?:\?tab=files&file_id=([0-9]+))?"
    )
    """
    Regex pattern for capturing, game id, mod id and file id from
    a Nexus Mods modpage url.
    """

    __api_key: Optional[str] = None
    """The user-specific API key used for most API requests."""

    __premium: bool = False
    """Whether the user has Nexus Mods premium or not."""

    __rem_hreq: int = 0
    """Remaining API requests at current hour"""

    __rem_dreq: int = 0
    """Remaining API requests at current day"""

    __scraper: Optional[cs.CloudScraper] = None
    """
    Scraper for circumventing Cloudflare protection when scraping the HTML of a
    modpage for translations.
    """

    def set_api_key(self, key: str) -> None:
        """
        Sets API key and checks it.

        Args:
            key (str): API key

        Raises:
            ValueError: when the API key is invalid
        """

        self.log.info("Checking API Key...")

        api_key_valid: bool
        premium: bool
        api_key_valid, premium = self.__validate_api_key(key)

        self.log.info(f"API Key valid: {api_key_valid}")

        if not api_key_valid:
            raise ValueError("Invalid API Key!")

        self.__api_key = key
        self.__premium = premium

    def __validate_api_key(self, key: str) -> tuple[bool, bool]:
        url = "https://api.nexusmods.com/v1/users/validate.json"
        headers = {
            "accept": "application/json",
            "apikey": key,
            "User-Agent": self.user_agent,
        }

        self.log.debug(f"Sending API request to {url!r}...")
        res: req.Response = self._request(
            url, headers=headers, handle_status_code=False
        )
        self.log.debug(f"Status Code: {res.status_code}")

        api_key_valid: bool = res.status_code == 200
        premium: bool = False
        if api_key_valid:
            data: dict[str, Any] = json.loads(res.content.decode("utf8"))
            premium = data.get("is_premium", False)
        else:
            self.log.error("Response has non-200 status code!")
            self.log.debug(f"Response content: {res.content}")

        return api_key_valid, premium

    @override
    def is_api_key_valid(self, key: str) -> bool:
        return self.__validate_api_key(key)[0]

    @override
    def _request(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        handle_status_code: bool = True,
    ) -> req.Response:
        res: req.Response = super()._request(url, headers, handle_status_code)

        rem_hreq: Optional[str] = res.headers.get("X-RL-Hourly-Remaining", None)
        rem_dreq: Optional[str] = res.headers.get("X-RL-Daily-Remaining", None)

        if rem_hreq is not None and rem_hreq.isnumeric():
            self.__rem_hreq = int(rem_hreq)
        if rem_dreq is not None and rem_dreq.isnumeric():
            self.__rem_dreq = int(rem_dreq)

        return res

    def __request(self, path: str, cache_result: bool = True) -> req.Response:
        """
        Sends request to `path` and returns response.

        Caches result for avoiding redundant requests if `cache_result` is `True`.
        """

        url = "https://api.nexusmods.com/v1/" + path

        if self.__api_key is None:
            raise ValueError("API Key not set!")

        headers: dict[str, str] = {
            "accept": "application/json",
            "apikey": self.__api_key,
            "User-Agent": self.user_agent,
        }

        if cache_result:
            return self._cached_request(url, headers)

        return self._request(url, headers)

    def __request_with_model(
        self, path: str, model: type[M], cache_result: bool = True
    ) -> M:
        """
        Sends a request to a given path and attempts to deserialize the response to a
        given model.

        Args:
            path (str): Path to the API endpoint, relative to the base URL.
            model (type[M]): Model to deserialize the response to.
            cache_result (bool, optional): Whether to cache the result. Defaults to True.

        Raises:
            UnexpectedResponseError: If the response failed to deserialize to the model.

        Returns:
            M: Deserialized response.
        """

        res: req.Response = self.__request(path, cache_result)

        try:
            return model.model_validate_json(res.content, by_alias=True)
        except ValidationError as ex:
            raise UnexpectedResponseError(path, res.content.decode()) from ex

    @override
    def is_direct_download_possible(self) -> bool:
        return self.__premium

    @override
    def get_remaining_requests(self) -> tuple[int, int]:
        return (self.__rem_hreq, self.__rem_dreq)

    @override
    def get_mod_details(self, mod_id: ModId) -> ModDetails:
        mod_details: ModDetails
        if mod_id.file_id:
            file: NmFile = self.__request_file(mod_id)

            mod_details = ModDetails(
                display_name=file.name,
                version=file.version,
                file_name=file.file_name,
                mod_id=mod_id,
                timestamp=file.uploaded_timestamp,
                author=None,
                uploader=None,
                modpage_url=NexusModsApi.create_nexus_mods_url(
                    game_id=mod_id.nm_game_id,
                    mod_id=mod_id.mod_id,
                    file_id=mod_id.file_id,
                ),
            )

        else:
            mod: NmMod = self.__request_mod_details(mod_id)

            mod_details = ModDetails(
                display_name=mod.name,
                version=mod.version,
                file_name="",
                mod_id=mod_id,
                timestamp=mod.updated_timestamp,
                author=mod.author,
                uploader=mod.uploader,
                modpage_url=NexusModsApi.create_nexus_mods_url(
                    game_id=mod_id.nm_game_id,
                    mod_id=mod_id.mod_id,
                    file_id=mod_id.file_id,
                ),
            )

        return mod_details

    def __request_file(self, mod_id: ModId) -> NmFile:
        if not mod_id.mod_id or not mod_id.file_id:
            ProviderApi.raise_mod_not_found_error(mod_id)

        self.log.info(f"Requesting file info for {mod_id.mod_id} > {mod_id.file_id}...")
        files: NmFiles = self.__request_mod_files(mod_id.nm_game_id, mod_id.mod_id)
        files_by_id: dict[int, NmFile] = {f.file_id: f for f in files.files}

        if mod_id.file_id not in files_by_id:
            ProviderApi.raise_mod_not_found_error(mod_id)

        return files_by_id[mod_id.file_id]

    def __request_mod_details(self, mod_id: ModId) -> NmMod:
        if not mod_id.mod_id:
            ProviderApi.raise_mod_not_found_error(mod_id)

        self.log.info(f"Requesting mod info for {mod_id.mod_id}...")
        path: str = f"games/{mod_id.nm_game_id}/mods/{mod_id.mod_id}.json"

        return self.__request_with_model(path, NmMod)

    @override
    def get_modpage_url(self, mod_id: ModId) -> str:
        return NexusModsApi.create_nexus_mods_url(
            game_id=mod_id.nm_game_id, mod_id=mod_id.mod_id
        )

    @override
    def get_translations(
        self, mod_id: ModId, file_name: str, language: str
    ) -> list[ModId]:
        translation_mod_ids: list[int] = self.__scrape_mod_translations(
            game_id=mod_id.nm_game_id, mod_id=mod_id.mod_id, language=language
        )

        translations: list[ModId] = []
        for translation_mod_id in translation_mod_ids:
            translation_files: list[int] = self.__scan_mod_for_filename(
                game_id=mod_id.nm_game_id,
                mod_id=translation_mod_id,
                file_name=file_name,
            )

            translations += [
                ModId(
                    mod_id=translation_mod_id,
                    file_id=file_id,
                    nm_id=translation_mod_id,
                    nm_game_id=mod_id.nm_game_id,
                )
                for file_id in translation_files
            ]

        self.__sort_available_translations(translations, mod_id)

        return translations

    def __sort_available_translations(
        self, available_translations: list[ModId], original_mod_id: ModId
    ) -> None:
        """
        Sorts the available translations after their relevance (and potential
        compatibility) to the installed original mod.

        Translation relevance is determined by the following factors in this order:
        1. File has the "same" age as the installed mod (newer than the installed
        original but older than the original's updates (if any)).
        2. File upload timestamp (newer first).

        Args:
            available_translations (list[ModId]): List of available translations.
            original_mod_id (ModId): Mod identifier of the installed original mod.
        """

        original_mod_timestamp: int = self.get_mod_details(original_mod_id).timestamp

        # sort translations ascending after their timestamp difference to the original
        # mod timestamp or their upload timestamp if they're older than the original mod
        available_translations.sort(
            key=lambda mod_id: self.__get_sort_key(
                self.get_mod_details(mod_id).timestamp, original_mod_timestamp
            ),
            reverse=True,
        )

        self.log.debug(
            f"Sorted {len(available_translations)} translations after their potential "
            "relevance."
        )

    @staticmethod
    def __get_sort_key(
        translation_timestamp: int, original_mod_timestamp: int
    ) -> tuple[bool, int]:
        """
        Calculates a sort key for a translation.

        Args:
            translation_timestamp (int): Timestamp of the translation.
            original_mod_timestamp (int): Timestamp of the original mod.

        Returns:
            tuple[bool, int]: Sort key
        """

        return (translation_timestamp > original_mod_timestamp, translation_timestamp)

    @override
    def is_update_available(self, mod_id: ModId, timestamp: int) -> bool:
        files: NmFiles = self.__request_mod_files(
            game_id=mod_id.nm_game_id, mod_id=mod_id.mod_id
        )
        updates: dict[int, int] = NexusModsApi.__map_file_updates(files.updates)

        return mod_id.file_id in updates

    @staticmethod
    def __map_file_updates(updates: list[FileUpdate]) -> dict[int, int]:
        return {update.old_file_id: update.new_file_id for update in updates}

    def __request_mod_files(self, game_id: str, mod_id: int) -> NmFiles:
        """
        Requests a list of files a mod has at Nexus Mods.
        """

        path = f"games/{game_id}/mods/{mod_id}/files.json?category=main%2Cupdate%2Coptional%2Cold_version%2Cmiscellaneous"
        return self.__request_with_model(path, NmFiles)

    def __get_file_contents(
        self, game_id: str, mod_id: int, file_name: str
    ) -> Optional[list[str]]:
        """
        Gets contents of `file_name` from `mod_id` in `game_id` and returns paths in a list.
        """

        _game_id = self.GAME_IDS[game_id]

        url = f"https://file-metadata.nexusmods.com/file/nexus-files-s3-meta/{_game_id}/{mod_id}/{urllib.parse.quote(file_name)}.json"

        try:
            res: req.Response = self._cached_request(url)
            return extract_file_paths(res.json())
        except Exception as ex:
            self.log.error(f"Failed to get file contents: {ex}", exc_info=ex)
            self.log.debug(f"Request URL: {url}")
            return None

    def __scan_mod_for_filename(
        self, game_id: str, mod_id: int, file_name: str
    ) -> list[int]:
        """
        Scans modpage for Files that contain `file_name` and returns their file ids.
        """

        self.log.debug(f"Scanning mod {mod_id} for file {file_name!r}...")

        mod_files: NmFiles = self.__request_mod_files(game_id, mod_id)

        file_contents: dict[NmFile, list[str]] = {}
        with ThreadPoolExecutor(thread_name_prefix="NexusModsApiThread") as executor:
            futures: dict[Future[Optional[list[str]]], NmFile] = {}
            for mod_file in mod_files.files:
                if mod_file.category_name is None:
                    self.log.debug(
                        f"Skipped file without category: '{mod_file.file_name}'"
                    )
                    continue

                futures[
                    executor.submit(
                        self.__get_file_contents, game_id, mod_id, mod_file.file_name
                    )
                ] = mod_file

            for future in as_completed(futures):
                mod_file: NmFile = futures[future]
                result: Optional[list[str]] = future.result()
                if result is not None:
                    file_contents[mod_file] = result
                else:
                    self.log.debug(
                        f"Failed to get file contents of '{mod_file.file_name}'!"
                    )

        matches: list[int] = []
        for mod_file, content in file_contents.items():
            if any(
                file.lower().strip().endswith(file_name.lower().strip())
                or (
                    f"skse/plugins/dynamicstringdistributor/{file_name.lower().strip()}"
                    in file.lower()
                )
                for file in content
            ):
                self.log.debug(f"Found '{file_name}' in file '{mod_file.file_name}'.")
                matches.append(mod_file.file_id)

        matches.reverse()

        if not matches:
            self.log.error(f"File '{file_name}' not found in mod {mod_id}!")

        return matches

    def __scrape_mod_translations(
        self, game_id: str, mod_id: int, language: str
    ) -> list[int]:
        """
        Requests modpage and extracts translations from HTML code
        because official API does not include translations in its response.

        As soon as the API v2 is available and supports translations, this function
        can be removed/replaced.

        Permission granted by Pickysaurus (Nexus Mods Moderator).

        Args:
            game_id (str): Nexus Mods game id, eg. skyrimspecialedition
            mod_id (int): Nexus Mods mod id

        Raises:
            ModNotFoundError: when the requested mod could not be found

        Returns:
            list[int]: List of translation mod ids
        """

        if not mod_id:
            raise ProviderApi.raise_mod_not_found_error(ModId(mod_id=mod_id))

        url: str = f"https://www.nexusmods.com/{game_id}/mods/{mod_id}"
        cache_file_path = ProviderApi.CACHE_FOLDER / (
            get_url_identifier(url) + ".cache"
        )

        cached: Optional[req.Response] = None
        try:
            cached = Cache.get_from_cache(cache_file_path)
        except FileNotFoundError:
            pass

        res: req.Response
        if cached is None:
            if self.__scraper is None:
                self.__scraper = cs.CloudScraper()

            headers = {
                "User-Agent": self.user_agent,
            }

            res = self.__scraper.get(url, headers=headers)
            Cache.save_to_cache(cache_file_path, res)
        else:
            res = cached
            self.log.debug(f"Got cached Web response for {url!r}")

        self.handle_status_code(url, res.status_code)

        html: str = res.content.decode(errors="replace")
        parsed = bs4.BeautifulSoup(html, features="html.parser")

        translation_list = parsed.find("ul", {"class": "translations"})
        if translation_list is None:
            return []

        available_translations: list[int] = []
        for tag in translation_list.children:  # type: ignore[attr-defined]
            tag_text: Optional[str] = tag.text

            if not tag_text or tag_text == "\n":
                continue

            tags = parsed.find_all("a", {"class": f"sortme flag flag-{tag_text}"})
            urls: list[str] = [tag["href"] for tag in tags]  # type: ignore[misc,index]

            lang_name: str = NexusModsApi.LANG_OVERRIDES.get(tag_text, tag_text).lower()
            if lang_name == language:
                available_translations += [
                    NexusModsApi.get_ids_from_url(url)[1] for url in urls
                ]

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
        url = f"https://www.nexusmods.com/sso?id={uuid}&application={self.APP_SLUG}"
        webbrowser.open(url)

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

        self.__api_key = api_key
        self.log.info("SSO process successful.")

        return self.__api_key

    def __get_premium_download_url(
        self, game_id: str, mod_id: int, file_id: int, server_id: str = "Nexus CDN"
    ) -> str:
        """
        Generates premium download URL for `file_id` from `mod_id`.
        Uses `server` if specified.
        """

        path: str = f"games/{game_id}/mods/{mod_id}/files/{file_id}/download_link.json"
        res: req.Response = self.__request(path, cache_result=False)
        data: list[dict[str, str]] = json.loads(res.content.decode())

        if not data:
            raise ApiNoServerAvailableError(path)

        try:
            for url_data in data:
                if url_data["short_name"].lower() == server_id.lower():
                    return url_data["URI"]

            # Handle errors
            else:
                raise ApiInvalidServerError(path)

        except KeyError as ex:
            raise UnexpectedResponseError(path, res.content.decode()) from ex

    def __get_free_download_url(
        self, game_id: str, mod_id: int, file_id: int, key: str, expires: int
    ) -> str:
        """
        Generates non-premium download URL for `file_id` from `mod_id`
        by using `key` and `expires`.
        """

        path: str = f"games/{game_id}/mods/{mod_id}/files/{file_id}/download_link.json"
        path += f"?key={key}&expires={expires}"

        res: req.Response = self.__request(path, cache_result=False)
        data: list[dict[str, str]] = json.loads(res.content.decode())

        try:
            for url_data in data:
                return url_data["URI"]
            else:
                raise ApiNoServerAvailableError(path)

        except KeyError as ex:
            raise UnexpectedResponseError(path, res.content.decode()) from ex

    @override
    def request_download(self, mod_id: ModId) -> str:
        """
        Requests direct download url for a mod file from Nexus Mods.
        Waits for a Mod Manager download if the user has no Premium
        so make sure that the user is able to start it.

        Args:
            mod_id (ModId): Mod identifier

        Returns:
            str: Direct download url
        """

        if mod_id.file_id is None:
            raise ValueError("Mod file id must not be None.")

        if self.__premium:
            self.log.info("Starting premium download...")

            url = self.__get_premium_download_url(
                mod_id.nm_game_id, mod_id.mod_id, mod_id.file_id
            )

        else:
            self.log.info("Waiting for non-premium download...")

            # Use a queue to get the download details in a thread-safe way
            queue: Queue[NxmRequest] = Queue(1)

            def process_url(url: str) -> None:
                nxm_request: NxmRequest = NxmRequest.from_url(url)

                if (
                    nxm_request.mod_id == mod_id.mod_id
                    and nxm_request.file_id == mod_id.file_id
                    and nxm_request.game == mod_id.nm_game_id
                ):
                    queue.put(nxm_request)

            NXMHandler.get().request_signal.connect(process_url)
            nxm_request: NxmRequest = queue.get()
            NXMHandler.get().request_signal.disconnect(process_url)

            key: str = nxm_request.key
            expires: int = nxm_request.expires

            url = self.__get_free_download_url(
                mod_id.nm_game_id, mod_id.mod_id, mod_id.file_id, key, expires
            )
            queue.task_done()

            self.log.info("Got non-premium download.")

        return url

    @override
    @classmethod
    def get_source(cls) -> Source:
        return Source.NexusMods

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
    def get_ids_from_url(url: str) -> tuple[str, int, Optional[int]]:
        """
        Extracts the game id, mod id and file id from a Nexus Mods url.

        Args:
            url (str): Nexus Mods url

        Raises:
            ValueError:
                When the url is not a Nexus Mods url or does not contain a mod or game id

        Returns:
            tuple[str, int, Optional[int]]: Game id, mod id and file id, if any
        """

        url_match: Optional[re.Match[str]] = NexusModsApi.MODPAGE_URL_PATTERN.match(url)

        if url_match is not None:
            game_id: str = url_match.group(1)
            mod_id: int = int(url_match.group(2))
            file_id: Optional[int] = int(url_match.group(3) or 0) or None

            return game_id, mod_id, file_id

        raise ValueError(f"Could not extract mod id from {url!r}")
