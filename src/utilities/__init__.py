"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import ctypes
import hashlib
import logging
from datetime import datetime

import jstyleson as json
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw
import requests as req

from .constants import *
from .detector import LangDetector, Language
from .exceptions import *
from .importer import *
from .ini_parser import IniParser
from .leveldb import LevelDB
from .licenses import LICENSES
from .localisation import Localisator
from .mod import Mod
from .nxm_listener import NXMListener
from .plugin import Plugin
from .source import Source
from .stdout_pipe import StdoutPipe
from .string import String
from .thread import Thread

LOG_LEVELS = {
    10: "debug",  # DEBUG
    20: "info",  # INFO
    30: "warning",  # WARNING
    40: "error",  # ERROR
    50: "critical",  # CRITICAL
}


logging.getLogger("Utilities")


def strlevel2intlevel(level: str) -> int:
    """
    Converts logging level from string to integer.
    Returns 20 (info level) if string is invalid.

    Example: "debug" -> 10
    """

    intlevel: int = getattr(logging, level.upper(), 20)

    return intlevel


def intlevel2strlevel(level: int) -> str:
    """
    Converts logging level from integer to string.
    Returns "info" if integer is invalid.

    Example: 10 -> "debug"
    """

    if level == logging.DEBUG:
        return "debug"
    elif level == logging.INFO:
        return "info"
    elif level == logging.CRITICAL:
        return "critical"
    elif level == logging.ERROR:
        return "error"
    elif level == logging.FATAL:
        return "fatal"
    else:
        return "info"


def center(widget: qtw.QWidget, referent: qtw.QWidget = None) -> None:
    """
    Moves <widget> to center of its parent or if given to
    center of <referent>.

    Parameters:
        widget: QWidget (widget to move)
        referent: QWidget (widget reference for center coords;
        uses widget.parent() if None)
    """

    size = widget.size()
    w = size.width()
    h = size.height()

    if referent is None:
        rsize = qtw.QApplication.primaryScreen().size()
    else:
        rsize = referent.size()
    rw = rsize.width()
    rh = rsize.height()

    x = int((rw / 2) - (w / 2))
    y = int((rh / 2) - (h / 2))

    widget.move(x, y)


def get_diff(start_time: str, end_time: str, str_format: str = "%H:%M:%S"):
    """
    Returns difference between <start_time> and <end_time> in <str_format>.
    """

    tdelta = str(
        datetime.strptime(end_time, str_format)
        - datetime.strptime(start_time, str_format)
    )
    return tdelta


def apply_dark_title_bar(widget: qtw.QWidget):
    """
    Applies dark title bar to <widget>.


    More information here:

    https://docs.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
    """

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    hwnd = widget.winId()
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = 2  # on
    value = ctypes.c_int(value)
    set_window_attribute(
        hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value)
    )


def is_valid_hex_color(color_code: str):
    """
    Checks if color code is valid
    and returns True or False.
    """

    color_code = color_code.removeprefix("#")

    if (len(color_code) == 6) or (len(color_code) == 8):
        try:
            int(color_code, 16)
            return True

        except ValueError:
            return False
    else:
        return False


def scale_value(value: int | float, suffix="B", factor: int = 1024):
    """
    Scales `value` to its proper format
    with `suffix` as unit and `factor` as scaling
    and returns it as string; for e.g:

        1253656 => '1.20 MB'

        1253656678 => '1.17 GB'
    """

    if value is None:
        return f"0 {suffix}"

    for unit in ["", "K", "M", "G", "T", "P", "H"]:
        if value < factor:
            if f"{value:.2f}".split(".")[1] == "00":
                return f"{int(value)} {unit}{suffix}"

            return f"{value:.2f} {unit}{suffix}"

        value /= factor

    return str(value)


def extract_file_paths(data: dict):
    """
    Extracts file paths from Nexus Mods file contents preview data.
    Returns them in a flat list of strings.
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


def trim_string(text: str, max_length: int = 100):
    """
    Returns raw representation (for eg. "\\n" instead of a line break) of `text` trimmed to `max_length` characters.
    Appends "..." suffix if `text` was longer than `max_length`.
    """

    if not isinstance(text, str):
        return str(text)

    if len(text) > max_length:
        trimmed_text = text[: max_length - 3] + "..."
        return f"{trimmed_text!r}"[1:-1]

    return f"{text!r}"[1:-1]


def relative_data_path(file: str):
    """
    Example:
        `"000 Data/interface/translations/requiem_french.txt"`
        -> `"interface/translations/requiem_french.txt"`
    """

    filters = ["/interface/", "/scripts/", "/textures/", "/sound/"]

    for filter in filters:
        index = file.find(filter)
        if index != -1:
            return file[index + 1 :]

    return file


def get_file_identifier(file_path: os.PathLike, block_size: int = 1024 * 1024):
    """
    Creates a sha256 hash of the first and last block with `block_size`
    and returns first 8 characters of the hash.
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


def get_folder_size(folder: Path):
    """
    Returns folder size in bytes.
    """

    total_size = 0

    for path in folder.rglob("*"):
        if path.is_file():
            total_size += path.stat().st_size

    return total_size


masterlist: dict[str, dict] = None


def get_masterlist(language: str, cache: bool = True) -> dict[str, dict]:
    """
    Gets Masterlist from GitHub Repository.

    Caches response if `cache` is True.
    """

    global masterlist

    language = language.lower()

    REPO_NAME = "SSE-Auto-Translator"
    REPO_OWNER = "Cutleast"
    BRANCH = "master"
    INDEX_PATH = f"masterlists/index.json"

    if masterlist is None or cache == False:
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{INDEX_PATH}"

        res = req.get(url, timeout=3)

        if res.status_code == 200:
            data = res.content.decode()
            index: dict[str, str] = json.loads(data)

            url = index.get(language)

            if not url:
                log.error(f"No masterlist for {language} available!")
                masterlist = {}

                return masterlist

            res = req.get(url, timeout=3)

            if res.status_code == 200:
                data = res.content.decode()
                masterlist = json.loads(data)
            else:
                log.debug(f"Request URL: {url!r}")
                raise Exception(f"Request failed! Status Code: {res.status_code}")

        else:
            log.debug(f"Request URL: {url!r}")
            raise Exception(f"Request failed! Status Code: {res.status_code}")

    return masterlist
