"""
Copyright (c) Cutleast

Script to build the SSE-AT executable and pack all its dependencies in one folder.
"""

import logging
import os
import re
import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path
from typing import Any

from semantic_version import Version

project_file = Path("pyproject.toml")
project_data: dict[str, Any] = tomllib.loads(project_file.read_text(encoding="utf8"))[
    "project"
]
project_name: str = project_data["description"]
project_version: Version = Version(project_data["version"])
project_author: str = project_data["authors"][0]["name"]
project_license: str = (
    Path(project_data["license"]["file"])
    .read_text(encoding="utf8")
    .splitlines()[0]
    .strip()
)
file_version = str(project_version.truncate())
if project_version.prerelease:
    file_version += "." + project_version.prerelease[0].rsplit("-", 1)[1]

VERSION_PATTERN: re.Pattern[str] = re.compile(r'(?<=version = ")[^"]+(?=")')
DIST_OUTPUT_PATH = Path("dist/SSE-AT")
BUILD_PATH = Path("build")
UNUSED_ITEMS: list[Path] = [
    DIST_OUTPUT_PATH / "data" / "app" / "config.json",
    DIST_OUTPUT_PATH / "data" / "cache",
    DIST_OUTPUT_PATH / "data" / "user",
    DIST_OUTPUT_PATH / "data" / "user.old",
    DIST_OUTPUT_PATH / "data" / "logs",
    DIST_OUTPUT_PATH / "data" / "translator",
    DIST_OUTPUT_PATH / "data" / "icons" / "Confrerie.svg",
]
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("build") / "data": DIST_OUTPUT_PATH / "data",
    Path("doc"): DIST_OUTPUT_PATH / "doc",
    Path("LICENSE"): DIST_OUTPUT_PATH / "LICENSE",
    Path("build") / "TaskbarLib.tlb": DIST_OUTPUT_PATH / "TaskbarLib.tlb",
    Path(".venv")
    / "Lib"
    / "site-packages"
    / "cloudscraper"
    / "user_agent"
    / "browsers.json": DIST_OUTPUT_PATH
    / "cloudscraper"
    / "user_agent"
    / "browsers.json",
    Path("7-zip"): DIST_OUTPUT_PATH,
}

logging.basicConfig(level=logging.DEBUG)

logging.info(f"Project name: {project_name}")
logging.info(f"Project version: {project_version}")
logging.info(f"Project author: {project_author}")
logging.info(f"Project license: {project_license}")


def prepare_src() -> None:
    logging.info(f"Preparing source code for '{project_name}'...")

    logging.debug("Copying source code to build directory...")
    shutil.rmtree(BUILD_PATH, ignore_errors=True)
    shutil.copytree("src", BUILD_PATH)

    # Set version string in app file
    logging.debug("Setting version string in app file...")
    app_file: Path = BUILD_PATH / "main.py"
    app_file.write_text(
        VERSION_PATTERN.sub(str(project_version), app_file.read_text(encoding="utf8"))
    )


def generate_nuitka_cmd() -> list[str]:
    return [
        ".venv\\scripts\\nuitka",
        "--msvc=latest",
        "--standalone",
        "--include-package=hunspell",
        "--include-package=cacheman",
        "--enable-plugin=pyside6",
        "--remove-output",
        "--windows-console-mode=attach",
        f"--company-name={project_author}",
        f"--copyright={project_license}",
        f"--product-name={project_name}",
        f"--file-description={project_name}",
        f"--file-version={str(project_version).split('-')[0]}",
        f"--product-version={str(project_version).split('-')[0]}",
        "--nofollow-import-to=tkinter",
        "--windows-icon-from-ico=build/data/icons/icon.ico",
        "--output-filename=SSE-AT.exe",
        "build/app.py",
    ]


def build() -> None:
    logging.info("Building application with nuitka...")

    prepare_src()
    cmd: list[str] = generate_nuitka_cmd()

    logging.info(f"Running command: {' '.join(cmd)!r}")
    input("Press enter to continue...")
    subprocess.run(cmd, shell=True, check=True)

    if DIST_OUTPUT_PATH.is_dir():
        shutil.rmtree(DIST_OUTPUT_PATH)
        logging.info("Deleted old dist directory.")

    shutil.move("app.dist", DIST_OUTPUT_PATH)

    finalize_build()
    logging.info("Done.")


def zip_folder(folder_path: Path, output_path: Path) -> None:
    folder_name = folder_path.name

    # Create the zip file
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk the directory tree
        for root, _, files in os.walk(folder_path):
            for file in files:
                # Create the full filepath by joining root directory and the file
                full_path = os.path.join(root, file)
                # Create the archive name by removing the leading directory path
                arcname = os.path.join(
                    folder_name, os.path.relpath(full_path, folder_path)
                )
                # Write the file to the zip archive
                zipf.write(full_path, arcname)


def finalize_build() -> None:
    logging.info("Finalizing build...")

    logging.info(f"Copying {len(ADDITIONAL_ITEMS)} additional item(s)...")
    for item, dest in ADDITIONAL_ITEMS.items():
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True, copy_function=os.link)
        elif item.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.link(item, dest)
        else:
            logging.error(f"{str(item)!r} does not exist!")
            continue

        logging.info(
            f"Copied {str(item)!r} to {str(dest.relative_to(DIST_OUTPUT_PATH))!r}."
        )

    logging.info(f"Deleting {len(UNUSED_ITEMS)} unused item(s)...")
    for item in UNUSED_ITEMS:
        if item.is_dir():
            shutil.rmtree(item)
            logging.info(f"Removed folder '{item.name}'.")
        elif item.is_file():
            os.remove(item)
            logging.info(f"Removed file '{item.name}'.")

    logging.info("Packing into zip archive...")
    output_archive: Path = Path("dist") / f"{project_name} v{project_version}.zip"
    if output_archive.is_file():
        os.unlink(output_archive)
        logging.info("Deleted already existing zip archive.")

    zip_folder(DIST_OUTPUT_PATH, output_archive)

    logging.info(f"Packed into '{output_archive}'.")


if __name__ == "__main__":
    try:
        build()
    except Exception as ex:
        logging.error(f"Failed to build application with nuitka: {ex}", exc_info=ex)

        shutil.rmtree(DIST_OUTPUT_PATH, ignore_errors=True)

    else:
        shutil.rmtree(BUILD_PATH, ignore_errors=True)
        logging.debug("Deleted build directory.")
