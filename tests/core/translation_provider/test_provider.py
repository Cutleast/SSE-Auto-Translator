"""
Copyright (c) Cutleast
"""

import pytest
from pytest_mock import MockerFixture

from core.config.user_config import UserConfig
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.provider_preference import ProviderPreference
from core.translation_provider.source import Source
from tests.setup.data_factory import DataFactory


class TestTranslationProvider:
    """
    Tests `core.translation_provider.provider.TranslationProvider`.
    """

    @pytest.fixture
    def unavailable_provider(self, mocker: MockerFixture) -> TranslationProvider:
        """
        Creates a translation provider without an available API.

        Args:
            mocker (MockerFixture): Fixture for mocking dependencies.

        Returns:
            TranslationProvider: Translation provider without initialized APIs.
        """

        user_config: UserConfig = DataFactory.user_config()
        user_config.provider_preference = ProviderPreference.OnlyNexusMods
        mocker.patch(
            "core.translation_provider.provider_manager.NexusModsApi",
            side_effect=RuntimeError,
        )

        return TranslationProvider(user_config)

    def test_reports_unavailable_providers(
        self, unavailable_provider: TranslationProvider
    ) -> None:
        """
        Tests availability reporting when provider initialization fails.

        Args:
            unavailable_provider (TranslationProvider): Provider under test.
        """

        # then
        assert not unavailable_provider.is_available
        assert not unavailable_provider.is_source_available(Source.NexusMods)
        assert not unavailable_provider.is_source_available(Source.Confrerie)
