"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import platform
from enum import auto
from typing import Any, Optional

from app_context import AppContext
from core.cacher.cacher import Cacher
from core.masterlist.masterlist import Masterlist
from core.masterlist.masterlist_entry import MasterlistEntry
from core.translation_provider.source import Source
from core.utilities.base_enum import BaseEnum

from .cdt_api import CDTApi
from .nm_api import NexusModsApi


class Provider:
    """
    Unified class for available translation sources.

    TODO: Overhaul this
    """

    log = logging.getLogger("Provider")

    class Preference(BaseEnum):
        OnlyNexusMods = auto()
        PreferNexusMods = auto()
        OnlyConfrerie = auto()
        PreferConfrerie = auto()

    preference: Preference = Preference.PreferNexusMods

    # Common attributes
    user_agent: str

    # Nexus Mods attributes
    __nm_api: NexusModsApi

    @property
    def api_key(self) -> str:
        return self.__nm_api.api_key

    @api_key.setter
    def api_key(self, key: str) -> None:
        self.__nm_api.api_key = key

    # Confrérie attributes
    __cdt_api: CDTApi

    def __init__(self, api_key: str, cacher: Cacher, preference: Preference):
        self.preference = preference
        self.__init_apis(api_key, cacher)

        self.user_agent = (
            f"{AppContext.get_app_type().APP_NAME}/"
            f"{AppContext.get_app_type().APP_VERSION} "
            f"({platform.system()} {platform.version()}; "
            f"{platform.architecture()[0]})"
        )

    def __init_apis(self, api_key: str, cacher: Cacher) -> None:
        """
        Initializes APIs according to preference.
        """

        self.__nm_api = NexusModsApi(cacher, api_key)
        self.__cdt_api = CDTApi(cacher)

    def check_api_key(self) -> bool:
        """
        Checks Nexus Mods API Key if Nexus Mods API is initialized and enabled.

        Returns always `True` for Confrérie API.
        """

        if self.preference != Provider.Preference.OnlyConfrerie:
            return self.__nm_api.check_api_key()

        return True

    def direct_downloads_possible(self) -> bool:
        """
        Checks if direct downloads are possible for Nexus Mods API.

        Returns:
            bool: `True` if direct downloads are possible, `False` otherwise
        """

        if self.preference != Provider.Preference.OnlyConfrerie:
            return self.__nm_api.premium

        return True

    def get_remaining_requests(self) -> tuple[int, int]:
        """
        Returns remaining API requests for Nexus Mods and -1 for Confrérie.

        Returns: `(rem_hreq, rem_dreq)`
        """

        if (
            self.__nm_api is not None
            and self.preference != Provider.Preference.OnlyConfrerie
        ):
            return (self.__nm_api.rem_hreq, self.__nm_api.rem_dreq)

        return (-1, -1)

    def get_details(
        self,
        mod_id: int,
        file_id: Optional[int] = None,
        source: Optional[Source] = None,
    ) -> dict[str, Any]:
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
                Provider.Preference.OnlyNexusMods,
                Provider.Preference.PreferNexusMods,
            ]:
                source = Source.NexusMods
            else:
                source = Source.Confrerie

        if source == Source.NexusMods:
            if file_id:
                nm_details = self.__nm_api.get_file_details(
                    "skyrimspecialedition", mod_id, file_id
                )
                if nm_details is None:
                    raise FileNotFoundError(
                        f"File {mod_id} > {file_id} not found on Nexus Mods!"
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
                if nm_details is None:
                    raise FileNotFoundError(f"Mod {mod_id} not found on Nexus Mods!")

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
            if cdt_details is None:
                raise FileNotFoundError(f"Mod {mod_id} not found on Confrérie!")

            details = {
                "name": cdt_details["FrenchName"],
                "filename": cdt_details["Filename"],
                "version": cdt_details["Version"],
                "timestamp": self.__cdt_api.get_timestamp_of_file(mod_id),
                "modpage_url": self.__cdt_api.get_modpage_link(mod_id),
            }

        return details

    def get_modpage_link(
        self,
        mod_id: int,
        file_id: Optional[int] = None,
        source: Optional[Source] = None,
        mod_manager: bool = False,
    ) -> str | None:
        """
        Gets modpage url for `mod_id` (and `file_id` if given) from `source`.
        """

        if source is None:
            if self.preference in [
                Provider.Preference.OnlyNexusMods,
                Provider.Preference.PreferNexusMods,
            ]:
                source = Source.NexusMods
            else:
                source = Source.Confrerie

        if source == Source.NexusMods:
            return NexusModsApi.create_nexus_mods_url(
                "skyrimspecialedition", mod_id, file_id, mod_manager
            )
        else:
            return self.__cdt_api.get_modpage_link(mod_id)

    def get_translations(
        self, mod_id: int, plugin_name: str, language: str, author_blacklist: list[str]
    ) -> list[tuple[int, list[int], Source]]:
        """
        Scans for translations for `language` that contain `plugin_name` and
        returns a list of tuples `(translation mod id, [translation file ids], source)`
        specifying available translations.
        """

        available_translations: list[tuple[int, list[int], Source]] = []
        nm_translations: list[tuple[int, list[int], Source]] = []
        cdt_translations: list[tuple[int, list[int], Source]] = []

        if self.preference != Provider.Preference.OnlyConfrerie:
            translation_urls = self.__nm_api.get_mod_translations(
                "skyrimspecialedition", mod_id
            ).get(language, [])

            for translation_url in translation_urls:
                translation_mod_id = int(translation_url.split("/")[-1].split("?")[0])

                try:
                    translation_details = self.__nm_api.get_mod_details(
                        "skyrimspecialedition", translation_mod_id
                    )
                    if translation_details is None:
                        raise FileNotFoundError(
                            f"Translation {translation_mod_id} not found on Nexus Mods!"
                        )
                except Exception as ex:
                    self.log.error(
                        f"Failed to get details of mod {translation_mod_id}: {ex}",
                        exc_info=ex,
                    )
                    continue

                # Skip translations from authors on the author_blacklist
                if translation_details["author"].lower() in author_blacklist:
                    self.log.debug(
                        f"Skipped translation by author {translation_details['author']!r} due to configured blacklist."
                    )
                    continue
                elif translation_details["uploaded_by"].lower() in author_blacklist:
                    self.log.debug(
                        f"Skipped translation by uploader {translation_details['uploaded_by']!r} due to configured blacklist."
                    )
                    continue

                try:
                    translation_file_ids = self.__nm_api.scan_mod_for_filename(
                        "skyrimspecialedition", translation_mod_id, plugin_name
                    )
                except Exception as ex:
                    self.log.error(
                        f"Failed to scan mod {translation_mod_id} for files: {ex}",
                        exc_info=ex,
                    )
                    continue

                if translation_file_ids:
                    nm_translations.append(
                        (
                            translation_mod_id,
                            translation_file_ids,
                            Source.NexusMods,
                        )
                    )

        if self.preference != Provider.Preference.OnlyNexusMods:
            if self.__cdt_api.has_translation(mod_id):
                cdt_translations.append((mod_id, [], Source.Confrerie))

        masterlist: Masterlist = AppContext.get_app().masterlist
        masterlist_entry: Optional[MasterlistEntry] = masterlist.entries.get(
            plugin_name.lower()
        )
        if masterlist_entry is not None:
            if (
                masterlist_entry.type == MasterlistEntry.Type.Route
                and masterlist_entry.targets
            ):
                for target in masterlist_entry.targets:
                    masterlist_mod_id: int = target.mod_id
                    masterlist_file_id: Optional[int] = target.file_id
                    masterlist_source: Source = target.source

                    # TODO: Improve this to prevent overriding other translations with the same mod id
                    if masterlist_source == Source.NexusMods:
                        if masterlist_file_id is not None:
                            nm_translations.append(
                                (
                                    masterlist_mod_id,
                                    [masterlist_file_id or 0],
                                    masterlist_source,
                                )
                            )
                        else:
                            self.log.warning(
                                f"Failed to process masterlist entry for {plugin_name} "
                                "due to missing file id!"
                            )
                    elif masterlist_source == Source.Confrerie:
                        cdt_translations.append(
                            (masterlist_mod_id, [], masterlist_source)
                        )

        match self.preference:
            case Provider.Preference.PreferNexusMods:
                available_translations = nm_translations + cdt_translations

            case Provider.Preference.PreferConfrerie:
                available_translations = cdt_translations + nm_translations

            case Provider.Preference.OnlyNexusMods:
                available_translations = nm_translations

            case Provider.Preference.OnlyConfrerie:
                available_translations = cdt_translations

        return available_translations

    def is_update_available(
        self, mod_id: int, file_id: int, timestamp: int, source: Source
    ) -> bool:
        """
        Checks if an update is available for the specified mod and file.
        Uses `mod_id` and `file_id` for Nexus Mods and `timestamp`
        for Confrérie des Traducteurs.
        """

        if (
            source == Source.NexusMods
            and self.preference != Provider.Preference.OnlyConfrerie
        ):
            return file_id in self.__nm_api.get_mod_updates(
                "skyrimspecialedition", mod_id
            )

        elif (
            source == Source.Confrerie
            and self.preference != Provider.Preference.OnlyNexusMods
        ):
            cdt_timestamp = self.__cdt_api.get_timestamp_of_file(mod_id)
            if cdt_timestamp is not None and timestamp is not None:
                return cdt_timestamp > timestamp

        return False

    def get_updated_file_id(self, mod_id: int, file_id: Optional[int]) -> Optional[int]:
        """
        Returns file id of updated file for `file_id` if NexusMods is enabled as source.
        """

        new_file_id: Optional[int] = None
        if self.preference != Provider.Preference.OnlyConfrerie:
            updates = self.__nm_api.get_mod_updates("skyrimspecialedition", mod_id)

            old_file_id: Optional[int] = file_id

            while old_file_id := updates.get(old_file_id):  # type: ignore[arg-type]
                new_file_id = old_file_id

        return new_file_id

    def request_download(
        self,
        mod_id: int,
        file_id: Optional[int] = None,
        source: Optional[Source] = None,
    ) -> str:
        """
        Requests a download for a mod file from a specified source.
        Attempts to determine source automatically if not specified.

        Args:
            mod_id (int): Nexus Mods mod id.
            file_id (Optional[int], optional): Nexus Mods file id. Defaults to None.
            source (Optional[Source], optional): Source. Defaults to None.

        Raises:
            FileNotFoundError: when the mod is not found on the source.

        Returns:
            str: Download link.
        """

        if source is None:
            if (self.preference == Provider.Preference.OnlyNexusMods) or file_id:
                source = Source.NexusMods
            else:
                source = Source.Confrerie

        if source == Source.NexusMods:
            if file_id is None:
                raise ValueError("File id must be specified for Nexus Mods!")

            return self.__nm_api.request_download(
                "skyrimspecialedition", mod_id, file_id
            )

        else:
            url: Optional[str] = self.__cdt_api.get_download_link(mod_id)

            if url is None:
                raise FileNotFoundError("File not found on Confrérie des Traducteurs!")

            return url
