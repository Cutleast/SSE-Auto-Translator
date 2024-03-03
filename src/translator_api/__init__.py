"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from .translator import Translator
from .google import GoogleTranslator
from .deepl import DeepLTranslator


AVAILABLE_APIS: list[type[Translator]] = [
    GoogleTranslator,
    DeepLTranslator,
]
