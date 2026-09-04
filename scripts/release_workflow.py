"""Utilities used by the tag release workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

NEXUS_URL_PATTERN = re.compile(
    r"^https://www\.nexusmods\.com/(?P<game>[a-z0-9-]+)/mods/(?P<mod_id>\d+)/?$"
)
NEXUS_V3_BASE_URL = "https://api.nexusmods.com/v3"
NEXUS_V1_BASE_URL = "https://api.nexusmods.com/v1"
USER_AGENT = "SSE-Auto-Translator release workflow"


class ReleaseError(RuntimeError):
    """Raised when release metadata or Nexus state is invalid."""


class RetryableReleaseError(ReleaseError):
    """Raised for temporary Nexus failures that may succeed on retry."""


@dataclass(frozen=True)
class ProjectMetadata:
    """Metadata required by the release workflow."""

    version: str
    tag: str
    description: str
    nexus_url: str
    game_domain: str
    public_mod_id: str
    archive_path: Path


@dataclass(frozen=True)
class NexusFileState:
    """Relevant state of an existing Nexus mod file."""

    file_id: str
    name: str
    version: str
    public_version_id: str


@dataclass(frozen=True)
class NexusReleaseState:
    """Current Nexus mod-page and file state."""

    mod_version: str
    file: NexusFileState


def normalize_version(version: str) -> str:
    """Normalize Nexus and Git version strings for comparison."""

    return version.strip().removeprefix("v")


def version_key(version: str) -> tuple[int, ...]:
    """Convert the project's numeric version format into a comparison key."""

    normalized = normalize_version(version)
    parts = normalized.split(".")
    if not parts or any(not part.isdecimal() for part in parts):
        raise ReleaseError(f"Unsupported release version '{version}'.")
    return tuple(int(part) for part in parts)


def load_project_metadata(project_file: Path, tag: str) -> ProjectMetadata:
    """Load project data and validate that the tag matches its version."""

    project = tomllib.loads(project_file.read_text(encoding="utf8"))["project"]
    version = str(project["version"])
    expected_tag = f"v{version}"
    if tag != expected_tag:
        raise ReleaseError(
            f"Tag '{tag}' does not match project version '{version}' "
            f"(expected '{expected_tag}')."
        )

    description = str(project["description"])
    try:
        nexus_url = str(project["urls"]["Nexus Mods"])
    except KeyError as error:
        raise ReleaseError(
            "pyproject.toml is missing project.urls.'Nexus Mods'."
        ) from error

    url_match = NEXUS_URL_PATTERN.fullmatch(nexus_url)
    if url_match is None:
        raise ReleaseError(f"Unsupported Nexus Mods project URL: {nexus_url}")

    return ProjectMetadata(
        version=version,
        tag=tag,
        description=description,
        nexus_url=nexus_url,
        game_domain=url_match.group("game"),
        public_mod_id=url_match.group("mod_id"),
        archive_path=Path("dist") / f"{description}_v{version}.zip",
    )


def extract_changelog(changelog_file: Path, tag: str) -> str:
    """Extract the body of a version section from the changelog."""

    changelog = changelog_file.read_text(encoding="utf8")
    heading = re.compile(rf"^#\s+{re.escape(tag)}(?:\s+.*)?$", re.MULTILINE)
    match = heading.search(changelog)
    if match is None:
        raise ReleaseError(f"No changelog section found for '{tag}'.")

    next_heading = re.search(r"^#\s+v\S+.*$", changelog[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(changelog)
    changes = changelog[match.end() : end].strip()
    if not changes:
        raise ReleaseError(f"Changelog section for '{tag}' is empty.")
    return changes


def create_release_notes(changes: str, download_url: str) -> str:
    """Create the GitHub Release body."""

    return f"## Changes\n\n{changes}\n\n## Download\n\n[{download_url}]({download_url})\n"


def update_update_json(update_file: Path, version: str, download_url: str) -> bool:
    """Update the application's remote update metadata."""

    if update_file.is_file():
        current = json.loads(update_file.read_text(encoding="utf8"))
        current_version = current.get("version")
        if isinstance(current_version, str) and version_key(
            current_version
        ) > version_key(version):
            return False

    data = {"version": normalize_version(version), "download_url": download_url}
    update_file.write_text(json.dumps(data, indent=4) + "\n", encoding="utf8")
    return True


def write_github_outputs(output_file: Path, values: dict[str, str]) -> None:
    """Append simple values to a GitHub Actions output file."""

    with output_file.open("a", encoding="utf8") as stream:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise ReleaseError(f"GitHub output '{key}' contains a newline.")
            stream.write(f"{key}={value}\n")


class NexusClient:
    """Small read-only client for resolving and verifying Nexus releases."""

    def __init__(self, api_key: str) -> None:
        """Create a client using an API key that remains in memory only."""

        if not api_key:
            raise ReleaseError("NEXUSMODS_API_KEY is not configured.")
        self.__api_key = api_key

    def __get_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={
                "apikey": self.__api_key,
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf8", errors="replace")[:500]
            error_type = (
                RetryableReleaseError
                if error.code == 429 or 500 <= error.code < 600
                else ReleaseError
            )
            raise error_type(
                f"Nexus API returned HTTP {error.code} for {url}: {detail}"
            ) from error
        except urllib.error.URLError as error:
            raise RetryableReleaseError(
                f"Nexus API request failed for {url}: {error.reason}"
            ) from error

        if not isinstance(result, dict):
            raise ReleaseError(f"Nexus API returned an invalid response for {url}.")
        return result

    def get_mod_version(self, game_domain: str, public_mod_id: str) -> str:
        """Get the version currently displayed on the Nexus mod page."""

        response = self.__get_json(
            f"{NEXUS_V1_BASE_URL}/games/{game_domain}/mods/{public_mod_id}.json"
        )
        version = response.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ReleaseError("Nexus mod response does not contain a version.")
        return version

    def get_internal_mod_id(self, game_domain: str, public_mod_id: str) -> str:
        """Resolve a game-scoped mod ID to the v3 internal ID."""

        response = self.__get_json(
            f"{NEXUS_V3_BASE_URL}/games/{game_domain}/mods/{public_mod_id}"
        )
        internal_id = response.get("data", {}).get("id")
        if not isinstance(internal_id, (str, int)) or str(internal_id) == "":
            raise ReleaseError("Nexus mod response does not contain an internal ID.")
        return str(internal_id)

    def get_mod_files(self, internal_mod_id: str) -> list[dict[str, Any]]:
        """Get all mod files belonging to a Nexus mod."""

        response = self.__get_json(
            f"{NEXUS_V3_BASE_URL}/mods/{internal_mod_id}/files"
        )
        files = response.get("data", {}).get("mod_files")
        if not isinstance(files, list):
            raise ReleaseError("Nexus files response does not contain a file list.")
        return [file for file in files if isinstance(file, dict)]

    def get_file_versions(self, file_id: str) -> list[dict[str, Any]]:
        """Get all published versions of a Nexus mod file."""

        response = self.__get_json(
            f"{NEXUS_V3_BASE_URL}/mod-files/{file_id}/versions"
        )
        versions = response.get("data", {}).get("versions")
        if not isinstance(versions, list):
            raise ReleaseError("Nexus versions response does not contain a version list.")
        return [version for version in versions if isinstance(version, dict)]

    @staticmethod
    def latest_version(versions: list[dict[str, Any]]) -> dict[str, Any]:
        """Select the newest version using its position in the update chain."""

        if not versions:
            raise ReleaseError("Nexus mod file has no versions.")

        def position(version: dict[str, Any]) -> Decimal:
            try:
                return Decimal(str(version["position"]))
            except (KeyError, InvalidOperation) as error:
                raise ReleaseError("Nexus file version has an invalid position.") from error

        return max(versions, key=position)

    def inspect_release(
        self,
        game_domain: str,
        public_mod_id: str,
        expected_file_name: str,
        file_id: str | None = None,
    ) -> NexusReleaseState:
        """Read and validate the current mod-page and target-file state."""

        mod_version = self.get_mod_version(game_domain, public_mod_id)
        internal_mod_id = self.get_internal_mod_id(game_domain, public_mod_id)
        files = self.get_mod_files(internal_mod_id)
        candidates = [
            file
            for file in files
            if file.get("is_active") is True
            and file.get("name") == expected_file_name
            and (file_id is None or str(file.get("id")) == file_id)
        ]
        if len(candidates) != 1:
            summary = [
                {
                    "id": file.get("id"),
                    "name": file.get("name"),
                    "is_active": file.get("is_active"),
                }
                for file in files
            ]
            raise ReleaseError(
                f"Expected exactly one active Nexus file named "
                f"'{expected_file_name}', found {len(candidates)}. Files: {summary}"
            )

        candidate = candidates[0]
        resolved_file_id = str(candidate["id"])
        latest = self.latest_version(self.get_file_versions(resolved_file_id))
        version = latest.get("version")
        public_version_id = latest.get("game_scoped_id")
        if not isinstance(version, str) or not version:
            raise ReleaseError("Latest Nexus file version has no version string.")
        if (
            not isinstance(public_version_id, (str, int))
            or str(public_version_id) == ""
        ):
            raise ReleaseError("Latest Nexus file version has no public file ID.")

        return NexusReleaseState(
            mod_version=mod_version,
            file=NexusFileState(
                file_id=resolved_file_id,
                name=expected_file_name,
                version=version,
                public_version_id=str(public_version_id),
            ),
        )


def direct_download_url(nexus_url: str, public_file_id: str) -> str:
    """Build a public Nexus file-tab link."""

    return f"{nexus_url}?tab=files&file_id={public_file_id}"


def command_prepare(args: argparse.Namespace) -> None:
    """Validate project metadata and prepare changelog outputs."""

    metadata = load_project_metadata(args.project_file, args.tag)
    changes = extract_changelog(args.changelog_file, metadata.tag)
    args.changes_file.write_text(changes + "\n", encoding="utf8")
    write_github_outputs(
        args.github_output,
        {
            "version": metadata.version,
            "tag": metadata.tag,
            "description": metadata.description,
            "nexus_url": metadata.nexus_url,
            "game_domain": metadata.game_domain,
            "public_mod_id": metadata.public_mod_id,
            "archive_path": str(metadata.archive_path),
            "changes_file": str(args.changes_file),
        },
    )


def command_resolve(args: argparse.Namespace) -> None:
    """Resolve the existing Nexus file and determine rerun state."""

    client = NexusClient(os.environ.get("NEXUSMODS_API_KEY", ""))
    state = client.inspect_release(
        args.game_domain, args.public_mod_id, args.file_name
    )
    file_matches_target = normalize_version(state.file.version) == normalize_version(
        args.target_version
    )
    versions_match = normalize_version(state.mod_version) == normalize_version(
        state.file.version
    )
    if not versions_match and not file_matches_target:
        raise ReleaseError(
            f"Nexus mod-page version '{state.mod_version}' does not match latest "
            f"file version '{state.file.version}'."
        )

    already_published = file_matches_target
    write_github_outputs(
        args.github_output,
        {
            "file_id": state.file.file_id,
            "already_published": str(already_published).lower(),
            "current_version": state.mod_version,
            "public_file_id": state.file.public_version_id,
        },
    )


def command_verify(args: argparse.Namespace) -> None:
    """Wait until Nexus exposes the newly published version."""

    client = NexusClient(os.environ.get("NEXUSMODS_API_KEY", ""))
    deadline = time.monotonic() + args.timeout
    last_state: NexusReleaseState | None = None
    last_retryable_error: RetryableReleaseError | None = None
    while time.monotonic() < deadline:
        try:
            last_state = client.inspect_release(
                args.game_domain,
                args.public_mod_id,
                args.file_name,
                file_id=args.file_id,
            )
        except RetryableReleaseError as error:
            last_retryable_error = error
            time.sleep(args.interval)
            continue
        if (
            normalize_version(last_state.mod_version)
            == normalize_version(args.target_version)
            == normalize_version(last_state.file.version)
        ):
            download_url = direct_download_url(
                args.nexus_url, last_state.file.public_version_id
            )
            write_github_outputs(
                args.github_output,
                {
                    "public_file_id": last_state.file.public_version_id,
                    "download_url": download_url,
                },
            )
            return
        time.sleep(args.interval)

    if last_state is None:
        detail = (
            f" Last transient error: {last_retryable_error}."
            if last_retryable_error
            else ""
        )
        raise ReleaseError(f"Timed out before Nexus returned release state.{detail}")
    raise ReleaseError(
        f"Timed out waiting for Nexus version '{args.target_version}'. "
        f"Mod page: '{last_state.mod_version}', file: '{last_state.file.version}'."
    )


def command_notes(args: argparse.Namespace) -> None:
    """Create GitHub Release notes containing the direct Nexus link."""

    changes = args.changes_file.read_text(encoding="utf8").strip()
    args.notes_file.write_text(
        create_release_notes(changes, args.download_url), encoding="utf8"
    )


def command_update_json(args: argparse.Namespace) -> None:
    """Write application update metadata after publishing."""

    update_update_json(args.update_file, args.version, args.download_url)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--tag", required=True)
    prepare.add_argument("--project-file", type=Path, default=Path("pyproject.toml"))
    prepare.add_argument("--changelog-file", type=Path, default=Path("Changelog.md"))
    prepare.add_argument("--changes-file", type=Path, required=True)
    prepare.add_argument("--github-output", type=Path, required=True)
    prepare.set_defaults(handler=command_prepare)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--game-domain", required=True)
    resolve.add_argument("--public-mod-id", required=True)
    resolve.add_argument("--file-name", required=True)
    resolve.add_argument("--target-version", required=True)
    resolve.add_argument("--github-output", type=Path, required=True)
    resolve.set_defaults(handler=command_resolve)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--game-domain", required=True)
    verify.add_argument("--public-mod-id", required=True)
    verify.add_argument("--file-name", required=True)
    verify.add_argument("--file-id", required=True)
    verify.add_argument("--target-version", required=True)
    verify.add_argument("--nexus-url", required=True)
    verify.add_argument("--timeout", type=int, default=600)
    verify.add_argument("--interval", type=int, default=15)
    verify.add_argument("--github-output", type=Path, required=True)
    verify.set_defaults(handler=command_verify)

    notes = subparsers.add_parser("notes")
    notes.add_argument("--changes-file", type=Path, required=True)
    notes.add_argument("--download-url", required=True)
    notes.add_argument("--notes-file", type=Path, required=True)
    notes.set_defaults(handler=command_notes)

    update_json = subparsers.add_parser("update-json")
    update_json.add_argument("--update-file", type=Path, default=Path("update.json"))
    update_json.add_argument("--version", required=True)
    update_json.add_argument("--download-url", required=True)
    update_json.set_defaults(handler=command_update_json)
    return parser


def main() -> None:
    """Run the requested release helper command."""

    args = create_parser().parse_args()
    try:
        args.handler(args)
    except ReleaseError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
