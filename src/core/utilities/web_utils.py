"""
Copyright (c) Cutleast
"""

import hashlib


def get_url_identifier(url: str) -> str:
    """
    Calcuates a unique identifier for the given URL.

    Args:
        url (str): URL

    Returns:
        str: Unique identifier
    """

    return hashlib.sha256(url.encode()).hexdigest()[:8]
