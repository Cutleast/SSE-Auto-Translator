"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import html
import logging
from abc import abstractmethod
from collections.abc import Mapping
from concurrent.futures import Future, as_completed
from pathlib import Path
from typing import Optional, cast, final

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)
from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor
from cutleast_core_lib.core.utilities.exceptions import TaskCancelledError
from cutleast_core_lib.core.utilities.hash import sha256_hash
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.core.utilities.truncate import truncate_string
from cutleast_core_lib.core.utilities.typing_utils import AbstractBase
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject

from core.config.translator_config import TranslatorConfig

from .models import TranslationRequest, TranslationResult


class Translator(QObject, AbstractBase):
    """
    Base class for translator APIs that generate automated machine translations.

    **Note to implementers**: The instances should be stateless.
    """

    CACHE_FOLDER = Path("translator_cache")
    """The subfolder within the cache folder to store cached API translations."""

    CACHE_MAX_AGE: int = 60 * 60 * 72  # 72 hours
    """Maximum age of cached translations in seconds."""

    _config: TranslatorConfig
    """The app-wide translator configuration."""

    log: logging.Logger

    def __init__(self, config: TranslatorConfig) -> None:
        """
        Args:
            config (TranslatorConfig): The app-wide translator configuration.
        """

        super().__init__()

        self._config = config

        self.log = logging.getLogger(self.__class__.__name__)

    @final
    @Cache.persistent_cache(
        cache_subfolder=CACHE_FOLDER,
        id_generator=lambda self, request, update_callback: cast(
            Translator, self
        )._get_cache_id(request),
        max_age=CACHE_MAX_AGE,
    )
    def translate(
        self,
        request: TranslationRequest,
        update_callback: Optional[UpdateCallback] = None,
    ) -> TranslationResult:
        """
        Translates a single text from a source language to a destination language.

        Args:
            request (TranslationRequest): The translation request.
            update_callback (Optional[UpdateCallback], optional):
                Optional progress callback. Defaults to None.

        Returns:
            TranslationResult: The translation result.
        """

        progress_req_text: str = html.escape(
            truncate_string(request.text, 50), quote=False
        )
        update(
            update_callback,
            ProgressUpdate(
                status_text=self.tr("Translating '{0}'...").format(progress_req_text),
                value=0,
                maximum=0,
            ),
        )

        translated_text: str = self._process_request(request)

        result = TranslationResult(request=request, translated_text=translated_text)

        return result

    @abstractmethod
    def _process_request(self, request: TranslationRequest) -> str:
        """
        Processes a translation request by translating its text to the destination
        language while including additional context and instructions, if supported by
        this translator.

        Args:
            request (TranslationRequest): The translation request.

        Returns:
            str: The translated text.
        """

    def batch_translate(
        self,
        requests: list[TranslationRequest],
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> Mapping[TranslationRequest, TranslationResult]:
        """
        Translates multiple texts from a source language to a destination language.

        Args:
            requests (list[TranslationRequest]): The list of translation requests.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            Mapping[TranslationRequest, TranslationResult]: The translation results.
        """

        results: Mapping[TranslationRequest, TranslationResult] = ReferenceDict()
        with ProgressExecutor(
            pdisplay,
            max_workers=(
                self._config.max_parallel_requests
                if self.supports_parallel_requests()
                else 1
            ),
        ) as executor:
            executor.set_main_progress_text(self.tr("Translating with API..."))

            futures: dict[Future[TranslationResult], TranslationRequest] = {
                executor.submit(lambda uc, req=request: self.translate(req, uc)): request
                for request in requests
            }

            for future in as_completed(futures):
                request: TranslationRequest = futures[future]
                try:
                    results[request] = future.result()
                except TaskCancelledError:
                    raise
                except Exception as ex:
                    self.log.error(
                        f"Failed to process translation request '{request}': {ex}",
                        exc_info=ex,
                    )

        return results

    def _get_cache_id(self, request: TranslationRequest) -> str:
        """
        Generates an ID for a cache file for a single translation request.

        Args:
            request (TranslationRequest): The translation request.

        Returns:
            str: The cache ID.
        """

        data: str = f"{self.__class__.__name__}-{request.model_dump_json()}"
        data += self._config.model_dump_json()

        return sha256_hash(data.encode())

    @classmethod
    def supports_parallel_requests(cls) -> bool:
        """
        Returns:
            bool: If this translator supports parallel requests.
        """

        return False

    @classmethod
    def supports_corrections(cls) -> bool:
        """
        Returns:
            bool:
                If this translator supports correction requests for previous
                translations.
        """

        return False

    @classmethod
    def supports_instructions(cls) -> bool:
        """
        Returns:
            bool:
                If this translator supports additional translation instructions per
                string.
        """

        return False
