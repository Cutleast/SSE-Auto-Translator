"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import ctypes
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import jstyleson as json
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

from .constants import *
from .detector import LangDetector, Language
from .download import Download
from .exceptions import *
from .importer import *
from .ini_parser import IniParser
from .localisation import Localisator
from .mod import Mod
from .nxm_listener import NXMListener
from .plugin import Plugin
from .plugin_loader import PluginLoader
from .stdout_pipe import StdoutPipe
from .string import String
from .thread import Thread
from .types import ProgressUpdate


LOG_LEVELS = {
    10: "debug",  # DEBUG
    20: "info",  # INFO
    30: "warning",  # WARNING
    40: "error",  # ERROR
    50: "critical",  # CRITICAL
}


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


def apply_shadow(widget: qtw.QWidget, color: str = "#181818") -> None:
    """
    Applies standardized shadow effect to <widget>.
    """

    shadoweffect = qtw.QGraphicsDropShadowEffect(widget)
    shadoweffect.setBlurRadius(4)
    shadoweffect.setOffset(4, 4)
    shadoweffect.setColor(color)
    widget.setGraphicsEffect(shadoweffect)


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


def revert_dark_title_bar(widget: qtw.QWidget):
    """
    Reverts dark title bar of <widget>.


    More information here:

    https://docs.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
    """

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    hwnd = widget.winId()
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = 0  # off
    value = ctypes.c_int(value)
    set_window_attribute(
        hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value)
    )


def fmt_time(timestamp: float | int, format: str = None) -> str:
    """
    Converts timestamp (seconds since epoch)
    to a formatted string.

    For example:
        1684054736.043326 -> "14.05.2023 10:58:56"
    """

    timestamp = time.localtime(timestamp)
    if format is None:
        return time.strftime("%d.%m.%Y %H:%M:%S", timestamp)
    else:
        return time.strftime(format, timestamp)


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


def create_nexus_mods_url(
    game_id: str, mod_id: int, file_id: int = None, mod_manager: bool = False
):
    """
    Creates URL to Nexus Mods page of `mod_id` in `game_id` nexus.

    `file_id` is optional and can be used to link directly to a file.
    """

    base_url = "https://www.nexusmods.com"

    if file_id is None:
        url = f"{base_url}/{game_id}/mods/{mod_id}"
    else:
        url = f"{base_url}/{game_id}/mods/{mod_id}?tab=files&file_id={file_id}"
        if mod_manager:
            url += "&nmm=1"

    return url


def get_file_list(folder: Path):
    """
    Creates a list with all files
    with relative paths to <folder> and returns it.
    """

    files: list[Path] = []

    for root, _, _files in os.walk(folder):
        root = Path(root).relative_to(folder)
        for f in _files:
            path = root / f
            files.append(path)

    return files


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


def flatten_nested_dict(nested_dict: dict) -> dict[str, str]:
    """
    This function takes a nested dictionary
    and converts it back to a flat dictionary in the format of
    {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}.

    Parameters:
            nested_dict: dict (nested dictionary)
    Returns:
            dict (dictionary in the format above.)
    """

    flat_dict: dict[str, str] = {}

    def flatten_dict_helper(dictionary, prefix=""):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                flatten_dict_helper(value, prefix + key + "###")
            else:
                flat_dict[prefix + key] = json.dumps(value, separators=(",", ":"))

    flatten_dict_helper(nested_dict)

    return flat_dict


def parse_flat_dict(data: dict[str, str]):
    """
    This function takes a dict in the
    format of
    {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}
    and converts it into a nested dictionary.

    Parameters:
        data: dict of format above

    Returns:
        result: dict (nested dictionary)
    """

    result: dict = {}

    for keys, value in data.items():
        try:
            keys = keys.strip().split("###")

            # Add keys and value to result
            current = result
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current: dict[str, dict] = current[key]
            value = json.loads(value)
            current[keys[-1]] = value
        except ValueError:
            print(f"Failed to process key: {keys:20}...")
            continue

    return result


def normalize_path(path: Path):
    """
    Workaround for long paths (> 255 chars). This adds `\\\\?\\` as prefix.
    """

    normalized = os.fspath(path.resolve())

    if not normalized.startswith("\\\\?\\"):
        normalized = "\\\\?\\" + normalized

    return Path(normalized)


def trim_string(text: str, max_length: int = 100):
    """
    Returns raw representation (for eg. "\\n" instead of a line break) of `text` trimmed to `max_length` characters.
    Appends "..." suffix if `text` was longer than `max_length`.
    """

    if len(text) > max_length:
        trimmed_text = text[:max_length-3] + "..."
        return f"{trimmed_text!r}"[1:-1]

    return f"{text!r}"[1:-1]


class ProxyStyle(qtw.QProxyStyle):
    """
    Proxy Style to replace icon of clear button in QLineEdit.
    """

    def standardIcon(self, standardIcon, option=None, widget=None):
        if standardIcon == qtw.QStyle.StandardPixmap.SP_LineEditClearButton:
            return qtg.QIcon("./data/icons/close.svg")
        return super().standardIcon(standardIcon, option, widget)
