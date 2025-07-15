"""
Copyright (c) Cutleast

This script builds the SSE-AT.exe and bundles all its dependencies in one folder.
"""

import logging
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import jstyleson as json
from semantic_version import Version

project_file = Path("pyproject.toml")
project_data: dict[str, Any] = tomllib.loads(project_file.read_text(encoding="utf8"))[
    "project"
]
project_name: str = project_data["description"]
project_version = Version(project_data["version"])
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

EXE_NAME: str = "SSE-AT.exe"
RES_FOLDER: Path = Path("res")
ICON_PATH: Path = RES_FOLDER / "icons" / "icon.ico"
CONSOLE_MODE: str = "force"  # "attach": Attaches to console it was started with (if any), "force": starts own console window, "disable": disables console completely
VERSION_PATTERN: re.Pattern[str] = re.compile(r'(?<=APP_VERSION: str = ")[^"]+(?=")')
BUILD_PATH = Path("build")
NUITKA_OUTPUT_PATH = Path("main.dist")
DIST_FOLDER: Path = Path("dist") / Path(EXE_NAME).stem
OUTPUT_ARCHIVE_PATH: Path = Path("dist") / f"{project_name} v{project_version}.zip"
UNUSED_ITEMS: list[Path] = [DIST_FOLDER / "lib" / "qtpy" / "tests"]
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("doc"): DIST_FOLDER / "doc",
    Path("LICENSE"): DIST_FOLDER / "LICENSE",
    Path(".venv")
    / "Lib"
    / "site-packages"
    / "cloudscraper"
    / "user_agent"
    / "browsers.json": DIST_FOLDER / "cloudscraper" / "user_agent" / "browsers.json",
}

# Add external resources from res/ext_resources.json
with open("res/ext_resources.json", encoding="utf8") as f:
    for item in json.load(f):
        for i in RES_FOLDER.glob(item):
            ADDITIONAL_ITEMS[i] = DIST_FOLDER / "res" / i.relative_to(RES_FOLDER)

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
    app_file: Path = BUILD_PATH / "app.py"
    app_file.write_text(
        VERSION_PATTERN.sub(str(project_version), app_file.read_text(encoding="utf8"))
    )


def generate_nuitka_cmd() -> list[str]:
    return [
        ".venv\\scripts\\nuitka",
        "--msvc=latest",
        "--standalone",
        "--enable-plugin=pyside6",
        "--remove-output",
        f"--windows-console-mode={CONSOLE_MODE}",
        f"--company-name={project_author}",
        f"--copyright={project_license}",
        f"--product-name={project_name}",
        f"--file-description={project_name}",
        f"--file-version={str(project_version).split('-')[0]}",
        f"--product-version={str(project_version).split('-')[0]}",
        "--nofollow-import-to=tkinter",
        f"--windows-icon-from-ico={ICON_PATH}",
        f"--output-filename={EXE_NAME}",
        "build/main.py",
    ]


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
            logging.error(f"'{str(item)}' does not exist!")
            continue

        logging.info(f"Copied '{str(item)}' to '{str(dest.relative_to(DIST_FOLDER))}'.")

    logging.info(f"Deleting {len(UNUSED_ITEMS)} unused item(s)...")
    for item in UNUSED_ITEMS:
        if item.is_dir():
            shutil.rmtree(item)
            logging.info(f"Removed folder '{item.name}'.")
        elif item.is_file():
            os.remove(item)
            logging.info(f"Removed file '{item.name}'.")

    logging.info("Packing into 7-zip archive...")
    if OUTPUT_ARCHIVE_PATH.is_file():
        os.unlink(OUTPUT_ARCHIVE_PATH)
        logging.info("Deleted already existing 7-zip archive.")

    cmd: list[str] = [
        "..\\res\\7-zip\\7z.exe",
        "a",
        str(OUTPUT_ARCHIVE_PATH.relative_to(DIST_FOLDER.parent)),
        str(DIST_FOLDER.relative_to(DIST_FOLDER.parent)),
    ]
    cwd: str = os.getcwd()
    os.chdir(DIST_FOLDER.parent)
    subprocess.run(cmd, shell=True, check=True)
    os.chdir(cwd)

    logging.info(f"Packed into '{OUTPUT_ARCHIVE_PATH}'.")


def build() -> None:
    logging.info("Building application with nuitka...")

    prepare_src()
    cmd: list[str] = generate_nuitka_cmd()

    logging.info(f"Running command: '{' '.join(cmd)}'")
    subprocess.run(cmd, shell=True, check=True)

    if DIST_FOLDER.is_dir():
        shutil.rmtree(DIST_FOLDER)
        logging.info("Deleted old dist directory.")

    shutil.copytree(NUITKA_OUTPUT_PATH, DIST_FOLDER, copy_function=os.link)

    try:
        shutil.rmtree(NUITKA_OUTPUT_PATH)
    except Exception as ex:
        logging.error(f"Failed to delete 'main.dist': {ex}", exc_info=ex)

    finalize_build()
    logging.info("Done.")


if __name__ == "__main__":
    try:
        build()
    except Exception as ex:
        logging.error(f"Failed to build application: {ex}", exc_info=ex)

        shutil.rmtree(DIST_FOLDER, ignore_errors=True)

    else:
        shutil.rmtree(BUILD_PATH, ignore_errors=True)
        logging.debug("Deleted build directory.")
