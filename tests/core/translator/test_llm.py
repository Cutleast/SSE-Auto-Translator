"""
Copyright (c) Cutleast
"""

from typing import Optional
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from core.config.translator_config import TranslatorConfig
from core.mod_file.context import ModFileContext
from core.translation_context.context import TranslationContext
from core.translator.llm import LlmTranslator
from core.translator.models.excerpt import TranslationExcerpt
from core.translator.models.request import TranslationRequest
from core.utilities.game_language import GameLanguage


class TestLlmTranslator:
    """
    Tests `core.translator.llm.LlmTranslator`.
    """

    @pytest.fixture
    def client(self, mocker: MockerFixture) -> MagicMock:
        """
        Replaces the OpenAI client used by the translator with a mock.

        Args:
            mocker (MockerFixture): The pytest-mock fixture.

        Returns:
            MagicMock: The mocked client instance.
        """

        client_class: MagicMock = mocker.patch("core.translator.llm.OpenAIClient")
        client: MagicMock = client_class.return_value
        TestLlmTranslator.set_reply(client, "Übersetzung")

        return client

    @pytest.fixture
    def translator(self, client: MagicMock) -> LlmTranslator:
        """
        Creates an LLM translator using the mocked client.

        Args:
            client (MagicMock): The mocked client instance.

        Returns:
            LlmTranslator: The translator.
        """

        return LlmTranslator(
            TranslatorConfig(llm_base_url="http://localhost/v1", llm_model="model")
        )

    @staticmethod
    def set_reply(client: MagicMock, reply: str) -> None:
        """
        Sets the reply of the mocked model.

        Args:
            client (MagicMock): The mocked client instance.
            reply (str): The reply of the model.
        """

        choice = MagicMock()
        choice.finish_reason = "stop"
        choice.message.content = reply
        client.chat.completions.create.return_value.choices = [choice]

    @staticmethod
    def get_user_prompt(client: MagicMock) -> str:
        """
        Gets the user prompt of the last request sent to the mocked client.

        Args:
            client (MagicMock): The mocked client instance.

        Returns:
            str: The user prompt.
        """

        messages: list[dict[str, str]] = client.chat.completions.create.call_args.kwargs[
            "messages"
        ]

        return messages[1]["content"]

    @staticmethod
    def create_request(
        text: str, excerpt: Optional[TranslationExcerpt] = None
    ) -> TranslationRequest:
        """
        Creates a translation request without additional context.

        Args:
            text (str): The text to translate.
            excerpt (Optional[TranslationExcerpt], optional):
                The excerpt to translate. Defaults to None.

        Returns:
            TranslationRequest: The translation request.
        """

        return TranslationRequest(
            text=text,
            dst=GameLanguage.German,
            context=TranslationContext(
                similar_strings=[], mod_file_context=ModFileContext()
            ),
            instructions="Use a formal tone.",
            excerpt=excerpt,
        )

    def test_prompt_without_excerpt(
        self, translator: LlmTranslator, client: MagicMock
    ) -> None:
        """
        Tests that the prompt for a complete text contains only the non-empty sections.
        """

        # given
        request: TranslationRequest = TestLlmTranslator.create_request("Iron Sword")

        # when
        result: str = translator._process_request(request)  # pyright: ignore[reportPrivateUsage]

        # then
        assert result == "Übersetzung"
        assert TestLlmTranslator.get_user_prompt(client) == (
            f"{LlmTranslator.INSTRUCTIONS_HEADING}\nUse a formal tone.\n\n"
            f"{LlmTranslator.TEXT_HEADING}\nIron Sword"
        )

    def test_prompt_with_excerpt(
        self, translator: LlmTranslator, client: MagicMock
    ) -> None:
        """
        Tests that the prompt for an excerpt contains the original text and the
        current translation with the marked excerpt.
        """

        # given
        excerpt = TranslationExcerpt(
            text="Iron",
            prefix="Ein ",
            suffix="schwert",
            original_text="An Iron Sword",
        )
        request: TranslationRequest = TestLlmTranslator.create_request(
            excerpt.text, excerpt
        )

        # when
        translator._process_request(request)  # pyright: ignore[reportPrivateUsage]

        # then
        user_prompt: str = TestLlmTranslator.get_user_prompt(client)
        assert LlmTranslator.EXCERPT_ORIGINAL_HEADING + "\nAn Iron Sword" in user_prompt
        assert "Ein ⟦Iron⟧schwert" in user_prompt
        assert user_prompt.endswith(f"{LlmTranslator.EXCERPT_TEXT_HEADING}\nIron")
        assert LlmTranslator.TEXT_HEADING not in user_prompt

    def test_excerpt_markers_are_removed_from_reply(
        self, translator: LlmTranslator, client: MagicMock
    ) -> None:
        """
        Tests that excerpt markers kept by the model are removed from its reply.
        """

        # given
        excerpt = TranslationExcerpt(
            text="Iron", prefix="Ein ", suffix="schwert", original_text="An Iron Sword"
        )
        request: TranslationRequest = TestLlmTranslator.create_request(
            excerpt.text, excerpt
        )
        TestLlmTranslator.set_reply(client, " ⟦Eisen⟧ ")

        # when
        result: str = translator._process_request(request)  # pyright: ignore[reportPrivateUsage]

        # then
        assert result == "Eisen"
