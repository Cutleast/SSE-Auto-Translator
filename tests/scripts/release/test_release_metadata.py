"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from scripts.release.release_error import ReleaseError
from scripts.release.release_metadata import ReleaseMetadata


class TestReleaseMetadata:
    """
    Tests `scripts.release.release_metadata.ReleaseMetadata`.
    """

    @staticmethod
    def write_project(
        folder: Path, version: str, dependencies: tuple[str, ...] = ()
    ) -> Path:
        """
        Writes a minimal project file.

        Args:
            folder (Path): Folder to write `pyproject.toml` to.
            version (str): Project version.
            dependencies (tuple[str, ...], optional): Project dependencies.

        Returns:
            Path: Path to the project file.
        """

        dependency_list: str = ", ".join(f'"{dep}"' for dep in dependencies)
        project_file: Path = folder / "pyproject.toml"
        project_file.write_text(
            "[project]\n"
            'name = "sse-auto-translator"\n'
            f'version = "{version}"\n'
            'description = "SSE Auto Translator"\n'
            f"dependencies = [{dependency_list}]\n",
            encoding="utf8",
        )
        return project_file

    def test_stable_release(self, tmp_path: Path) -> None:
        """
        Tests the metadata of a stable release.
        """

        # given
        project_file: Path = TestReleaseMetadata.write_project(tmp_path, "3.2.7")

        # when
        metadata: ReleaseMetadata = ReleaseMetadata.load(project_file, "v3.2.7")

        # then
        assert not metadata.prerelease
        assert metadata.archive_path == Path("dist") / "SSE Auto Translator_v3.2.7.zip"
        assert not metadata.depends_on_bethkit

    def test_prerelease(self, tmp_path: Path) -> None:
        """
        Tests that development versions are detected as prereleases.
        """

        # given
        project_file: Path = TestReleaseMetadata.write_project(
            tmp_path, "3.3.0-dev-3", ("bethkit>=2.6.0", "PySide6")
        )

        # when
        metadata: ReleaseMetadata = ReleaseMetadata.load(project_file, "v3.3.0-dev-3")

        # then
        assert metadata.prerelease
        assert metadata.depends_on_bethkit

    def test_tag_must_match_version(self, tmp_path: Path) -> None:
        """
        Tests that a tag not matching the project version is rejected.
        """

        # given
        project_file: Path = TestReleaseMetadata.write_project(tmp_path, "3.2.7")

        # then
        with pytest.raises(ReleaseError, match="does not match"):
            ReleaseMetadata.load(project_file, "v3.2.8")

    def test_extract_changes(self, tmp_path: Path) -> None:
        """
        Tests that only the section of the requested version is extracted.
        """

        # given
        changelog: Path = tmp_path / "Changelog.md"
        changelog.write_text(
            "# v3.2.7 (Hotfix)\n\n- Fix A\n- Fix B\n\n# v3.2.6\n\n- Old fix\n",
            encoding="utf8",
        )

        # when
        changes: str = ReleaseMetadata.extract_changes(changelog, "v3.2.7")

        # then
        assert changes == "- Fix A\n- Fix B"

    def test_missing_changelog_section(self, tmp_path: Path) -> None:
        """
        Tests that a release without changelog section is rejected.
        """

        # given
        changelog: Path = tmp_path / "Changelog.md"
        changelog.write_text("# v3.2.6\n\n- Old fix\n", encoding="utf8")

        # then
        with pytest.raises(ReleaseError, match="No changelog section"):
            ReleaseMetadata.extract_changes(changelog, "v3.2.7")
