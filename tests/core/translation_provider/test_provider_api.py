"""
Copyright (c) Cutleast
"""

from typing import Optional

import pytest

from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.mod_id import ModId
from core.translation_provider.provider_api import ProviderApi
from tests.core.core_test import CoreTest


class TestProviderApi(CoreTest):
    """
    Tests `core.translation_provider.provider_api.ProviderApi`.
    """

    mod_not_found_values: list[tuple[str, int, Optional[str], Optional[int]]] = [
        ("abc (123 > 456)", 123, "abc", 456),
        ("abc (123)", 123, "abc", None),
        ("123", 123, None, None),
        ("123 > 456", 123, None, 456),
    ]

    @pytest.mark.parametrize(
        "exc_text, mod_id, mod_name, file_id", mod_not_found_values
    )
    def test_raise_mod_not_found_error(
        self,
        exc_text: str,
        mod_id: int,
        mod_name: Optional[str],
        file_id: Optional[int],
    ) -> None:
        """
        Tests `ProviderApi.raise_mod_not_found_error()`.
        """

        with pytest.raises(ModNotFoundError) as exc_info:
            # when
            ProviderApi.raise_mod_not_found_error(
                ModId(mod_id=mod_id, file_id=file_id), mod_name
            )

        # then
        assert exc_text in exc_info.value.args[0]
