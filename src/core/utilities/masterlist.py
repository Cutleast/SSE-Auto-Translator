"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

import jstyleson as json
import requests as req

log: logging.Logger = logging.getLogger("Utilities.Masterlist")

__masterlist: Optional[dict[str, dict]] = None
"""
For caching the masterlist.
"""


def get_masterlist(language: str, cache: bool = True) -> dict[str, dict]:
    """
    Gets the masterlist from the GitHub Repository.

    Args:
        language (str): Language to get masterlist for.
        cache (bool, optional):
            Whether to get the masterlist from the cache. Defaults to True.

    Returns:
        dict[str, dict]: Masterlist
    """

    global __masterlist

    language = language.lower()

    REPO_NAME = "SSE-Auto-Translator"
    REPO_OWNER = "Cutleast"
    BRANCH = "master"
    INDEX_PATH = "masterlists/index.json"

    if __masterlist is None or not cache:
        url: Optional[str] = (
            f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{INDEX_PATH}"
        )

        res: req.Response = req.get(url, timeout=3)

        if res.status_code == 200:
            data: str = res.content.decode()
            index: dict[str, str] = json.loads(data)

            url = index.get(language)

            if url is None:
                log.error(f"No masterlist for {language} available!")
                __masterlist = {}

                return __masterlist

            res = req.get(url, timeout=3)

            if res.status_code == 200:
                data = res.content.decode()
                __masterlist = json.loads(data)
            else:
                log.debug(f"Request URL: {url!r}")
                raise Exception(f"Request failed! Status Code: {res.status_code}")

        else:
            log.debug(f"Request URL: {url!r}")
            raise Exception(f"Request failed! Status Code: {res.status_code}")

    return __masterlist or {}
