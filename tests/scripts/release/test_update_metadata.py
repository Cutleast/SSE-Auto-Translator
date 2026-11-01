"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path

from scripts.release.update_metadata import UpdateMetadata


class TestUpdateMetadata:
    """
    Tests `scripts.release.update_metadata.UpdateMetadata`.
    """

    def test_download_url_contains_public_file_id(self) -> None:
        """
        Tests the Nexus Mods download link of a file.
        """

        # when
        url: str = UpdateMetadata.download_url_for(
            "skyrimspecialedition", "111491", "900000"
        )

        # then
        assert (
            url
            == "https://www.nexusmods.com/skyrimspecialedition/mods/111491?tab=files&file_id=900000"
        )

    def test_write_new_release(self, tmp_path: Path) -> None:
        """
        Tests that a newer release replaces the existing metadata.
        """

        # given
        update_file: Path = tmp_path / "update.json"
        update_file.write_text(
            '{"version": "3.2.6", "download_url": "https://example.invalid/old"}',
            encoding="utf8",
        )
        metadata = UpdateMetadata(
            version="3.2.7", download_url="https://example.invalid/new", file_id="900000"
        )

        # when
        written: bool = metadata.write(update_file)

        # then
        assert written
        assert json.loads(update_file.read_text(encoding="utf8")) == {
            "version": "3.2.7",
            "download_url": "https://example.invalid/new",
            "file_id": "900000",
        }

    def test_never_downgrades(self, tmp_path: Path) -> None:
        """
        Tests that an older release does not replace newer metadata.
        """

        # given
        update_file: Path = tmp_path / "update.json"
        original: str = '{"version": "3.3.0", "download_url": "https://example.invalid"}'
        update_file.write_text(original, encoding="utf8")
        metadata = UpdateMetadata(
            version="3.2.7", download_url="https://example.invalid/new", file_id="900000"
        )

        # when
        written: bool = metadata.write(update_file)

        # then
        assert not written
        assert update_file.read_text(encoding="utf8") == original
