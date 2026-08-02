"""
Copyright (c) Cutleast
"""

import logging
from typing import Literal, NoReturn, TypeVar, overload

from core.config.user_config import UserConfig

from .cdt_api.ctd_api import CDTApi
from .nm_api.nm_api import NexusModsApi
from .provider_api import ProviderApi
from .provider_preference import ProviderPreference
from .source import Source

T = TypeVar("T", bound=ProviderApi)


class ProviderManager:
    """
    Creates and resolves the translation providers configured for one application run.
    """

    __providers: dict[Source, ProviderApi]
    __provider_preference: ProviderPreference

    log: logging.Logger = logging.getLogger("ProviderManager")

    def __init__(self, user_config: UserConfig) -> None:
        """
        Initializes the configured providers.

        Args:
            user_config (UserConfig): The user configuration.
        """

        self.__providers = {}
        self.__provider_preference = user_config.provider_preference

        self.log.info("Initializing configured translation providers.")
        self.log.debug(f"Provider preference: '{self.__provider_preference}'")

        for source in self.__get_configured_sources():
            self.__initialize_provider(source, user_config)

    @property
    def providers(self) -> tuple[ProviderApi, ...]:
        """
        Gets the initialized providers in configured preference order.

        Returns:
            tuple[ProviderApi, ...]: The configured providers.
        """

        return tuple(self.__providers.values())

    def __get_configured_sources(self) -> tuple[Source, ...]:
        """
        Gets the sources configured by the user's provider preference.

        Returns:
            tuple[Source, ...]: Sources in preference order.
        """

        match self.__provider_preference:
            case ProviderPreference.OnlyNexusMods:
                return (Source.NexusMods,)
            case ProviderPreference.PreferNexusMods:
                return (Source.NexusMods, Source.Confrerie)
            case ProviderPreference.OnlyConfrerie:
                return (Source.Confrerie,)
            case ProviderPreference.PreferConfrerie:
                return (Source.Confrerie, Source.NexusMods)

    def __initialize_provider(self, source: Source, user_config: UserConfig) -> None:
        """
        Initializes one provider without preventing other configured sources from starting.

        Args:
            source (Source): Source to initialize.
            user_config (UserConfig): The user configuration.
        """

        try:
            match source:
                case Source.NexusMods:
                    provider = NexusModsApi()
                    provider.set_api_key(user_config.api_key)

                case Source.Confrerie:
                    provider = CDTApi()

                case _:
                    raise ValueError(f"Unsupported provider source: '{source}'")

        except Exception:
            self.log.exception(f"Failed to initialize provider '{source}'.")

        else:
            self.__providers[source] = provider

    def get_default_provider(self) -> ProviderApi:
        """
        Gets the highest-priority initialized provider.

        Raises:
            ValueError: When no provider is initialized.

        Returns:
            ProviderApi: The default provider.
        """

        if self.__providers:
            return next(iter(self.__providers.values()))

        raise ValueError("No translation provider is initialized.")

    def get_provider(self, provider_type: type[T]) -> T:
        """
        Gets an initialized provider by implementation type.

        Args:
            provider_type (type[T]): Provider implementation type.

        Raises:
            ValueError: When no matching provider is initialized.

        Returns:
            T: The requested provider.
        """

        for provider in self.__providers.values():
            if isinstance(provider, provider_type):
                return provider

        raise ValueError(
            f"Provider of type '{provider_type.__name__}' is not initialized."
        )

    @overload
    def get_provider_by_source(self, source: Literal[Source.Local]) -> NoReturn: ...

    @overload
    def get_provider_by_source(
        self, source: Literal[Source.NexusMods]
    ) -> NexusModsApi: ...

    @overload
    def get_provider_by_source(self, source: Literal[Source.Confrerie]) -> CDTApi: ...

    def get_provider_by_source(self, source: Source) -> ProviderApi:
        """
        Gets an initialized provider by source.

        Args:
            source (Source): Provider source.

        Raises:
            ValueError: When the source is local or not initialized.

        Returns:
            ProviderApi: The provider for the source.
        """

        if source is Source.Local:
            raise ValueError("Local files do not have a translation provider.")

        try:
            return self.__providers[source]
        except KeyError as ex:
            raise ValueError(
                f"Provider for source '{source}' is not initialized."
            ) from ex
