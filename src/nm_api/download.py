"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from .api import NexusModsApi
import requests as req

import os
from pathlib import Path


class Download:
    """
    Class for single file downloads.
    """

    CHUNK_SIZE = 1024 * 1024  # 1 MB

    running: bool = None

    cur_speed: int = None
    """
    Current Speed in Bytes per Second
    """

    previous_size: int = None
    """
    Previous Size of downloaded Data, for calculation of Speed
    """

    current_size: int = None
    """
    Size of downloaded Data in Bytes
    """

    file_size: int = None
    """
    Total Download Size
    """

    def __init__(self, url: str, dl_path: Path):
        self.url = url
        self.dl_path = dl_path

    def download(self):
        """
        Downloads file.
        """

        headers = {
            "User-Agent": NexusModsApi.user_agent,
        }
        stream = req.get(self.url, stream=True, headers=headers)

        self.file_size = int(stream.headers.get("Content-Length", "0"))

        self.running = True
        self.previous_size = 0
        self.current_size = 0
        self.cur_speed = 0

        with self.dl_path.open("wb") as file:
            for data in stream.iter_content(chunk_size=self.CHUNK_SIZE):
                if self.running:
                    file.write(data)
                    self.current_size += len(data)
                else:
                    break

        self.running = False

        if self.current_size < self.file_size:
            os.remove(self.dl_path)

    def cancel_download(self):
        """
        Cancels download.
        """

        self.running = False
