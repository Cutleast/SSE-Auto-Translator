"""
Copyright (c) Cutleast
"""

import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Optional

from virtual_glob import InMemoryPath
from virtual_glob import glob as vglob


def create_folder_list(folder: Path) -> list[Path]:
    """
    Creates a list of all files in all subdirectories of a folder.

    Args:
        folder (Path): Folder to get list of files of.

    Returns:
        list[Path]: List of relative file paths from folder and all subdirectories.
    """

    return [item.relative_to(folder) for item in folder.glob("**/*") if item.is_file()]


def extract_file_paths(data: dict) -> list[str]:
    """
    Extracts file paths from Nexus Mods file contents preview data.
    Returns them in a flat list of strings.

    Args:
        data (dict): File contents preview data.

    Returns:
        list[str]: List of file paths.
    """

    file_paths: list[str] = []

    for item in data["children"]:
        path = item["path"]
        item_type = item["type"]

        if item_type == "file":
            file_paths.append(path)
        elif item_type == "directory":
            file_paths.extend(extract_file_paths(item))

    return file_paths


def relative_data_path(file: str) -> str:
    """
    Returns relative path to data folder from file path.

    Example:
        `"000 Data/interface/translations/requiem_french.txt"`
        -> `"interface/translations/requiem_french.txt"`

    Args:
        file (str): Full file path.

    Returns:
        str: Relative path to data folder.
    """

    filters = ["/interface/", "/scripts/", "/textures/", "/sound/"]

    for filter in filters:
        index = file.lower().find(filter)
        if index != -1:
            return file[index + 1 :]

    return file


def get_file_identifier(file_path: os.PathLike, block_size: int = 1024 * 1024) -> str:
    """
    Creates a sha256 hash of the first and last block with `block_size`
    and returns first 8 characters of the hash.

    Args:
        file_path (os.PathLike): Path to file to hash.
        block_size (int, optional): Size of block to hash. Defaults to 1MB.

    Returns:
        str: First 8 characters of hash.
    """

    hasher = hashlib.sha256()
    file_size = os.path.getsize(file_path)

    with open(file_path, "rb") as f:
        if file_size <= block_size:
            # File is smaller than block_size, hash the entire file
            chunk = f.read()
            hasher.update(chunk)
        else:
            # Hash the first block
            chunk = f.read(block_size)
            if chunk:
                hasher.update(chunk)

            # Move to the end and hash the last block
            f.seek(-block_size, os.SEEK_END)
            chunk = f.read(block_size)
            if chunk:
                hasher.update(chunk)

    return hasher.hexdigest()[:8]


def get_folder_size(folder: Path) -> int:
    """
    Returns folder size in bytes.

    Args:
        folder (Path): Folder to get size of.

    Returns:
        int: Folder size in bytes.
    """

    total_size = 0

    for path in folder.rglob("*"):
        if path.is_file():
            total_size += path.stat().st_size

    return total_size


def clean_fs_name(folder_or_file_name: str) -> str:
    """
    Cleans a folder or file name of illegal characters like ":".

    Args:
        folder_or_file_name (str): File or folder name to clean.

    Returns:
        str: Cleaned file or folder name.
    """

    return re.sub(r'[:<>?*"|]', "", folder_or_file_name)


def parse_path(path: Path) -> tuple[Optional[Path], Optional[Path]]:
    """
    Parses path and returns tuple with two components:
    bsa path and file path

    Examples:
        ```python
            path = 'C:/Modding/RaceMenu/RaceMenu.bsa/interface/racesex_menu.swf'
            => (
                'C:/Modding/RaceMenu/RaceMenu.bsa',
                'interface/racesex_menu.swf'
            )
        ```

    Args:
        path (Path): Path to parse.

    Returns:
        tuple[Optional[Path], Optional[Path]]: Tuple with bsa path and file path.
    """

    bsa_path = file_path = None

    parts: list[str] = []

    for part in path.parts:
        parts.append(part)

        if part.endswith(".bsa"):
            bsa_path = Path("/".join(parts))
            parts.clear()
    if parts:
        file_path = Path("/".join(parts))

    return (bsa_path, file_path)


def safe_copy(
    src: os.PathLike, dst: os.PathLike, *, follow_symlinks: bool = True
) -> os.PathLike | str:
    """
    Safe version of `shutil.copy` which ignores existing files.

    Args:
        src (os.PathLike): Source file.
        dst (os.PathLike): Destination file.
        follow_symlinks (bool, optional): Follow symlinks. Defaults to True.

    Returns:
        os.PathLike | str: Copied file.
    """

    if os.path.exists(dst):
        return dst

    return shutil.copy(src, dst, follow_symlinks=follow_symlinks)


def norm(path: str) -> str:
    """
    Normalizes a path.

    Args:
        path (str): Path to normalize.

    Returns:
        str: Normalized path.
    """

    return path.replace("\\", "/")


def glob(pattern: str, files: list[str], case_sensitive: bool = False) -> list[str]:
    """
    Glob function for a list of files as strings.

    Args:
        pattern (str): Glob pattern.
        files (list[str]): List of files.
        case_sensitive (bool, optional): Case sensitive. Defaults to False.

    Returns:
        list[str]: List of matching files.
    """

    file_map: dict[str, str]
    """
    Map of original file names and normalized file names.
    """

    if case_sensitive:
        file_map = {norm(file): file for file in files}
        pattern = norm(pattern)
    else:
        file_map = {norm(file).lower(): file for file in files}
        pattern = norm(pattern).lower()

    fs: InMemoryPath = InMemoryPath.from_list(list(file_map.keys()))
    matches: list[str] = [
        file_map[p.path] for p in vglob(fs, pattern) if p.path in file_map
    ]

    return matches


def split_path_with_bsa(path: Path) -> tuple[Optional[Path], Optional[Path]]:
    """
    Splits a path containing a BSA file and returns bsa path and file path.

    For example:
    ```
    path = 'C:/Modding/RaceMenu/RaceMenu.bsa/interface/racesex_menu.swf'
    ```
    ==>
    ```
    (
        'C:/Modding/RaceMenu/RaceMenu.bsa',
        'interface/racesex_menu.swf'
    )
    ```

    Args:
        path (Path): Path to split.

    Returns:
        tuple[Optional[Path], Optional[Path]]:
            BSA path or None and relative file path or None
    """

    bsa_path: Optional[Path] = None
    file_path: Optional[Path] = None

    parts: list[str] = []

    for part in path.parts:
        parts.append(part)

        if part.endswith(".bsa"):
            bsa_path = Path("/".join(parts))
            parts.clear()

    if parts:
        file_path = Path("/".join(parts))

    return (bsa_path, file_path)


def open_in_explorer(path: Path) -> None:
    """
    Opens the specified path in the Windows Explorer.
    Opens the parent folder and selects the item if the specified path
    is a file otherwise it just opens the folder.

    Args:
        path (Path): The path to open.
    """

    if path.is_dir():
        os.startfile(path)
    else:
        os.system(f'explorer.exe /select,"{path}"')
