"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
from typing import Optional

from core.config.user_config import UserConfig
from core.masterlist.masterlist import Masterlist
from core.masterlist.masterlist_entry import MasterlistEntry
from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.provider_api import ProviderApi

from .mod_details import ModDetails
from .mod_id import ModId
from .provider_manager import ProviderManager
from .source import Source


class Provider:
    """
    Unified class for available translation sources.
    """

    log: logging.Logger = logging.getLogger("Provider")

    def __init__(self, user_config: UserConfig) -> None:
        ProviderManager.init(user_config)

    def direct_downloads_possible(self, source: Optional[Source] = None) -> bool:
        """
        Checks if direct downloads are possible for Nexus Mods API.

        Args:
            source (Optional[Source], optional): Source. Defaults to preferred.

        Returns:
            bool: `True` if direct downloads are possible, `False` otherwise
        """

        if source is None:
            return ProviderManager.get_default_provider().is_direct_download_possible()

        else:
            return ProviderManager.get_provider_by_source(
                source
            ).is_direct_download_possible()

    def get_remaining_requests(self) -> tuple[int, int]:
        """
        Returns remaining API requests for Nexus Mods and -1 for Confrérie.

        Returns: `(rem_hreq, rem_dreq)`
        """

        return ProviderManager.get_default_provider().get_remaining_requests()

    def get_details(self, mod_id: ModId, source: Optional[Source] = None) -> ModDetails:
        """
        Returns the details for a mod.

        Args:
            mod_id (int): Mod identifier
            source (Optional[Source], optional): Source. Defaults to preferred.

        Raises:
            ValueError: when the Source is specified as `Source.Local`
            ModNotFoundError: when the requested mod could not be found

        Returns:
            ModDetails: Mod details
        """

        if source is None:
            return ProviderManager.get_default_provider().get_mod_details(mod_id)

        else:
            return ProviderManager.get_provider_by_source(source).get_mod_details(
                mod_id
            )

    def get_modpage_url(self, mod_id: ModId, source: Optional[Source] = None) -> str:
        """
        Gets modpage url for the specified mod.

        Args:
            mod_id (ModId): Mod identifier
            source (Optional[Source], optional): Source. Defaults to preferred.

        Raises:
            ValueError: when the Source is specified as `Source.Local`
            ModNotFoundError: when the requested mod could not be found

        Returns:
            str: Url to the modpage
        """

        if source is None:
            return ProviderManager.get_default_provider().get_modpage_url(mod_id)

        else:
            return ProviderManager.get_provider_by_source(source).get_modpage_url(
                mod_id
            )

    def get_translations(
        self,
        mod_id: ModId,
        file_name: str,
        language: str,
        masterlist: Masterlist,
        author_blacklist: list[str],
    ) -> dict[Source, list[ModId]]:
        """
        Gets available translations for the specified file from all available providers.

        Args:
            mod_id (ModId): Mod identifier
            file_name (str): Name of file that requires a translation.
            language (str): Language to filter for
            masterlist (Masterlist): Masterlist to use
            author_blacklist (list[str]): List of authors to ignore

        Returns:
            dict[Source, list[ModId]]: Map of sources and available translations
        """

        available_translations: dict[Source, list[ModId]] = {}

        for provider in ProviderManager.providers:
            translation_ids: list[ModId] = provider.get_translations(
                mod_id, file_name, language
            )

            for translation_id in translation_ids:
                translation_details: ModDetails = provider.get_mod_details(
                    translation_id
                )

                if (
                    translation_details.author
                    and translation_details.author.lower() in author_blacklist
                ):
                    self.log.debug(
                        f"Skipped translation by author {translation_details.author!r} "
                        "due to configured blacklist."
                    )
                    continue
                elif (
                    translation_details.uploader
                    and translation_details.uploader.lower() in author_blacklist
                ):
                    self.log.debug(
                        f"Skipped translation by uploader "
                        f"{translation_details.uploader!r} due to configured blacklist."
                    )
                    continue

                available_translations.setdefault(provider.get_source(), []).append(
                    translation_id
                )

        masterlist_entry: Optional[MasterlistEntry] = masterlist.entries.get(
            file_name.lower()
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

                    available_translations.setdefault(masterlist_source, []).append(
                        ModId(mod_id=masterlist_mod_id, file_id=masterlist_file_id)
                    )

        return available_translations

    def request_download(self, mod_id: ModId, source: Optional[Source] = None) -> str:
        """
        Requests a download url for a mod file from a specified source.

        Args:
            mod_id (int): Nexus Mods mod id.
            source (Optional[Source], optional): Source. Defaults to preferred.

        Raises:
            ValueError: when the Source is specified as `Source.Local`
            ModNotFoundError: when the mod is not found on the source.

        Returns:
            str: Download url
        """

        if source is None:
            return ProviderManager.get_default_provider().request_download(mod_id)

        else:
            return ProviderManager.get_provider_by_source(source).request_download(
                mod_id
            )

    def is_mod_id_valid(
        self, mod_id: ModId, source: Optional[Source] = None, check_online: bool = True
    ) -> bool:
        """
        Checks if the mod id is valid at the specified source by attempting to get its
        details if `check_online` is True.

        Args:
            mod_id (ModId): Mod identifier
            source (Optional[Source], optional): Source. Defaults to preferred.
            check_online (bool, optional):
                Whether to check by attempting to get the mod details. Defaults to True.

        Returns:
            bool: Whether the mod id is valid
        """

        if not mod_id.mod_id or mod_id.file_id == 0:
            return False

        if check_online:
            provider_api: ProviderApi
            if source is None:
                provider_api = ProviderManager.get_default_provider()
            else:
                provider_api = ProviderManager.get_provider_by_source(source)

            try:
                provider_api.get_mod_details(mod_id)
            except ModNotFoundError:
                return False

        return True

    @property
    def user_agent(self) -> str:
        """
        The user agent of the default provider.
        """

        return ProviderManager.get_default_provider().user_agent
