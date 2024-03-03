"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass


@dataclass
class Download:
    """
    Class for download entries in DownloadListDialog.
    """

    original_mod_name: str
    original_plugin_name: str

    available_translations: list[int]
    """
    List of mod ids of available translations.
    """

    available_translation_files: dict[int, list[int]]
    """
    List of fitting file ids for each available translation mod id.
    """
