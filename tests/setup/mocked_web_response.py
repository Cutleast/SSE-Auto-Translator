"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any, Self

import jstyleson as json
from pydantic import BaseModel
from requests_mock import Mocker as RequestsMock


class MockedWebResponse(BaseModel, frozen=True):
    """
    Represents a recorded web response that is served by `requests_mock` in tests.
    """

    method: str
    """The HTTP method of the request."""

    url: str
    """The requested URL."""

    status_code: int
    """The HTTP status code of the response."""

    headers: dict[str, str]
    """The headers of the response."""

    body: Any
    """The body of the response (either a JSON-compatible object or a string)."""

    @classmethod
    def load_from_folder(cls, folder: Path) -> list[Self]:
        """
        Loads all recorded responses from the JSON files in the specified folder.

        Args:
            folder (Path): The folder with the recorded responses.

        Returns:
            list[Self]: The loaded responses.
        """

        responses: list[Self] = []
        for response_file in sorted(folder.glob("*.json")):
            raw_responses: list[dict[str, Any]] = json.loads(response_file.read_text())
            responses.extend(
                cls(
                    method=raw_response["method"],
                    url=raw_response["url"],
                    status_code=raw_response["status_code"],
                    headers=raw_response.get("response_headers", {}),
                    body=raw_response["response_body"],
                )
                for raw_response in raw_responses
            )

        return responses

    def register(self, requests_mock: RequestsMock) -> None:
        """
        Registers this response at the specified `requests_mock` instance.

        Args:
            requests_mock (RequestsMock): The `requests_mock` instance.
        """

        if isinstance(self.body, (dict, list)):
            requests_mock.register_uri(
                self.method,
                self.url,
                status_code=self.status_code,
                headers=self.headers,
                json=self.body,
            )
        else:
            requests_mock.register_uri(
                self.method,
                self.url,
                status_code=self.status_code,
                headers=self.headers,
                text=self.body,
            )
