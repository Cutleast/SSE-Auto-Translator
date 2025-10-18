"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional


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

    if Path(file).suffix.lower() in [".esm", ".esp", ".esl"]:
        return Path(file).name

    file = file.replace("\\", "/")

    filters = ["/interface/", "/scripts/", "/textures/", "/sound/"]

    for filter in filters:
        index = file.lower().find(filter)
        if index != -1:
            return file[index + 1 :]

    return file


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
