"""
Copyright (c) Cutleast
"""

import argparse
import zipfile
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from scripts.release import __main__ as cli
from scripts.release.nexus_file_version import NexusFileVersion
from scripts.release.release_error import ReleaseError


class TestReleaseCli:
    """
    Tests the commands in `scripts.release.__main__`.
    """

    @staticmethod
    def create_project(
        root: Path, monkeypatch: pytest.MonkeyPatch, *, bethkit: bool
    ) -> Path:
        """
        Creates a project file and switches into its folder.

        Args:
            root (Path): Project root folder.
            monkeypatch (pytest.MonkeyPatch): Used to change the working directory.
            bethkit (bool): Whether the project depends on bethkit.

        Returns:
            Path: Path of the release archive expected by the release helpers.
        """

        dependencies: str = '"bethkit"' if bethkit else ""
        (root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "sse-auto-translator"\n'
            'version = "3.2.7"\n'
            'description = "SSE Auto Translator"\n'
            f"dependencies = [{dependencies}]\n",
            encoding="utf8",
        )
        monkeypatch.chdir(root)
        archive: Path = root / "dist" / "SSE Auto Translator_v3.2.7.zip"
        archive.parent.mkdir()
        return archive

    @staticmethod
    def verify_archive(root: Path) -> None:
        """
        Runs the `verify-archive` command.

        Args:
            root (Path): Project root folder.
        """

        cli.command_verify_archive(
            argparse.Namespace(
                tag="v3.2.7",
                project_file=Path("pyproject.toml"),
                checksum_file=root / "SHA256SUMS.txt",
            )
        )

    def test_verify_archive_with_bethkit_library(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that a complete archive is accepted and its checksum is written.
        """

        # given
        archive: Path = TestReleaseCli.create_project(
            tmp_path, monkeypatch, bethkit=True
        )
        with zipfile.ZipFile(archive, "w") as zip_file:
            zip_file.writestr("SSE-AT/SSE-AT.exe", b"exe")
            zip_file.writestr("SSE-AT/bethkit/bethkit_ffi.dll", b"dll")

        # when
        TestReleaseCli.verify_archive(tmp_path)

        # then
        checksum: str = (tmp_path / "SHA256SUMS.txt").read_text(encoding="utf8")
        assert checksum.endswith(" *SSE Auto Translator_v3.2.7.zip\n")

    def test_verify_archive_without_bethkit_library(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that a build missing the native bethkit library is rejected.
        """

        # given
        archive: Path = TestReleaseCli.create_project(
            tmp_path, monkeypatch, bethkit=True
        )
        with zipfile.ZipFile(archive, "w") as zip_file:
            zip_file.writestr("SSE-AT/SSE-AT.exe", b"exe")
            zip_file.writestr("SSE-AT/bethkit/licenses/LICENSE", b"license")

        # then
        with pytest.raises(ReleaseError, match="bethkit_ffi.dll"):
            TestReleaseCli.verify_archive(tmp_path)

    def test_verify_archive_without_bethkit_dependency(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that the bethkit library is only required if the project depends on it.
        """

        # given
        archive: Path = TestReleaseCli.create_project(
            tmp_path, monkeypatch, bethkit=False
        )
        with zipfile.ZipFile(archive, "w") as zip_file:
            zip_file.writestr("SSE-AT/SSE-AT.exe", b"exe")

        # when
        TestReleaseCli.verify_archive(tmp_path)

        # then
        assert (tmp_path / "SHA256SUMS.txt").is_file()

    def test_nexus_lookup_writes_public_file_id(
        self, tmp_path: Path, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that the public file ID of the uploaded version becomes the download link.
        """

        # given
        monkeypatch.setenv("NEXUSMODS_API_KEY", "key")
        mocker.patch(
            "scripts.release.nexus_client.NexusClient.get_version",
            return_value=NexusFileVersion(
                id="7318627000000",
                game_scoped_id="900000",
                version="v3.2.7",
                file_id="3176167",
            ),
        )
        output: Path = tmp_path / "output.txt"

        # when
        cli.command_nexus_lookup(
            argparse.Namespace(
                file_id="3176167",
                version_id="7318627000000",
                version="v3.2.7",
                game_domain="skyrimspecialedition",
                mod_id="111491",
                github_output=output,
            )
        )

        # then
        assert output.read_text(encoding="utf8").splitlines() == [
            "public_file_id=900000",
            (
                "download_url=https://www.nexusmods.com/skyrimspecialedition/mods/111491"
                "?tab=files&file_id=900000"
            ),
        ]

    def test_nexus_lookup_rejects_foreign_file(
        self, tmp_path: Path, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that a version of another mod file is never written to update.json.
        """

        # given
        monkeypatch.setenv("NEXUSMODS_API_KEY", "key")
        mocker.patch(
            "scripts.release.nexus_client.NexusClient.get_version",
            return_value=NexusFileVersion(
                id="7318627000000",
                game_scoped_id="900000",
                version="v3.2.7",
                file_id="1234",
            ),
        )

        # then
        with pytest.raises(ReleaseError, match="belongs to file 1234"):
            cli.command_nexus_lookup(
                argparse.Namespace(
                    file_id="3176167",
                    version_id="7318627000000",
                    version="v3.2.7",
                    game_domain="skyrimspecialedition",
                    mod_id="111491",
                    github_output=tmp_path / "output.txt",
                )
            )

    def test_nexus_file_version_from_api(self) -> None:
        """
        Tests reading a v3 `ModFileVersion` object.
        """

        # when
        version: NexusFileVersion = NexusFileVersion.from_api(
            {
                "id": "7318627000000",
                "game_scoped_id": "900000",
                "version": "v3.2.7",
                "file": {"id": "3176167", "name": "SSE Auto Translator"},
                "position": "12",
            }
        )

        # then
        assert version.file_id == "3176167"
        assert version.game_scoped_id == "900000"
