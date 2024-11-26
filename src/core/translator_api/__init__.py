"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from .deepl import DeepLTranslator
from .google import GoogleTranslator
from .translator import Translator

AVAILABLE_APIS: list[type[Translator]] = [
    GoogleTranslator,
    DeepLTranslator,
]
