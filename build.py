"""
This script builds the SSE-AT.exe and packs
all its dependencies in one folder.
"""

import os
import shutil
from pathlib import Path

from src.app import MainApp

COMPILER = "cx_freeze"  # "pyinstaller" or "nuitka" or "cx_freeze"

DIST_FOLDER = Path("app.dist").resolve()
APPNAME = "SSE Auto Translator"
VERSION = MainApp.version.split("-")[0]
AUTHOR = "Cutleast"
LICENSE = "Attribution-NonCommercial-NoDerivatives 4.0 International"
CONSOLE_MODE = "attach"  # "attach": Attaches to console it was started with (if any), "force": starts own console window, "disable": disables console completely
UNUSED_ITEMS: list[Path] = [
    DIST_FOLDER / "data" / "app" / "config.json",
    DIST_FOLDER / "data" / "cache",
    DIST_FOLDER / "data" / "user",
    DIST_FOLDER / "data" / "user.old",
    DIST_FOLDER / "data" / "logs",
    DIST_FOLDER / "data" / "translator",
    DIST_FOLDER / "data" / "icons" / "Confrerie.svg",
]
ADDITIONAL_ITEMS: dict[Path, Path] = {
    Path("src") / "data": DIST_FOLDER / "data",
    Path("doc"): DIST_FOLDER / "doc",
    Path("LICENSE"): DIST_FOLDER / "LICENSE",
    Path("src") / "TaskbarLib.tlb": DIST_FOLDER / "TaskbarLib.tlb",
    Path(".venv")
    / "Lib"
    / "site-packages"
    / "cloudscraper"
    / "user_agent"
    / "browsers.json": DIST_FOLDER
    / "cloudscraper"
    / "user_agent"
    / "browsers.json",
    Path("7-zip"): DIST_FOLDER,
}
OUTPUT_FOLDER = DIST_FOLDER.with_name("SSE-AT")
OUTPUT_ARCHIVE = Path(f"SSE-AT v{MainApp.version}.zip").resolve()


if OUTPUT_FOLDER.is_dir():
    shutil.rmtree(OUTPUT_FOLDER)
    print(f"Deleted already existing {OUTPUT_FOLDER.name!r} folder.")


print(f"Building with {COMPILER}...")
if COMPILER == "nuitka":
    cmd = f'nuitka \
--msvc="latest" \
--standalone \
--include-package=hunspell \
--include-package=cacheman \
--enable-plugin=pyside6 \
--remove-output \
--windows-console-mode={CONSOLE_MODE} \
--company-name="{AUTHOR}" \
--product-name="{APPNAME}" \
--file-version="{VERSION}" \
--product-version="{VERSION}" \
--file-description="{APPNAME}" \
--copyright="{LICENSE}" \
--nofollow-import-to=tkinter \
--windows-icon-from-ico="src/data/icons/icon.ico" \
--output-filename="SSE-AT.exe" \
"src/app.py"'

elif COMPILER == "pyinstaller":
    # Create version file
    import pyinstaller_versionfile

    pyinstaller_versionfile.create_versionfile(
        output_file="versioninfo.txt",
        version=VERSION,
        company_name=AUTHOR,
        file_description=APPNAME,
        internal_name=APPNAME,
        legal_copyright=LICENSE,
        original_filename="SSE-AT.exe",
        product_name=APPNAME,
    )

    print("Created version info at: versioninfo.txt")

    cmd = f'pyinstaller \
--noconfirm \
--hide-console=hide-late \
--version-file="versioninfo.txt" \
--hidden-import=cacheman \
--hidden-import=cacheman.cachewrap \
--distpath="{OUTPUT_FOLDER.parent}" \
-i="./src/data/icons/icon.ico" \
--name="SSE-AT" \
"./src/app.py"'

elif COMPILER == "cx_freeze":
    import sys

    from cx_Freeze import Executable, setup

    build_options = {
        "replace_paths": [("*", "")],
        "packages": ["cacheman"],
        "excludes": [],
        "includes": ["cacheman.cachewrap"],
        "include_files": [("./.venv/Lib/site-packages/plyvel_ci.libs", "./lib/plyvel")],
        "include_path": "./src",
        "build_exe": DIST_FOLDER.name,
    }

    base = "gui"

    executables = [
        Executable(
            "./src/app.py",
            base=base,
            target_name="SSE-AT.exe",
            icon="./src/data/icons/icon.ico",
            copyright=LICENSE,
        )
    ]

    sys.argv.append("build_exe")

    setup(
        name=APPNAME,
        version=VERSION,
        description=APPNAME,
        author=AUTHOR,
        license=LICENSE,
        options={"build_exe": build_options},
        executables=executables,
    )

else:
    raise ValueError(f"Compiler {COMPILER!r} is not supported!")

if COMPILER != "cx_freeze":
    return_code = os.system(cmd)

    if return_code != 0 and COMPILER == "nuitka":
        print("Build command failed!")
        shutil.rmtree(DIST_FOLDER)
        exit()

print(f"Copying {len(ADDITIONAL_ITEMS)} additional item(s)...")
for item, dest in ADDITIONAL_ITEMS.items():
    if item.is_dir():
        shutil.copytree(item, dest, dirs_exist_ok=True, copy_function=os.link)
    elif item.is_file():
        os.makedirs(dest.parent, exist_ok=True)
        os.link(item, dest)
    else:
        print(f"{str(item)!r} does not exist!")
        continue

    print(f"Copied {str(item)!r} to {str(dest.relative_to(DIST_FOLDER))!r}.")

print(f"Deleting {len(UNUSED_ITEMS)} unused item(s)...")
for item in UNUSED_ITEMS:
    if item.is_dir():
        shutil.rmtree(item)
        print(f"Removed folder '{item.name}'.")
    elif item.is_file():
        os.remove(item)
        print(f"Removed file '{item.name}'.")

print("Creating Output folder...")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print("Hardlinking files into Output folder...")
shutil.copytree(DIST_FOLDER, OUTPUT_FOLDER, dirs_exist_ok=True, copy_function=os.link)

print("Packing into archive...")
if OUTPUT_ARCHIVE.is_file():
    os.remove(OUTPUT_ARCHIVE)
    print("Deleted already existing archive.")

cmd = f'7-zip\\7z.exe \
a \
"{OUTPUT_ARCHIVE}" \
"{OUTPUT_FOLDER}"'
os.system(cmd)

print("Cleaning dist folder...")
shutil.rmtree(DIST_FOLDER)

print("Done!")
