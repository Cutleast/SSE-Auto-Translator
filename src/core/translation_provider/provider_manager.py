"""
Copyright (c) Cutleast
"""

import logging
from typing import Literal, NoReturn, TypeVar, overload

from PySide6.QtCore import QObject

from core.cache.cache import Cache
from core.config.user_config import UserConfig

from .cdt_api.ctd_api import CDTApi
from .nm_api.nm_api import NexusModsApi
from .provider_api import ProviderApi
from .provider_preference import ProviderPreference
from .source import Source

T = TypeVar("T", bound=ProviderApi)


class ProviderManager(QObject):
    """
    Singleton-class for managing translation providers.
    """

    log: logging.Logger = logging.getLogger("ProviderManager")

    providers: list[ProviderApi] = []
    """The content and order of this list resembles the user preference."""

    provider_preference: ProviderPreference = ProviderPreference.OnlyNexusMods
    """The user preference for translation providers."""

    @classmethod
    def init(cls, user_config: UserConfig, cache: Cache) -> None:
        """
        Initializes configured translation providers. Clears all previously initialized
        providers.

        Args:
            user_config (UserConfig): The user configuration.
            cache (Cache): The cache.
        """

        cls.log.info("Initializing configured translation providers...")
        cls.log.debug(f"Provider preference: {user_config.provider_preference}")

        cls.providers.clear()
        cls.provider_preference = user_config.provider_preference
        match cls.provider_preference:
            case ProviderPreference.OnlyNexusMods:
                cls.__init_nm_api(user_config, cache)

            case ProviderPreference.PreferNexusMods:
                cls.__init_nm_api(user_config, cache)
                cls.__init_cdt_api(user_config, cache)

            case ProviderPreference.OnlyConfrerie:
                cls.__init_cdt_api(user_config, cache)

            case ProviderPreference.PreferConfrerie:
                cls.__init_cdt_api(user_config, cache)
                cls.__init_nm_api(user_config, cache)

    @classmethod
    def __init_nm_api(cls, user_config: UserConfig, cache: Cache) -> None:
        cls.log.info("Initializing Nexus Mods API...")
        try:
            nm_api = NexusModsApi(cache)
            nm_api.set_api_key(user_config.api_key)
            cls.providers.append(nm_api)
        except Exception as ex:
            cls.log.error(f"Failed to initialize Nexus Mods API: {ex}", exc_info=ex)

    @classmethod
    def __init_cdt_api(cls, user_config: UserConfig, cache: Cache) -> None:
        cls.log.info("Initializing Confrérie des Traducteurs API...")
        try:
            cdt_api = CDTApi(cache)
            cls.providers.append(cdt_api)
        except Exception as ex:
            cls.log.error(
                f"Failed to initialize Confrérie des Traducteurs API: {ex}", exc_info=ex
            )

    @classmethod
    def get_default_provider(cls) -> ProviderApi:
        """
        Gets the default provider based on the user preference. Just returns the first
        item of the providers list.

        Raises:
            ValueError: when there is no provider

        Returns:
            TranslationProvider: Default provider
        """

        if cls.providers:
            return cls.providers[0]

        raise ValueError("No provider found!")

    @classmethod
    def get_provider(cls, provider_type: type[T]) -> T:
        """
        Gets an initialized provider by its type.

        Args:
            provider_type (type[TranslationProvider]): Provider type

        Raises:
            ValueError: when the provider is not found

        Returns:
            TranslationProvider: Initialized provider
        """

        for provider in cls.providers:
            if isinstance(provider, provider_type):
                return provider
        else:
            raise ValueError(f"Provider of type {provider_type} not found!")

    @overload
    @classmethod
    def get_provider_by_source(cls, source: Literal[Source.Local]) -> NoReturn: ...

    @overload
    @classmethod
    def get_provider_by_source(
        cls, source: Literal[Source.NexusMods]
    ) -> NexusModsApi: ...

    @overload
    @classmethod
    def get_provider_by_source(cls, source: Literal[Source.Confrerie]) -> CDTApi: ...

    @classmethod
    def get_provider_by_source(cls, source: Source) -> ProviderApi:
        """
        Gets an initialized provider by its source.

        Args:
            source (Source): Source

        Raises:
            ValueError: when the provider is not found or Source is `Local`

        Returns:
            TranslationProvider: Initialized provider
        """

        match source:
            case Source.NexusMods:
                return cls.get_provider(NexusModsApi)

            case Source.Confrerie:
                return cls.get_provider(CDTApi)

            case _:
                raise ValueError(source)
