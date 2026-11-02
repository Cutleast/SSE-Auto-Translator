"""
Copyright (c) Cutleast

Command-line entry point of the release helpers, run as `python -m scripts.release`.
"""

import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional

from .nexus_client import NexusClient
from .nexus_file_version import NexusFileVersion
from .release_error import ReleaseError
from .release_metadata import ReleaseMetadata
from .target_branch_resolver import TargetBranchResolver
from .update_metadata import UpdateMetadata

EXE_NAME: str = "SSE-AT.exe"
"""Name of the application executable inside the release archive."""

BETHKIT_LIBRARY: str = "bethkit/bethkit_ffi.dll"
"""Path of the native bethkit library relative to the executable."""


def write_github_outputs(output_file: Path, values: dict[str, str]) -> None:
    """
    Appends single-line values to a GitHub Actions output file.

    Args:
        output_file (Path): The file referenced by `$GITHUB_OUTPUT`.
        values (dict[str, str]): Output names and values.

    Raises:
        ReleaseError: A value contains a line break.
    """

    with output_file.open("a", encoding="utf8") as stream:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise ReleaseError(f"GitHub output '{key}' contains a line break.")
            stream.write(f"{key}={value}\n")


def command_prepare(args: argparse.Namespace) -> None:
    """
    Validates the tag, determines the target branch and extracts the changelog.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Raises:
        ReleaseError: The release cannot be published.
    """

    metadata: ReleaseMetadata = ReleaseMetadata.load(args.project_file, args.tag)
    changes: str = ReleaseMetadata.extract_changes(args.changelog_file, metadata.tag)
    target_branch: str = TargetBranchResolver.resolve_from_git(
        args.commit, args.default_branch
    )
    print(f"Release {metadata.tag} targets branch '{target_branch}'.")

    args.changes_file.write_text(changes + "\n", encoding="utf8")
    write_github_outputs(
        args.github_output,
        {
            "version": metadata.version,
            "tag": metadata.tag,
            "prerelease": str(metadata.prerelease).lower(),
            "display_name": metadata.display_name,
            "archive_path": metadata.archive_path.as_posix(),
            "archive_name": metadata.archive_path.name,
            "target_branch": target_branch,
        },
    )


def command_verify_archive(args: argparse.Namespace) -> None:
    """
    Checks that the release archive contains the application and writes its checksum.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Raises:
        ReleaseError: The archive is missing or incomplete.
    """

    metadata: ReleaseMetadata = ReleaseMetadata.load(args.project_file, args.tag)
    archive: Path = metadata.archive_path
    if not archive.is_file():
        raise ReleaseError(f"Release archive '{archive}' was not created.")

    with zipfile.ZipFile(archive) as zip_file:
        names: list[str] = zip_file.namelist()

    exe_paths: list[str] = [name for name in names if name.split("/")[-1] == EXE_NAME]
    if len(exe_paths) != 1:
        raise ReleaseError(f"Expected exactly one '{EXE_NAME}' in '{archive}'.")

    app_folder: str = exe_paths[0].removesuffix(EXE_NAME)
    if metadata.depends_on_bethkit and app_folder + BETHKIT_LIBRARY not in names:
        # Nuitka does not detect libraries that are loaded via ctypes.
        raise ReleaseError(
            f"'{archive}' does not contain '{BETHKIT_LIBRARY}' next to '{EXE_NAME}'."
        )

    digest: str = hashlib.sha256(archive.read_bytes()).hexdigest()
    args.checksum_file.write_text(f"{digest} *{archive.name}\n", encoding="utf8")
    print(f"Verified '{archive}' (SHA-256 {digest}).")


def command_nexus_resolve(args: argparse.Namespace) -> None:
    """
    Checks whether the version was already published to the Nexus Mods file.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Raises:
        ReleaseError: The version exists more than once or Nexus Mods is unavailable.
    """

    client = NexusClient(os.environ.get("NEXUSMODS_API_KEY", ""))
    existing: list[NexusFileVersion] = [
        version
        for version in client.get_file_versions(args.file_id)
        if version.version.removeprefix("v") == args.version.removeprefix("v")
    ]
    if len(existing) > 1:
        raise ReleaseError(
            f"Version '{args.version}' exists {len(existing)} times on Nexus Mods."
        )

    write_github_outputs(
        args.github_output,
        {
            "already_published": str(bool(existing)).lower(),
            "version_id": existing[0].id if existing else "",
        },
    )


def command_nexus_lookup(args: argparse.Namespace) -> None:
    """
    Looks up the public file ID of an uploaded version and builds its download link.

    The upload action only returns the API identifier of the new version, while the
    download link requires the public (game-scoped) file ID.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Raises:
        ReleaseError: The version does not belong to the file or has another version.
    """

    client = NexusClient(os.environ.get("NEXUSMODS_API_KEY", ""))
    version: NexusFileVersion = client.get_version(args.version_id)
    if version.file_id != args.file_id:
        raise ReleaseError(
            f"Nexus Mods version {version.id} belongs to file {version.file_id}, "
            f"expected {args.file_id}."
        )
    if version.version.removeprefix("v") != args.version.removeprefix("v"):
        raise ReleaseError(
            f"Nexus Mods version {version.id} has version '{version.version}', "
            f"expected '{args.version}'."
        )

    download_url: str = UpdateMetadata.download_url_for(
        args.game_domain, args.mod_id, version.game_scoped_id
    )
    print(f"Published as file {version.game_scoped_id}: {download_url}")
    write_github_outputs(
        args.github_output,
        {"public_file_id": version.game_scoped_id, "download_url": download_url},
    )


def command_notes(args: argparse.Namespace) -> None:
    """
    Creates the GitHub Release notes.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """

    notes: str = "## Changes\n\n" + args.changes_file.read_text(encoding="utf8").strip()
    download_url: Optional[str] = args.download_url or None
    if download_url is not None:
        notes += f"\n\n## Download\n\n[Nexus Mods]({download_url})"

    args.notes_file.write_text(notes + "\n", encoding="utf8")


def command_update_json(args: argparse.Namespace) -> None:
    """
    Writes `update.json` for a published release.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """

    metadata = UpdateMetadata(
        version=args.version.removeprefix("v"),
        download_url=args.download_url,
        file_id=args.file_id,
    )
    if metadata.write(args.update_file):
        print(f"Updated '{args.update_file}' to {metadata.version}.")
    else:
        print(f"'{args.update_file}' already announces a newer version.")


def create_parser() -> argparse.ArgumentParser:
    """
    Creates the command-line parser.

    Returns:
        argparse.ArgumentParser: The parser with one subcommand per workflow step.
    """

    parser = argparse.ArgumentParser(prog="python -m scripts.release")
    commands = parser.add_subparsers(required=True)

    prepare = commands.add_parser("prepare")
    prepare.add_argument("--tag", required=True)
    prepare.add_argument("--commit", required=True)
    prepare.add_argument("--default-branch", required=True)
    prepare.add_argument("--project-file", type=Path, default=Path("pyproject.toml"))
    prepare.add_argument("--changelog-file", type=Path, default=Path("Changelog.md"))
    prepare.add_argument("--changes-file", type=Path, required=True)
    prepare.add_argument("--github-output", type=Path, required=True)
    prepare.set_defaults(handler=command_prepare)

    verify_archive = commands.add_parser("verify-archive")
    verify_archive.add_argument("--tag", required=True)
    verify_archive.add_argument(
        "--project-file", type=Path, default=Path("pyproject.toml")
    )
    verify_archive.add_argument("--checksum-file", type=Path, required=True)
    verify_archive.set_defaults(handler=command_verify_archive)

    nexus_resolve = commands.add_parser("nexus-resolve")
    nexus_resolve.add_argument("--file-id", required=True)
    nexus_resolve.add_argument("--version", required=True)
    nexus_resolve.add_argument("--github-output", type=Path, required=True)
    nexus_resolve.set_defaults(handler=command_nexus_resolve)

    nexus_lookup = commands.add_parser("nexus-lookup")
    nexus_lookup.add_argument("--file-id", required=True)
    nexus_lookup.add_argument("--version-id", required=True)
    nexus_lookup.add_argument("--version", required=True)
    nexus_lookup.add_argument("--game-domain", required=True)
    nexus_lookup.add_argument("--mod-id", required=True)
    nexus_lookup.add_argument("--github-output", type=Path, required=True)
    nexus_lookup.set_defaults(handler=command_nexus_lookup)

    notes = commands.add_parser("notes")
    notes.add_argument("--changes-file", type=Path, required=True)
    notes.add_argument("--download-url", default="")
    notes.add_argument("--notes-file", type=Path, required=True)
    notes.set_defaults(handler=command_notes)

    update_json = commands.add_parser("update-json")
    update_json.add_argument("--update-file", type=Path, default=Path("update.json"))
    update_json.add_argument("--version", required=True)
    update_json.add_argument("--download-url", required=True)
    update_json.add_argument("--file-id", required=True)
    update_json.set_defaults(handler=command_update_json)

    return parser


def main() -> None:
    """
    Runs the requested release helper command.
    """

    args: argparse.Namespace = create_parser().parse_args()
    try:
        args.handler(args)
    except ReleaseError as ex:
        print(f"error: {ex}", file=sys.stderr)
        raise SystemExit(1) from ex


if __name__ == "__main__":
    main()
