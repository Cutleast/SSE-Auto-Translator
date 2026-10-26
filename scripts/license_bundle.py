"""
Copyright (c) Cutleast

Collects release notices, dependency versions and application source.
"""

import json
import re
import shutil
import subprocess
import sys
import tomllib
from importlib.metadata import Distribution, distribution
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from packaging.markers import Marker


def collect_dependencies(project_root: Path, output: Path) -> None:
    """
    Copies installed runtime dependency notices and records their locked sources.

    Args:
        project_root (Path): Root of the build checkout.
        output (Path): Directory for the dependency inventory and license files.

    Raises:
        RuntimeError: A package differs from its locked version or has no notices.
        FileNotFoundError: The interpreter's license text cannot be found.
    """

    project: dict[str, Any] = tomllib.loads(
        (project_root / "pyproject.toml").read_text(encoding="utf-8")
    )
    lock: dict[str, Any] = tomllib.loads(
        (project_root / "uv.lock").read_text(encoding="utf-8")
    )
    packages: dict[str, dict[str, Any]] = {
        package["name"]: package for package in lock["package"]
    }
    pending: list[str] = [
        re.split(r"[\[ ;<>=!~]", requirement, maxsplit=1)[0]
        for requirement in project["project"]["dependencies"]
    ]
    inventory: dict[str, Any] = {}
    output.mkdir(parents=True, exist_ok=True)

    while pending:
        name: str = re.sub(r"[-_.]+", "-", pending.pop()).lower()
        if name in inventory:
            continue

        package: dict[str, Any] = packages[name]
        installed: Distribution = distribution(name)
        if installed.version != package["version"]:
            raise RuntimeError(
                f"'{name}' is '{installed.version}', expected '{package['version']}'. "
                "Run 'uv sync --locked' before building."
            )

        notices: list[str] = []
        for file in installed.files or []:
            if not any(
                word in file.name.lower()
                for word in ("license", "licence", "copying", "notice", "copyright")
            ):
                continue

            source = Path(str(installed.locate_file(file)))
            if source.is_file():
                destination: Path = output / name / f"{len(notices):03d}-{source.name}"
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                notices.append(destination.relative_to(output).as_posix())

        fallback: Path = project_root / "res" / "licenses" / f"{name}-LICENSE.txt"
        if not notices and fallback.is_file():
            destination: Path = output / name / fallback.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fallback, destination)
            notices.append(destination.relative_to(output).as_posix())

        if not notices:
            raise RuntimeError(
                f"No license files found for '{name}' '{installed.version}'. "
                "Add its upstream notice under 'res/licenses' before building."
            )

        metadata: dict[str, Any] = {
            "version": installed.version,
            "license_expression": installed.metadata.get("License-Expression"),
            "license": installed.metadata.get("License"),
            "project_urls": installed.metadata.get_all("Project-URL", []),
            "homepage": installed.metadata.get("Home-page"),
            "source": package.get("source"),
            "source_archive": package.get("sdist"),
            "notice_files": notices,
        }
        if name.startswith("pyside6") or name == "shiboken6":
            qt_version: str = installed.version
            qt_series: str = ".".join(qt_version.split(".")[:2])
            metadata["qt_source"] = (
                f"https://download.qt.io/archive/qt/{qt_series}/{qt_version}/"
                f"single/qt-everywhere-src-{qt_version}.tar.xz"
            )
            metadata["pyside_source"] = (
                f"https://code.qt.io/cgit/pyside/pyside-setup.git/?h=v{qt_version}"
            )
            metadata["qt_third_party_notices"] = (
                f"https://doc.qt.io/qt-{qt_series}/licenses-used-in-qt.html"
            )
            metadata["webengine_third_party_notices"] = (
                f"https://doc.qt.io/qt-{qt_series}/qtwebengine-licensing.html"
            )

        inventory[name] = metadata
        pending.extend(
            dependency["name"]
            for dependency in package.get("dependencies", [])
            if "marker" not in dependency or Marker(dependency["marker"]).evaluate()
        )

    python_license: Path = Path(sys.base_prefix) / "LICENSE.txt"
    if not python_license.is_file():
        raise FileNotFoundError(f"Python license not found at '{python_license}'.")
    shutil.copyfile(python_license, output / "Python-LICENSE.txt")
    (output / "dependencies.json").write_text(
        json.dumps(inventory, indent=4, sort_keys=True) + "\n", encoding="utf-8"
    )


def collect_source(project_root: Path, output: Path) -> None:
    """
    Archives application and submodule sources, including local license changes.

    Args:
        project_root (Path): Root of the build checkout.
        output (Path): Directory for the source archive and revision manifest.
    """

    output.mkdir(parents=True, exist_ok=True)
    tracked: list[str]
    revisions: dict[str, str]
    if (project_root / ".git").exists():
        tracked = (
            subprocess.check_output(
                ["git", "ls-files", "--recurse-submodules", "-z"], cwd=project_root
            )
            .decode("utf-8")
            .split("\0")
        )
        revisions = {}
        for directory in (
            project_root,
            *(project_root / p for p in ("core-lib", "core-res", "mod-manager-lib")),
        ):
            revisions[directory.relative_to(project_root).as_posix()] = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=directory, text=True
                ).strip()
            )
        revisions["working_tree_status"] = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=project_root, text=True
        )
    else:
        tracked = json.loads(
            (project_root / "SOURCE_FILES.json").read_text(encoding="utf-8")
        )
        revisions = json.loads(
            (project_root / "SOURCE_REVISIONS.json").read_text(encoding="utf-8")
        )

    archived: list[str] = []
    with ZipFile(output / "SSE-AT.zip", "w", compression=ZIP_DEFLATED) as archive:
        for relative in sorted(set(tracked)):
            if not relative:
                continue

            path = Path(relative)
            if (
                any(
                    part in (".git", ".venv", "__pycache__", "build", "dist")
                    for part in path.parts
                )
                or "/tests/data/" in f"/{path.as_posix()}/"
            ):
                continue
            if path.name == "resources_rc.py" or path.suffix == ".qm":
                continue

            source: Path = project_root / path
            if source.is_file() and source.resolve().is_relative_to(
                project_root.resolve()
            ):
                archive.write(source, arcname=path.as_posix())
                archived.append(path.as_posix())

        archive.writestr("SOURCE_FILES.json", json.dumps(archived, indent=4) + "\n")
        archive.writestr("SOURCE_REVISIONS.json", json.dumps(revisions, indent=4) + "\n")

    (output / "revisions.json").write_text(
        json.dumps(revisions, indent=4) + "\n", encoding="utf-8"
    )


def prepare_license_bundle(project_root: Path, dist_folder: Path) -> None:
    """
    Adds licensing materials before the builder copies and archives its output.

    Args:
        project_root (Path): Root of the build checkout.
        dist_folder (Path): Backend output directory containing the executable.
    """

    for name in ("LICENSE", "NOTICE.md"):
        shutil.copyfile(project_root / name, dist_folder / name)
    collect_dependencies(project_root, dist_folder / "licenses")
    collect_source(project_root, dist_folder / "source")
