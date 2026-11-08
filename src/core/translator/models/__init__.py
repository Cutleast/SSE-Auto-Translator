"""
Copyright (c) Cutleast
"""

from .request import TranslationRequest
from .result import TranslationResult

__all__ = [
    "TranslationRequest",
    "TranslationResult",
]

TranslationRequest.model_rebuild()
TranslationResult.model_rebuild()
