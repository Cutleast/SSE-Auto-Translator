"""
This script builds the SSE-AT.exe and packs
all its dependencies in one folder.
"""

import shutil
import os
from pathlib import Path

DIST_FOLDER = Path("app.dist").resolve()
APPNAME = "SSE Auto Translator"
VERSION = "1.1.0"
AUTHOR = "Cutleast"
LICENSE = "Attribution-NonCommercial-NoDerivatives 4.0 International"
UNUSED_ITEMS: list[Path] = [
    DIST_FOLDER / "data" / "app" / "config.json",
    DIST_FOLDER / "data" / "user",
    DIST_FOLDER / "data" / "user.old",
    DIST_FOLDER / "data" / "logs",
    DIST_FOLDER / "data" / "translator",
    DIST_FOLDER / "data" / "icons" / "Confrerie.svg",
]
OUTPUT_FOLDER = DIST_FOLDER.with_name("SSE-AT")
OUTPUT_ARCHIVE = Path(f"SSE-AT v{VERSION}.7z").resolve()

print("Building with nuitka...")
cmd = f'nuitka \
--msvc="latest" \
--standalone \
--include-data-dir="./7-zip=." \
--include-data-dir="./src/data=./data" \
--include-data-dir="./doc=./doc" \
--include-data-file="LICENSE=." \
--include-data-files="./.venv/Lib/site-packages/cloudscraper/user_agent/browsers.json=cloudscraper/user_agent/" \
--include-data-dir="./.venv/Lib/site-packages/qtawesome=./qtawesome" \
--enable-plugin=pyside6 \
--remove-output \
--disable-console \
--company-name="{AUTHOR}" \
--product-name="{APPNAME}" \
--file-version="{VERSION}" \
--product-version="{VERSION}" \
--file-description="{APPNAME}" \
--copyright="{LICENSE}" \
--nofollow-import-to=tkinter \
--windows-icon-from-ico="./src/data/icons/icon.ico" \
--output-filename="SSE-AT.exe" \
"./src/app.py"'
os.system(cmd)

print("Deleting unused files and folders...")
for item in UNUSED_ITEMS:
    if item.is_dir():
        shutil.rmtree(item)
        print(f"Removed folder '{item.name}'.")
    elif item.is_file():
        os.remove(item)
        print(f"Removed file '{item.name}'.")

shutil.copyfile("./7-zip/7z.dll", DIST_FOLDER / "7z.dll")
print("Copied 7z.dll to build folder.")

print("Renaming Output folder...")
if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print(f"Deleted already existing {OUTPUT_FOLDER.name!r} folder.")
os.rename(DIST_FOLDER, OUTPUT_FOLDER)

print("Done!")
