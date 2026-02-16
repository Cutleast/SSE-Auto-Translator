"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import re
from typing import Any, Optional, override

import jstyleson as json
import requests as req
from pydantic import ValidationError

from ..exceptions import ModNotFoundError, Non200HttpError, UnexpectedResponseError
from ..mod_details import ModDetails
from ..mod_id import ModId
from ..provider_api import ProviderApi
from ..source import Source
from .cdt_id import CdtModId
from .models.cdt_translation import CdtTranslation


class CDTApi(ProviderApi):
    """
    Class for communication with Confrérie des Traducteurs API.
    """

    API_BASE_URL: str = "https://www.confrerie-des-traducteurs.fr/api/skyrim/sse-at/"
    """Base URL for the SSE-AT API of Confrérie des Traducteurs."""

    DL_URL_PATTERN: re.Pattern[str] = re.compile(
        r"https://www\.confrerie-des-traducteurs\.fr/skyrim/telechargement-se/([0-9]+)"
        r"\?fromSseAtAPI=1"
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

    def __request_translation_details(self, mod_id: ModId) -> CdtTranslation:
        nm_mod_id: int = (
            mod_id.mod_id if not isinstance(mod_id, CdtModId) else mod_id.nm_mod_id
        )
        url: str = CDTApi.API_BASE_URL + str(nm_mod_id)
        res: req.Response = self._request(url)

        try:
            return CdtTranslation.model_validate_json(res.content, by_alias=True)
        except ValidationError as ex:
            raise UnexpectedResponseError(url, res.content.decode()) from ex

    @override
    def get_mod_details(self, mod_id: ModId) -> ModDetails:
        translation: CdtTranslation = self.__request_translation_details(mod_id)

        mod_details: ModDetails = ModDetails(
            display_name=translation.name,
            version=translation.version,
            file_name=translation.file_name,
            mod_id=CdtModId(
                installation_file_name=translation.file_name,
                mod_id=CDTApi.get_cdt_id_from_url(translation.download_link),
                nm_mod_id=(
                    mod_id.mod_id
                    if not isinstance(mod_id, CdtModId)
                    else mod_id.nm_mod_id
                ),
            ),
            timestamp=translation.timestamp,
            author=None,
            uploader=None,
            modpage_url=(
                "https://www.confrerie-des-traducteurs.fr/skyrim/mods/"
                + str(CDTApi.get_cdt_id_from_url(translation.download_link))
            ),
        )

        return mod_details

    @override
    def get_modpage_url(self, mod_id: ModId) -> str:
        return self.get_mod_details(mod_id).modpage_url

    @override
    def get_translations(
        self, mod_id: ModId, file_name: str, language: str
    ) -> list[ModId]:
        nm_mod_id: int = (
            mod_id.mod_id if not isinstance(mod_id, CdtModId) else mod_id.nm_mod_id
        )

        try:
            mod_details: ModDetails = self.get_mod_details(mod_id)
            translation_id = CdtModId(
                installation_file_name=mod_details.file_name,
                mod_id=CDTApi.get_cdt_id_from_url(mod_details.modpage_url),
                nm_mod_id=nm_mod_id,
            )

            return [translation_id]

        except ModNotFoundError:
            return []

    @override
    def request_download(self, mod_id: ModId) -> str:
        if not isinstance(mod_id, CdtModId):
            ProviderApi.raise_mod_not_found_error(mod_id)

        url: str = (
            "https://www.confrerie-des-traducteurs.fr/api/skyrim/sse-at/"
            f"{mod_id.nm_mod_id or mod_id.mod_id}"
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
