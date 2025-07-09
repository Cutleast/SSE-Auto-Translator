"""
This script builds the SSE-AT.exe and bundles all its dependencies in one folder.
"""

import os
import shutil
from pathlib import Path

import jstyleson as json

APPNAME: str = "SSE Auto Translator"
DISPLAY_VERSION: str = "3.0.0-alpha"
FILE_VERSION: str = "3.0.0.0"
AUTHOR: str = "Cutleast"
LICENSE: str = "Attribution-NonCommercial-NoDerivatives 4.0 International"
BUILD_FOLDER: Path = Path("main.dist")
DIST_FOLDER: Path = Path("dist")
SRC_FOLDER: Path = Path("src")
RES_FOLDER: Path = Path("res")
UNUSED_ITEMS: list[Path] = []
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("doc"): BUILD_FOLDER / "doc",
    Path("LICENSE"): BUILD_FOLDER / "LICENSE",
    Path(".venv")
    / "Lib"
    / "site-packages"
    / "cloudscraper"
    / "user_agent"
    / "browsers.json": BUILD_FOLDER / "cloudscraper" / "user_agent" / "browsers.json",
}
OUTPUT_FOLDER: Path = DIST_FOLDER / "SSE-AT"
OUTPUT_ARCHIVE: Path = DIST_FOLDER / f"SSE-AT v{DISPLAY_VERSION}.zip"

# Add external resources from res/ext_resources.json
with open("res/ext_resources.json", encoding="utf8") as f:
    for item in json.load(f):
        for i in RES_FOLDER.glob(item):
            ADDITIONAL_ITEMS[i] = BUILD_FOLDER / "res" / i.relative_to(RES_FOLDER)

if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print(f"Deleted already existing {OUTPUT_FOLDER.name!r} folder.")

DIST_FOLDER.mkdir(exist_ok=True)

print("Building with nuitka...")
cmd: str = f'.venv\\scripts\\nuitka \
--msvc="latest" \
--standalone \
--enable-plugin=pyside6 \
--remove-output \
--windows-console-mode=attach \
--company-name="{AUTHOR}" \
--product-name="{APPNAME}" \
--file-version="{FILE_VERSION}" \
--product-version="{FILE_VERSION}" \
--file-description="{APPNAME}" \
--copyright="{LICENSE}" \
--nofollow-import-to=tkinter \
--nofollow-import-to=mypy \
--windows-icon-from-ico="res/icons/icon.ico" \
--output-filename="SSE-AT.exe" \
"src/main.py"'
return_code: int = os.system(cmd)

if return_code != 0:
    print("Build command failed! Check the output above.")
    if BUILD_FOLDER.is_dir():
        shutil.rmtree(BUILD_FOLDER)
    exit(return_code)


def safe_copy(
    src: os.PathLike, dst: os.PathLike, *, follow_symlinks: bool = True
) -> os.PathLike | str:
    if os.path.exists(dst):
        return dst

    return shutil.copy(src, dst, follow_symlinks=follow_symlinks)


print(f"Copying {len(ADDITIONAL_ITEMS)} additional item(s)...")
for item, dest in ADDITIONAL_ITEMS.items():
    if item.is_dir():
        shutil.copytree(item, dest, dirs_exist_ok=True, copy_function=safe_copy)  # type: ignore[arg-type]
    elif item.is_file():
        if not dest.is_file():
            os.makedirs(dest.parent, exist_ok=True)
            os.link(item, dest)
    else:
        print(f"{str(item)!r} does not exist!")
        continue

    print(f"Copied {str(item)!r} to {str(dest)!r}.")

print(f"Deleting {len(UNUSED_ITEMS)} unused item(s)...")
for item in UNUSED_ITEMS:
    if item.is_dir():
        shutil.rmtree(item)
        print(f"Removed folder '{item.name}'.")
    elif item.is_file():
        os.remove(item)
        print(f"Removed file '{item.name}'.")

print("Moving build output to output folder...")
shutil.move(BUILD_FOLDER, OUTPUT_FOLDER)

print("Packing into archive...")
if OUTPUT_ARCHIVE.is_file():
    os.remove(OUTPUT_ARCHIVE)
    print("Deleted already existing archive.")

cmd = f'res\\7-zip\\7z.exe \
a \
"{OUTPUT_ARCHIVE}" \
"{OUTPUT_FOLDER}"'
os.system(cmd)

print("Done!")
