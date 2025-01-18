"""
Copyright (c) Cutleast
"""

import os
import sys
from typing import Any

import pytest
from pydantic import ValidationError

sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.masterlist.masterlist import Masterlist
from src.core.masterlist.masterlist_entry import MasterlistEntry
from src.core.translation_provider.source import Source


class TestMasterlist:
    """
    Tests `core.masterlist.masterlist.Masterlist`.
    """

    def test_masterlist_ignore(self) -> None:
        """
        Tests `core.masterlist.masterlist.Masterlist` on an ignore entry.
        """

        # given
        input_data: dict[str, dict[str, Any]] = {"test": {"type": "ignore"}}

        # when
        masterlist: Masterlist = Masterlist.from_data(input_data)

        # then
        assert masterlist.entries["test"].type == MasterlistEntry.Type.Ignore
        assert masterlist.is_ignored("test")
        assert masterlist.is_ignored("TeST")

    def test_masterlist_incomplete(self) -> None:
        """
        Tests `core.masterlist.masterlist.Masterlist` on incomplete entries.
        """

        # given
        input_data: dict[str, dict[str, Any]] = {"test": {"targets": []}}

        # then
        with pytest.raises(ValidationError):
            Masterlist.from_data(input_data)

    def test_masterlist_route(self) -> None:
        """
        Tests `core.masterlist.masterlist.Masterlist` on a route entry.
        """

        # given
        input_data: dict[str, dict[str, Any]] = {
            "test": {
                "type": "route",
                "targets": [{"source": "NexusMods", "mod_id": 1, "file_id": 1}],
            }
        }

        # when
        masterlist: Masterlist = Masterlist.from_data(input_data)
        entry: MasterlistEntry = masterlist.entries["test"]

        # then
        assert entry.type == MasterlistEntry.Type.Route
        assert entry.targets is not None
        assert len(entry.targets) == 1
        assert entry.targets[0].source.value == Source.NexusMods.value
        assert entry.targets[0].mod_id == 1
        assert entry.targets[0].file_id == 1
