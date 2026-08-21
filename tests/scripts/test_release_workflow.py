"""Tests for the release workflow helpers."""

import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from scripts.release_workflow import (
    NexusClient,
    ReleaseError,
    create_release_notes,
    direct_download_url,
    extract_changelog,
    load_project_metadata,
    normalize_version,
    update_update_json,
)


def test_load_project_metadata_validates_tag_and_nexus_url(tmp_path: Path) -> None:
    """Project metadata is derived from one authoritative TOML file."""

    project_file = tmp_path / "pyproject.toml"
    project_file.write_text(
        """
[project]
version = "3.2.2"
description = "SSE Auto Translator"

[project.urls]
"Nexus Mods" = "https://www.nexusmods.com/skyrimspecialedition/mods/111491"
""".strip(),
        encoding="utf8",
    )

    metadata = load_project_metadata(project_file, "v3.2.2")

    assert metadata.version == "3.2.2"
    assert metadata.game_domain == "skyrimspecialedition"
    assert metadata.public_mod_id == "111491"
    assert metadata.archive_path == Path("dist/SSE Auto Translator_v3.2.2.zip")


def test_load_project_metadata_rejects_mismatching_tag(tmp_path: Path) -> None:
    """A release tag cannot differ from the project version."""

    project_file = tmp_path / "pyproject.toml"
    project_file.write_text(
        """
[project]
version = "3.2.2"
description = "SSE Auto Translator"

[project.urls]
"Nexus Mods" = "https://www.nexusmods.com/skyrimspecialedition/mods/111491"
""".strip(),
        encoding="utf8",
    )

    with pytest.raises(ReleaseError, match="does not match"):
        load_project_metadata(project_file, "v3.2.3")


def test_extract_changelog_accepts_annotated_heading(tmp_path: Path) -> None:
    """Only the requested version section is included in release notes."""

    changelog = tmp_path / "Changelog.md"
    changelog.write_text(
        "# v3.2.2 (Hotfix)\n\n- First\n- Second\n\n# v3.2.1\n\n- Old\n",
        encoding="utf8",
    )

    assert extract_changelog(changelog, "v3.2.2") == "- First\n- Second"


def test_release_notes_include_direct_nexus_link() -> None:
    """GitHub notes point at the newly published Nexus file version."""

    url = "https://www.nexusmods.com/game/mods/1?tab=files&file_id=42"

    notes = create_release_notes("- Fixed", url)

    assert notes == f"## Changes\n\n- Fixed\n\n## Download\n\n[{url}]({url})\n"


def test_update_json_uses_version_without_v_prefix(tmp_path: Path) -> None:
    """Application update metadata remains compatible with semantic-version."""

    update_file = tmp_path / "update.json"
    url = "https://www.nexusmods.com/game/mods/1?tab=files&file_id=42"

    update_update_json(update_file, "v3.2.3", url)

    assert json.loads(update_file.read_text(encoding="utf8")) == {
        "version": "3.2.3",
        "download_url": url,
    }


def test_latest_nexus_version_uses_update_chain_position() -> None:
    """The latest Nexus version is selected by its decimal chain position."""

    versions = [
        {"version": "v2.0.0", "position": "2.0"},
        {"version": "v10.0.0", "position": "10.0"},
        {"version": "v3.0.0", "position": "3.0"},
    ]

    assert NexusClient.latest_version(versions)["version"] == "v10.0.0"


def test_inspect_release_resolves_unique_active_named_file(
    mocker: MockerFixture,
) -> None:
    """File resolution combines project name, active state and latest version."""

    client = NexusClient("test-key")
    mocker.patch.object(client, "get_mod_version", return_value="v3.2.2")
    mocker.patch.object(client, "get_internal_mod_id", return_value="internal-mod")
    mocker.patch.object(
        client,
        "get_mod_files",
        return_value=[
            {"id": "target", "name": "SSE Auto Translator", "is_active": True},
            {"id": "old", "name": "SSE Auto Translator", "is_active": False},
        ],
    )
    mocker.patch.object(
        client,
        "get_file_versions",
        return_value=[
            {
                "version": "v3.2.2",
                "position": "36",
                "game_scoped_id": "786690",
            }
        ],
    )

    state = client.inspect_release(
        "skyrimspecialedition", "111491", "SSE Auto Translator"
    )

    assert state.mod_version == "v3.2.2"
    assert state.file.file_id == "target"
    assert state.file.public_version_id == "786690"


def test_direct_download_url_uses_public_file_id() -> None:
    """The update URL uses the public game-scoped version ID."""

    assert direct_download_url("https://www.nexusmods.com/game/mods/1", "42") == (
        "https://www.nexusmods.com/game/mods/1?tab=files&file_id=42"
    )


def test_inspect_release_accepts_numeric_public_file_id(
    mocker: MockerFixture,
) -> None:
    """Numeric Nexus IDs are normalized for use in the direct link."""

    client = NexusClient("test-key")
    mocker.patch.object(client, "get_mod_version", return_value="v3.2.2")
    mocker.patch.object(client, "get_internal_mod_id", return_value="internal-mod")
    mocker.patch.object(
        client,
        "get_mod_files",
        return_value=[
            {"id": "target", "name": "SSE Auto Translator", "is_active": True}
        ],
    )
    mocker.patch.object(
        client,
        "get_file_versions",
        return_value=[
            {"version": "v3.2.2", "position": "36", "game_scoped_id": 786690}
        ],
    )

    state = client.inspect_release(
        "skyrimspecialedition", "111491", "SSE Auto Translator"
    )

    assert state.file.public_version_id == "786690"


@pytest.mark.parametrize(
    ("actual", "expected"),
    [("v3.2.2", "3.2.2"), ("3.2.2", "3.2.2")],
)
def test_normalize_version(actual: str, expected: str) -> None:
    """Version comparison accepts an optional leading v."""

    assert normalize_version(actual) == expected
