"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from pathlib import Path
from typing import Optional, cast
from unittest.mock import Mock

import pytest
from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.utilities.datetime import to_timestamp
from cutleast_core_lib.test.utils import Utils
from pytest_mock import MockerFixture

from core.translation_provider.provider_api import ProviderApi
from core.translation_provider.provider_manager import NexusModsApi
from core.utilities.web_utils import get_url_identifier
from tests.core.core_test import CoreTest


class TestNexusModsApi(CoreTest):
    """
    Tests `core.translation_provider.nm_api.NexusModsApi`.
    """

    GET_SORT_KEY: str = "get_sort_key"
    """Identifier for accessing the private method `NexusModsApi.__get_sort_key()`."""

    @staticmethod
    def get_sort_key_stub(
        translation_timestamp: int,
        translation_version: str,
        original_mod_timestamp: int,
        original_mod_version: str,
    ) -> tuple[bool, bool, int]:
        """Stub for `NexusModsApi.__get_sort_key()`."""

        raise NotImplementedError

    TEST_SORT_KEY_DATA: list[tuple[int, str, int, str, tuple[bool, bool, int]]] = [
        (0, "", 0, "", (False, False, 0)),
        (
            int(to_timestamp("01.10.2025 19:10")),
            "1.1-DV1.0",
            int(to_timestamp("01.10.2025 18:00")),
            "v1.1",
            (
                True,  # translation version starts with original mod version
                True,  # translation_timestamp > original_mod_timestamp
                1759338600,  # translation_timestamp
            ),
        ),
    ]
    """Test data for `TestNexusModsApi.test_get_sort_key"""

    @pytest.mark.parametrize(
        "translation_timestamp, translation_version, original_mod_timestamp, original_mod_version, expected_output",
        TEST_SORT_KEY_DATA,
    )
    def test_get_sort_key(
        self,
        translation_timestamp: int,
        translation_version: str,
        original_mod_timestamp: int,
        original_mod_version: str,
        expected_output: tuple[bool, int],
    ) -> None:
        """
        Tests `NexusModsApi.__get_sort_key()`.
        """

        # given
        method = Utils.get_private_method(
            NexusModsApi, TestNexusModsApi.GET_SORT_KEY, self.get_sort_key_stub
        )

        # when
        actual_result: tuple[bool, bool, int] = method(
            translation_timestamp,
            translation_version,
            original_mod_timestamp,
            original_mod_version,
        )

        # then
        assert actual_result == expected_output

    @staticmethod
    def __scrape(api: NexusModsApi, language: str) -> list[int]:
        """
        Calls the private scraper using the public method's language convention.

        Args:
            api (NexusModsApi): Provider under test.
            language (str): Requested language.

        Returns:
            list[int]: Matching translation IDs.
        """

        method_name: str = f"_{NexusModsApi.__name__}__scrape_mod_translations"
        method = cast(
            Callable[[str, int, str], list[int]],
            getattr(api, method_name),
        )
        return method("skyrimspecialedition", 123, language)

    @pytest.mark.parametrize(
        ("language", "expected"),
        [("russian", [191078]), ("Chinese", [190664]), ("german", [])],
    )
    def test_scrape_issue_table(
        self, mocker: MockerFixture, language: str, expected: list[int]
    ) -> None:
        """
        Tests the translation table structure reported in issue 158.

        Args:
            mocker (MockerFixture): Mocking fixture.
            language (str): Requested language.
            expected (list[int]): Expected translation IDs.
        """

        # given
        html: str = """
        <dd class="clearfix open"><div class="tabbed-block">
          <h3>Translations available on the Nexus</h3>
          <table class="table translation-table"><tbody>
            <tr><td class="table-translation-name">
              <a class="sortme flag flag-ru"
                 href="https://www.nexusmods.com/skyrimspecialedition/mods/191078">
                Russian
              </a><span class="table-author-name">Author: Apokrif Znaniy</span>
            </td><td class="table-translation-notes">
              <span class="sortme">King of the Murkmire Russian Translation</span>
            </td></tr>
            <tr><td class="table-translation-name">
              <a class="sortme flag flag-cn"
                 href="https://www.nexusmods.com/skyrimspecialedition/mods/190664">
                Simplified Chinese
              </a><span class="table-author-name">Author: DantyAcent</span>
            </td></tr>
          </tbody></table>
        </div></dd>
        """
        mocker.patch.object(
            Cache, "get_from_cache", return_value=Mock(content=html.encode())
        )
        session = mocker.patch(
            "core.translation_provider.nm_api.nm_api.curl_requests.Session"
        )
        api = NexusModsApi()

        # when
        actual: list[int] = self.__scrape(api, language)

        # then
        assert actual == expected
        session.assert_not_called()

    @pytest.mark.parametrize(
        ("label", "language", "expected"),
        [
            (" \n RuSSian \n ", " RUSSIAN ", [42, 43]),
            ("Mandarin", "chinese", [42, 43]),
            ("simplified\n Chinese", "chinese", [42, 43]),
            ("Traditional Chinese", "chinese", []),
        ],
    )
    def test_scrape_filters_links(
        self,
        mocker: MockerFixture,
        label: str,
        language: str,
        expected: list[int],
    ) -> None:
        """
        Tests normalization, table scoping, URL validation and stable deduplication.

        Args:
            mocker (MockerFixture): Mocking fixture.
            label (str): Language label in the HTML.
            language (str): Requested language.
            expected (list[int]): Expected unique IDs in table order.
        """

        # given
        base: str = "https://www.nexusmods.com/skyrimspecialedition/mods/"
        links: str = "".join(
            f'<a class="extra flag-ru flag sortme" href="{url}">{label}</a>'
            for url in [
                base + "42",
                base + "42",
                "invalid",
                "https://www.nexusmods.com/skyrim/mods/99",
                base + "43",
            ]
        )
        html: str = (
            f'<a class="sortme flag flag-ru" href="{base}88">{label}</a>'
            '<table class="extra translation-table table"><tbody><tr>'
            f'<td class="extra table-translation-name">{links}'
            f'<a>{label}</a></td><td class="table-translation-notes">'
            f'<a href="{base}77">{label}</a></td></tr></tbody></table>'
        )
        mocker.patch.object(
            Cache, "get_from_cache", return_value=Mock(content=html.encode())
        )

        # when
        actual: list[int] = self.__scrape(NexusModsApi(), language)

        # then
        assert actual == expected

    @pytest.mark.parametrize(
        "html",
        [
            "<html></html>",
            '<table class="translation-table"><tbody></tbody></table>',
            '<ul class="translations"><li>Russian</li></ul>',
        ],
    )
    def test_scrape_missing_table_entries(
        self, mocker: MockerFixture, html: str
    ) -> None:
        """
        Tests pages without usable new-format translations.

        Args:
            mocker (MockerFixture): Mocking fixture.
            html (str): Page without translation entries.
        """

        # given
        mocker.patch.object(
            Cache, "get_from_cache", return_value=Mock(content=html.encode())
        )

        # when
        actual: list[int] = self.__scrape(NexusModsApi(), "russian")

        # then
        assert actual == []

    def test_scrape_ignores_legacy_cache(self, mocker: MockerFixture) -> None:
        """
        Tests that legacy cached HTML cannot hide newly available translations.

        Args:
            mocker (MockerFixture): Mocking fixture.
        """

        # given
        url: str = "https://www.nexusmods.com/skyrimspecialedition/mods/123"
        identifier: str = get_url_identifier(url)
        old_path: Path = ProviderApi.CACHE_FOLDER / f"{identifier}.cache"
        new_path: Path = ProviderApi.CACHE_FOLDER / (
            f"translations-table-v1-{identifier}.cache"
        )
        cached: dict[Path, Mock] = {old_path: Mock(content=b"legacy page")}

        def get_cached(path: Path, default: Optional[Mock]) -> Optional[Mock]:
            """
            Looks up a response in the simulated cache.

            Args:
                path (Path): Cache key requested by the scraper.
                default (Optional[Mock]): Fallback for a missing entry.

            Returns:
                Optional[Mock]: Cached response or fallback.
            """

            return cached.get(path, default)

        read_cache = mocker.patch.object(Cache, "get_from_cache", side_effect=get_cached)
        save_cache = mocker.patch.object(Cache, "save_to_cache")
        response = Mock(status_code=200, content=b"<html></html>")
        session = mocker.patch(
            "core.translation_provider.nm_api.nm_api.curl_requests.Session"
        )
        session.return_value.get.return_value = response

        # when
        self.__scrape(NexusModsApi(), "russian")

        # then
        read_cache.assert_called_once_with(new_path, default=None)
        session.return_value.get.assert_called_once()
        save_cache.assert_called_once_with(new_path, response)

        # given
        cached[new_path] = response
        read_cache.reset_mock()

        # when
        self.__scrape(NexusModsApi(), "russian")

        # then
        read_cache.assert_called_once_with(new_path, default=None)
        session.assert_called_once()
        session.return_value.get.assert_called_once()
        save_cache.assert_called_once()

    def test_scrape_preserves_http_errors(self, mocker: MockerFixture) -> None:
        """
        Tests that HTTP errors reach the existing handler before caching or parsing.

        Args:
            mocker (MockerFixture): Mocking fixture.
        """

        # given
        mocker.patch.object(Cache, "get_from_cache", return_value=None)
        save_cache = mocker.patch.object(Cache, "save_to_cache")
        session = mocker.patch(
            "core.translation_provider.nm_api.nm_api.curl_requests.Session"
        )
        session.return_value.get.return_value = Mock(status_code=503)
        api = NexusModsApi()
        handler = mocker.patch.object(
            api, "handle_status_code", side_effect=RuntimeError("HTTP failure")
        )

        # when
        with pytest.raises(RuntimeError, match="HTTP failure"):
            self.__scrape(api, "russian")

        # then
        handler.assert_called_once_with(
            "https://www.nexusmods.com/skyrimspecialedition/mods/123", 503
        )
        save_cache.assert_not_called()
