"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path

import pytest

from utilities.batch.command import BatchCommand

from ...base_test import BaseTest


class TestBatchCommand(BaseTest):
    """
    Tests `utilities.batch.command.BatchCommand`.
    """

    def test_defaults(self) -> None:
        """
        Tests that all fields have the expected default values when creating an instance
        without arguments.
        """

        # when
        command = BatchCommand()

        # then
        assert command.run_basic_scan is True
        assert command.translation_archives == []
        assert command.build_output_mod is True
        assert command.output_path is None

    def test_model_validate_json_minimal(self) -> None:
        """
        Tests deserialization of a minimal JSON object (all defaults applied).
        """

        # given
        raw_json: str = "{}"

        # when
        command = BatchCommand.model_validate_json(raw_json)

        # then
        assert command.run_basic_scan is True
        assert command.translation_archives == []
        assert command.build_output_mod is True
        assert command.output_path is None

    def test_model_validate_json_all_fields(self, tmp_path: Path) -> None:
        """
        Tests deserialization of a fully-populated JSON object.
        """

        # given
        archive1: Path = tmp_path / "mod1.7z"
        archive2: Path = tmp_path / "mod2.zip"
        output: Path = tmp_path / "output"

        raw: dict = {
            "run_basic_scan": False,
            "translation_archives": [str(archive1), str(archive2)],
            "build_output_mod": False,
            "output_path": str(output),
        }

        # when
        command = BatchCommand.model_validate_json(json.dumps(raw))

        # then
        assert command.run_basic_scan is False
        assert command.translation_archives == [archive1, archive2]
        assert command.build_output_mod is False
        assert command.output_path == output

    def test_model_validate_json_from_file(self, tmp_path: Path) -> None:
        """
        Tests that a JSON file written to disk can be deserialized correctly.
        """

        # given
        command_file: Path = tmp_path / "command.json"
        command_file.write_text(
            json.dumps({"run_basic_scan": False, "build_output_mod": False}),
            encoding="utf-8",
        )

        # when
        command: BatchCommand = BatchCommand.model_validate_json(
            command_file.read_bytes()
        )

        # then
        assert command.run_basic_scan is False
        assert command.build_output_mod is False

    def test_immutability(self) -> None:
        """
        Tests that the frozen model cannot be mutated after creation.
        """

        # given
        command = BatchCommand()

        # then
        with pytest.raises(Exception):
            command.run_basic_scan = False  # type: ignore[misc]
