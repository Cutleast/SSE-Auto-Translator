"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import re
from datetime import datetime
from typing import Any, Optional, override

import jstyleson as json
import pytz
import requests as req

from core.translation_provider.source import Source

from ..exceptions import ModNotFoundError, Non200HttpError, UnexpectedResponseError
from ..mod_details import ModDetails
from ..mod_id import ModId
from ..provider_api import ProviderApi


class CDTApi(ProviderApi):
    """
    Class for communication with Confrérie des Traducteurs API.
    """

    DL_URL_PATTERN: re.Pattern[str] = re.compile(
        r"https://www\.confrerie-des-traducteurs\.fr/skyrim/telechargement_se/([0-9]+)/"
        r"sse\?fromSseAtAPI=1"
    )
    """
    Regex pattern for capturing the CDT mod id from a download url.
    """

    MODPAGE_URL_PATTERN: re.Pattern[str] = re.compile(
        r"https://www\.confrerie-des-traducteurs\.fr/skyrim/mods/([0-9]+)"
    )
    """
    Regex pattern for capturing the CDT mod id from a modpage url.
    """

    @override
    def is_api_key_valid(self, key: str) -> bool:
        return True

    @override
    def is_direct_download_possible(self) -> bool:
        return True

    @override
    def get_remaining_requests(self) -> tuple[int, int]:
        return (-1, -1)

    @override
    def get_mod_details(self, mod_id: ModId) -> ModDetails:
        if not mod_id.nm_id:
            ProviderApi.raise_mod_not_found_error(mod_id)

        url: str = (
            "https://www.confrerie-des-traducteurs.fr/api/skyrim/sse-at/"
            f"{mod_id.nm_id or mod_id.mod_id}"
        )
        res: req.Response = self._request(url)

        try:
            response_data: dict[str, Any] = json.loads(res.content.decode())
            mod_details: ModDetails = ModDetails(
                display_name=response_data["FrenchName"],
                version=response_data["Version"],
                file_name=response_data["Filename"],
                mod_id=ModId(
                    mod_id=CDTApi.get_cdt_id_from_url(response_data["DownloadLink"]),
                    nm_id=response_data["NexusModId"],
                ),
                timestamp=CDTApi.get_timestamp_from_response_data(response_data),
                author=None,
                uploader=None,
                modpage_url=(
                    "https://www.confrerie-des-traducteurs.fr/skyrim/mods/"
                    + str(CDTApi.get_cdt_id_from_url(response_data["DownloadLink"]))
                ),
            )
        except Exception as ex:
            raise UnexpectedResponseError(url, res.content.decode()) from ex

        return mod_details

    @override
    def get_modpage_url(self, mod_id: ModId) -> str:
        return self.get_mod_details(mod_id).modpage_url

    @override
    def get_translations(
        self, mod_id: ModId, file_name: str, language: str
    ) -> list[ModId]:
        try:
            mod_details: ModDetails = self.get_mod_details(mod_id)
            translation_id = ModId(
                mod_id=CDTApi.get_cdt_id_from_url(mod_details.modpage_url),
                nm_id=mod_id.nm_id,
            )

            return [translation_id]

        except ModNotFoundError:
            return []

    @override
    def request_download(self, mod_id: ModId) -> str:
        if not mod_id.nm_id:
            ProviderApi.raise_mod_not_found_error(mod_id)

        url: str = (
            "https://www.confrerie-des-traducteurs.fr/api/skyrim/sse-at/"
            f"{mod_id.nm_id or mod_id.mod_id}"
        )
        res: req.Response = self._request(url)

        try:
            response_data: dict[str, Any] = json.loads(res.content.decode())
            download_url: str = response_data["DownloadLink"]

        except Non200HttpError as ex:
            if ex.args[1] == 404:
                ProviderApi.raise_mod_not_found_error(mod_id)
            else:
                raise ex

        except Exception as ex:
            raise UnexpectedResponseError(url, res.content.decode()) from ex

        return download_url

    @override
    @classmethod
    def get_source(cls) -> Source:
        return Source.Confrerie

    @staticmethod
    def get_cdt_id_from_url(url: str) -> int:
        """
        Extracts the CDT id of a mod file from a specified download or modpage url.

        Args:
            url (str): Modpage or download url

        Raises:
            ValueError: when the CDT id could not be extracted

        Returns:
            int: CDT id
        """

        dl_url_match: Optional[re.Match[str]] = CDTApi.DL_URL_PATTERN.match(url)
        if dl_url_match is not None:
            return int(dl_url_match.group(1))

        modpage_url_match: Optional[re.Match[str]] = CDTApi.MODPAGE_URL_PATTERN.match(
            url
        )
        if modpage_url_match is not None:
            return int(modpage_url_match.group(1))

        raise ValueError(f"Could not extract CDT id from {url!r}")

    @staticmethod
    def get_timestamp_from_response_data(response_data: dict[str, Any]) -> int:
        """
        Extracts the upload timestamp from the response data returned by the CDT API.

        Args:
            response_data (dict[str, Any]): Deserialized response data

        Returns:
            int: Upload timestamp
        """

        upload_details: dict[str, Any] = response_data["LastArchiveUpdateDate"]
        date: str = upload_details["date"]
        timezone: str = upload_details["timezone"]

        date_obj: datetime = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
        date_obj_utc: datetime = date_obj.replace(
            tzinfo=pytz.timezone(timezone)
        ).astimezone(pytz.utc)
        timestamp = int(date_obj_utc.timestamp())

        return timestamp
