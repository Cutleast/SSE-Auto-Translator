"""
Copyright (c) Cutleast
"""

from requests import Response, get

from core.translation_provider.exceptions import Non200HttpError

from .cache import cache


@cache
def get_raw_web_content(url: str) -> bytes:
    """
    Fetches raw content from the given URL. The result is cached.

    Args:
        url (str): URL to fetch content from.

    Raises:
        Non200HttpError: If the status code is not 200.

    Returns:
        bytes: Raw content of the URL.
    """

    res: Response = get(url)

    if res.status_code != 200:
        raise Non200HttpError(url, res.status_code)

    return res.content
