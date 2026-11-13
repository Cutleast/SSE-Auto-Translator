"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.exceptions import LocalizedException
from PySide6.QtWidgets import QApplication


class LlmConnectionError(LocalizedException):
    """
    Class for general connection issues to LLM providers.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Failed to connect to the configured LLM provider. Please ensure, that the "
            "address and the API key are correct and try again.",
        )


class LlmReplyCutOffError(LocalizedException):
    """
    Occurs when a translation is cut off due to the model's token limit.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Translation was cut off due to the model's token limit. Please try again.",
        )
