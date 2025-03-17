"""
Copyright (c) Cutleast
"""

from .mod_file import ModFile
from .plugin_file import PluginFile

MODFILE_TYPES: list[type[ModFile]] = [
    PluginFile,
]


def get_modfiletype_for_suffix(suffix: str) -> type[ModFile]:
    """
    Returns a matching ModFile type for the specified file type suffix.

    Args:
        suffix (str): File type suffix

    Raises:
        NotImplementedError: when the file type is not supported

    Returns:
        type[ModFile]: ModFile type
    """

    for file_type in MODFILE_TYPES:
        if any(
            p.lower().endswith(suffix.lower()) for p in file_type.get_glob_patterns("")
        ):
            return file_type

    raise NotImplementedError(f"File type {suffix!r} not yet supported!")
