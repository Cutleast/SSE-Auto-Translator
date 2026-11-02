"""
Copyright (c) Cutleast
"""

import re
import tomllib
from pathlib import Path
from typing import Any, Optional, Self

import semantic_version as semver
from pydantic import BaseModel

from .release_error import ReleaseError


class ReleaseMetadata(BaseModel, frozen=True):
    """
    Release information derived from the project file and the pushed tag.
    """

    version: str
    """The project version, e.g. `3.2.7` or `3.3.0-dev-3`."""

    tag: str
    """The Git tag of the release, e.g. `v3.2.7`."""

    prerelease: bool
    """Whether the version is a prerelease, which is never published to users."""

    display_name: str
    """The display name of the application, used for the archive and Nexus Mods."""

    archive_path: Path
    """Path of the release archive created by `build.bat`, relative to the project."""

    depends_on_bethkit: bool
    """Whether the application bundles the native bethkit library."""

    @classmethod
    def load(cls, project_file: Path, tag: str) -> Self:
        """
        Loads the release metadata and checks that the tag matches the project version.

        Args:
            project_file (Path): Path to `pyproject.toml`.
            tag (str): The pushed Git tag.

        Raises:
            ReleaseError: The tag does not match the project version.

        Returns:
            Self: The release metadata.
        """

        project: dict[str, Any] = tomllib.loads(project_file.read_text(encoding="utf8"))[
            "project"
        ]
        version: str = str(project["version"])
        if tag != f"v{version}":
            raise ReleaseError(
                f"Tag '{tag}' does not match project version '{version}' "
                f"(expected 'v{version}')."
            )

        try:
            parsed_version = semver.Version(version)
        except ValueError as ex:
            raise ReleaseError(f"Unsupported project version '{version}'.") from ex

        # The build uses the project description as display name (see core-lib's
        # BuildMetadata), so the archive name is derived the same way.
        display_name: str = str(project.get("description", project["name"]))
        dependencies: list[str] = [str(dep) for dep in project.get("dependencies", [])]

        return cls(
            version=version,
            tag=tag,
            prerelease=bool(parsed_version.prerelease),
            display_name=display_name,
            archive_path=Path("dist") / f"{display_name}_v{parsed_version}.zip",
            depends_on_bethkit=any(
                re.match(r"bethkit\b", dependency) for dependency in dependencies
            ),
        )

    @staticmethod
    def extract_changes(changelog_file: Path, tag: str) -> str:
        """
        Extracts the changelog section of a release.

        Sections start with a level-one heading containing the tag, for example
        `# v3.2.6 (Hotfix)`.

        Args:
            changelog_file (Path): Path to `Changelog.md`.
            tag (str): The tag of the release.

        Raises:
            ReleaseError: The changelog has no or an empty section for the tag.

        Returns:
            str: The body of the changelog section.
        """

        changelog: str = changelog_file.read_text(encoding="utf8")
        heading: re.Pattern[str] = re.compile(
            rf"^#\s+{re.escape(tag)}(?:\s+.*)?$", re.MULTILINE
        )
        match: Optional[re.Match[str]] = heading.search(changelog)
        if match is None:
            raise ReleaseError(f"No changelog section found for '{tag}'.")

        next_heading: Optional[re.Match[str]] = re.search(
            r"^#\s+v\S+.*$", changelog[match.end() :], re.MULTILINE
        )
        end: int = match.end() + next_heading.start() if next_heading else len(changelog)
        changes: str = changelog[match.end() : end].strip()
        if not changes:
            raise ReleaseError(f"Changelog section for '{tag}' is empty.")

        return changes
