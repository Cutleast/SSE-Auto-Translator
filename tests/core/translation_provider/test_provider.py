"""
Copyright (c) Cutleast
"""

import pytest
from pytest_mock import MockerFixture

from core.translation_provider.provider import TranslationProvider
from core.translation_provider.provider_preference import ProviderPreference
from core.translation_provider.source import Source
from core.user_data.user_data import UserData
from tests.base_test import BaseTest


class TestTranslationProvider(BaseTest):
    """
    Tests `core.translation_provider.provider.TranslationProvider`.
    """

    @pytest.fixture
    def unavailable_provider(
        self, mocker: MockerFixture, user_data: UserData
    ) -> TranslationProvider:
        """
        Creates a translation provider without an available API.

        Args:
            mocker (MockerFixture): Fixture for mocking dependencies.
            user_data (UserData): User data containing the configuration.

        Returns:
            TranslationProvider: Translation provider without initialized APIs.
        """

        user_data.user_config.provider_preference = ProviderPreference.OnlyNexusMods
        mocker.patch(
            "core.translation_provider.provider_manager.NexusModsApi",
            side_effect=RuntimeError,
        )

        return TranslationProvider(user_data.user_config)

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
