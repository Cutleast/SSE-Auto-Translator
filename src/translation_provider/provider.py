"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import platform
from enum import Enum, auto

from main import MainApp

from .cdt_api import CDTApi
from .nm_api import NexusModsApi

from utilities import Source


class Provider:
    """
    Unified class for available translation sources.
    """

    log = logging.getLogger("Provider")

    class Preference(Enum):
        OnlyNexusMods = auto()
        PreferNexusMods = auto()
        OnlyConfrerie = auto()
        PreferConfrerie = auto()

        @classmethod
        def get(cls, name: str, default=None, /):
            try:
                return cls[name]
            except KeyError:
                return default

    preference: Preference = Preference.PreferNexusMods

    # Common attributes
    user_agent = f"\
{MainApp.name}/{MainApp.version} \
(\
{platform.system()} \
{platform.version()}; \
{platform.architecture()[0]}\
)"

    # Nexus Mods attributes
    __nm_api: NexusModsApi = None

    @property
    def api_key(self):
        return self.__nm_api.api_key

    @api_key.setter
    def api_key(self, key: str):
        self.__nm_api.api_key = key

    # Confrérie attributes
    __cdt_api: CDTApi = None

    def __init__(self, api_key: str, preference: Preference):
        self.preference = preference
        self.__init_apis(api_key)

    def __init_apis(self, api_key: str):
        """
        Initializes APIs according to preference.
        """

        self.log.info(
            f"Initializing APIs according to preference {self.preference.name!r}..."
        )

        match self.preference:
            case self.Preference.OnlyNexusMods:
                self.__nm_api = NexusModsApi(api_key)
            case self.Preference.OnlyConfrerie:
                self.__cdt_api = CDTApi()

            case self.Preference.PreferNexusMods | self.Preference.PreferConfrerie:
                self.__nm_api = NexusModsApi(api_key)
                self.__cdt_api = CDTApi()

        if self.__nm_api is not None:
            self.log.info("Initialized Nexus Mods API.")

        if self.__cdt_api is not None:
            self.log.info("Initialized Confrérie API.")

    def check_api_key(self):
        """
        Checks Nexus Mods API Key if Nexus Mods API is initialized and enabled.

        Returns always `True` for Confrérie API.
        """

        if self.preference != self.Preference.OnlyConfrerie:
            return self.__nm_api.check_api_key()

        return True

    def direct_downloads_possible(self):
        if self.preference != self.Preference.OnlyConfrerie:
            return self.__nm_api.premium

        return True

    def get_remaining_requests(self) -> tuple[int, int]:
        """
        Returns remaining API requests for Nexus Mods and -1 for Confrérie.

        Returns: `(rem_hreq, rem_dreq)`
        """

        if (
            self.__nm_api is not None
            and self.preference != self.Preference.OnlyConfrerie
        ):
            return (self.__nm_api.rem_hreq, self.__nm_api.rem_dreq)

        return (-1, -1)

    def get_details(
        self, mod_id: int, file_id: int = None, source: Source = None
    ) -> dict:
        """
        Returns details for `mod_id` (and `file_id` if given) from `source` as unified dictionary.

        Example:
        ```
        {
            "name": "<name>",
            "filename": "<filename if file_id is specified else None>",
            "version": "<version>",
            "timestamp": "<UNIX timestamp of upload / last update>",
            "modpage_url": "<url to modpage (and file if file_id is specified)",
        }
        ```
        """

        details: dict = {}

        if source is None:
            if self.preference in [
                self.Preference.OnlyNexusMods,
                self.Preference.PreferNexusMods,
            ]:
                source = Source.NexusMods
            else:
                source = Source.Confrerie

        if source == Source.NexusMods:
            if file_id:
                nm_details = self.__nm_api.get_file_details(
                    "skyrimspecialedition", mod_id, file_id
                )
                details = {
                    "name": nm_details["name"],
                    "filename": nm_details["file_name"],
                    "version": nm_details["mod_version"],
                    "timestamp": nm_details["uploaded_timestamp"],
                    "modpage_url": self.__nm_api.create_nexus_mods_url(
                        "skyrimspecialedition", mod_id, file_id
                    ),
                }
            else:
                nm_details = self.__nm_api.get_mod_details(
                    "skyrimspecialedition", mod_id
                )
                details = {
                    "name": nm_details["name"],
                    "filename": None,
                    "version": nm_details["version"],
                    "timestamp": nm_details["updated_timestamp"],
                    "modpage_url": self.__nm_api.create_nexus_mods_url(
                        "skyrimspecialedition", mod_id
                    ),
                }
        else:
            cdt_details = self.__cdt_api.get_mod_details(mod_id)
            details = {
                "name": cdt_details["FrenchName"],
                "filename": cdt_details["Filename"],
                "version": cdt_details["Version"],
                "timestamp": self.__cdt_api.get_timestamp_of_file(mod_id),
                "modpage_url": self.__cdt_api.get_modpage_link(mod_id),
            }

        return details

    def get_modpage_link(
        self, mod_id: int, file_id: int = None, source: Source = None
    ) -> str | None:
        """
        Gets modpage url for `mod_id` (and `file_id` if given) from `source`.
        """

        if source is None:
            if self.preference in [
                self.Preference.OnlyNexusMods,
                self.Preference.PreferNexusMods,
            ]:
                source = Source.NexusMods
            else:
                source = Source.Confrerie

        if source == Source.NexusMods:
            return NexusModsApi.create_nexus_mods_url(
                "skyrimspecialedition", mod_id, file_id
            )
        else:
            return self.__cdt_api.get_modpage_link(mod_id)

    def get_translations(
        self, mod_id: int, plugin_name: str, language: str
    ) -> list[tuple[int, list[int], Source]]:
        """
        Scans for translations for `language` that contain `plugin_name` and
        returns a list of tuples `(translation mod id, [translation file ids], source)`
        specifying available translations.
        """

        available_translations: list[tuple[int, list[int], Source]] = []
        nm_translations: list[tuple[int, list[int], Source]] = []
        cdt_translations: list[tuple[int, list[int], Source]] = []

        if self.preference != self.Preference.OnlyConfrerie:
            translation_urls = self.__nm_api.get_mod_translations(
                "skyrimspecialedition", mod_id
            ).get(language, [])
            for translation_url in translation_urls:
                translation_mod_id = int(translation_url.split("/")[-1].split("?")[0])

                translation_file_ids = self.__nm_api.scan_mod_for_filename(
                    "skyrimspecialedition", translation_mod_id, plugin_name
                )

                if translation_file_ids:
                    nm_translations.append(
                        (
                            translation_mod_id,
                            translation_file_ids,
                            Source.NexusMods,
                        )
                    )

        if self.preference != self.Preference.OnlyNexusMods:
            if self.__cdt_api.has_translation(mod_id):
                cdt_translations.append((mod_id, [], Source.Confrerie))

        match self.preference:
            case self.Preference.PreferNexusMods:
                available_translations = nm_translations + cdt_translations

            case self.Preference.PreferConfrerie:
                available_translations = cdt_translations + nm_translations

            case self.Preference.OnlyNexusMods:
                available_translations = nm_translations

            case self.Preference.OnlyConfrerie:
                available_translations = cdt_translations

        return available_translations

    def is_update_available(self, mod_id: int, file_id: int, timestamp: int, source: Source) -> bool:
        """
        Checks if an update is available for the specified mod and file.
        Uses `mod_id` and `file_id` for Nexus Mods and `timestamp`
        for Confrérie des Traducteurs.
        """

        if source == Source.NexusMods and self.preference != self.Preference.OnlyConfrerie:
            return file_id in self.__nm_api.get_mod_updates(
                "skyrimspecialedition", mod_id
            )

        elif source == Source.Confrerie and self.preference != self.Preference.OnlyNexusMods:
            cdt_timestamp = self.__cdt_api.get_timestamp_of_file(mod_id)
            if cdt_timestamp is not None and timestamp is not None:
                return cdt_timestamp > timestamp

        return False

    def get_updated_file_id(self, mod_id: int, file_id: int) -> int | None:
        """
        Returns file id of updated file for `file_id` if NexusMods is enabled as source.
        """

        if self.preference != self.Preference.OnlyConfrerie:
            updates = self.__nm_api.get_mod_updates("skyrimspecialedition", mod_id)

            old_file_id = file_id
            new_file_id = None

            while old_file_id := updates.get(old_file_id):
                new_file_id = old_file_id

            return new_file_id

    def get_direct_download_url(
        self,
        mod_id: int,
        file_id: int = None,
        key: str = None,
        expires: int = None,
        source: Source = None,
    ):
        """
        Returns direct download url from `source`. Auto-selects source if `source` is None.
        """

        if source is None:
            if (self.preference == self.Preference.OnlyNexusMods) or file_id:
                source = Source.NexusMods
            else:
                source = Source.Confrerie

        if source == Source.NexusMods:
            if self.__nm_api.premium or (key and expires):
                return self.__nm_api.get_direct_download_url(
                    "skyrimspecialedition", mod_id, file_id, key, expires
                )
            else:
                return None

        else:
            return self.__cdt_api.get_download_link(mod_id)
