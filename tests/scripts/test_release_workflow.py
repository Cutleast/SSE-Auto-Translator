"""Tests for the release workflow helpers."""

import json
import urllib.error
from argparse import Namespace
from email.message import Message
from io import BytesIO
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from scripts.release_workflow import (
    NexusClient,
    NexusFileState,
    NexusReleaseState,
    ReleaseError,
    RetryableReleaseError,
    command_resolve,
    command_verify,
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


def test_update_json_does_not_overwrite_newer_version(tmp_path: Path) -> None:
    """A delayed older release cannot downgrade update metadata."""

    update_file = tmp_path / "update.json"
    current = {"version": "3.3.0", "download_url": "https://example.com/new"}
    update_file.write_text(json.dumps(current), encoding="utf8")

    changed = update_update_json(update_file, "v3.2.3", "https://example.com/old")

    assert changed is False
    assert json.loads(update_file.read_text(encoding="utf8")) == current


def test_latest_nexus_version_uses_update_chain_position() -> None:
    """The latest Nexus version is selected by its decimal chain position."""

    versions = [
        {"version": "v2.0.0", "position": "2.0"},
        {"version": "v10.0.0", "position": "10.0"},
        {"version": "v3.0.0", "position": "3.0"},
    ]

    assert NexusClient.latest_version(versions)["version"] == "v10.0.0"


@pytest.mark.parametrize("status", [429, 500, 503])
def test_nexus_client_classifies_transient_http_errors(
    status: int, mocker: MockerFixture
) -> None:
    """Rate limits and server failures can be retried during verification."""

    error = urllib.error.HTTPError(
        "https://api.nexusmods.com/test",
        status,
        "temporary failure",
        hdrs=Message(),
        fp=BytesIO(b"temporary failure"),
    )
    mocker.patch("scripts.release_workflow.urllib.request.urlopen", side_effect=error)

    with pytest.raises(RetryableReleaseError):
        NexusClient("test-key").get_mod_version("game", "1")


def test_nexus_client_classifies_network_error_as_transient(
    mocker: MockerFixture,
) -> None:
    """Network failures can be retried during verification."""

    mocker.patch(
        "scripts.release_workflow.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection reset"),
    )

    with pytest.raises(RetryableReleaseError):
        NexusClient("test-key").get_mod_version("game", "1")


def test_nexus_client_keeps_permanent_http_error_non_retryable(
    mocker: MockerFixture,
) -> None:
    """Authentication and other permanent failures still abort immediately."""

    error = urllib.error.HTTPError(
        "https://api.nexusmods.com/test",
        401,
        "unauthorized",
        hdrs=Message(),
        fp=BytesIO(b"unauthorized"),
    )
    mocker.patch("scripts.release_workflow.urllib.request.urlopen", side_effect=error)

    with pytest.raises(ReleaseError) as raised:
        NexusClient("test-key").get_mod_version("game", "1")

    assert not isinstance(raised.value, RetryableReleaseError)


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


def test_resolve_treats_target_file_with_stale_mod_page_as_rerun(
    tmp_path: Path,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A propagated file version prevents a duplicate upload on rerun."""

    output = tmp_path / "output.txt"
    monkeypatch.setenv("NEXUSMODS_API_KEY", "test-key")
    mocker.patch.object(
        NexusClient,
        "inspect_release",
        return_value=NexusReleaseState(
            mod_version="v3.2.2",
            file=NexusFileState(
                file_id="target",
                name="SSE Auto Translator",
                version="v3.2.3",
                public_version_id="42",
            ),
        ),
    )

    command_resolve(
        Namespace(
            game_domain="skyrimspecialedition",
            public_mod_id="111491",
            file_name="SSE Auto Translator",
            target_version="v3.2.3",
            github_output=output,
        )
    )

    assert "already_published=true" in output.read_text(encoding="utf8")


def test_verify_retries_transient_failure_then_succeeds(
    tmp_path: Path,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Temporary Nexus failures do not abort propagation polling."""

    output = tmp_path / "output.txt"
    monkeypatch.setenv("NEXUSMODS_API_KEY", "test-key")
    inspect_release = mocker.patch.object(
        NexusClient,
        "inspect_release",
        side_effect=[
            RetryableReleaseError("temporarily unavailable"),
            NexusReleaseState(
                mod_version="v3.2.3",
                file=NexusFileState(
                    file_id="target",
                    name="SSE Auto Translator",
                    version="v3.2.3",
                    public_version_id="43",
                ),
            ),
        ],
    )
    sleep = mocker.patch("scripts.release_workflow.time.sleep")

    command_verify(
        Namespace(
            game_domain="skyrimspecialedition",
            public_mod_id="111491",
            file_name="SSE Auto Translator",
            file_id="target",
            target_version="v3.2.3",
            nexus_url="https://www.nexusmods.com/skyrimspecialedition/mods/111491",
            timeout=10,
            interval=1,
            github_output=output,
        )
    )

    assert inspect_release.call_count == 2
    sleep.assert_called_once_with(1)
    assert "public_file_id=43" in output.read_text(encoding="utf8").splitlines()


@pytest.mark.parametrize(
    ("actual", "expected"),
    [("v3.2.2", "3.2.2"), ("3.2.2", "3.2.2")],
)
def test_normalize_version(actual: str, expected: str) -> None:
    """Version comparison accepts an optional leading v."""

    assert normalize_version(actual) == expected
