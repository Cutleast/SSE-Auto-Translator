"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtWidgets import QApplication

from .base_string import BaseString


class PluginString(BaseString):
    """
    Class for translation strings from plugin files (.esp, .esm and .esl).
    """

    form_id: str
    """
    FormIDs are hexadecimal numbers that identify the record of the string.
    """

    type: str
    """
    Scheme: Record Subrecord, for eg. WEAP FULL
    """

    index: Optional[int] = None
    """
    String index in current record (only for INFO and QUST).
    """

    editor_id: Optional[str] = None
    """
    EditorIDs are the IDs that are visible in CK, xTranslator and xEdit
    but not all strings do have one.
    """

    @property
    @override
    def id(self) -> str:
        """
        Generates a unique ID for the string. Intended only for internal use.

        Included attributes:
        - lowered `form_id` without master index (first two digits)
        - `editor_id`
        - `type`
        - `index`
        """

        return f"{self.form_id[2:].lower()}###{self.editor_id}###{self.type}###{self.index}"

    @property
    @override
    def display_id(self) -> str:
        fields: list[str] = []
        fields.append(self.form_id)

        if self.editor_id is not None:
            fields.append(self.editor_id)

        fields.append(self.type)

        if self.index is not None:
            fields.append(str(self.index))

        return " - ".join(fields)

    @override
    def get_localized_info(self) -> str:
        info: str = ""
        info += QApplication.translate("PluginString", "Form ID") + ": "
        info += self.form_id + "\n"

        if self.editor_id is not None:
            info += QApplication.translate("PluginString", "Editor ID") + ": "
            info += self.editor_id + "\n"

        info += QApplication.translate("PluginString", "Type") + ": " + self.type + "\n"
        if self.index is not None:
            info += QApplication.translate("PluginString", "Index") + ": "
            info += str(self.index)

        return info.strip("\n")

    # this method is redefined here so that Pyright sees the class as hashable
    # see this issue for more info: https://github.com/microsoft/pyright/issues/7344
    @override
    def __hash__(self) -> int:
        return hash((self.id, self.original, self.string, self.status))
