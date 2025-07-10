"""
Copyright (c) Cutleast
"""

import logging
import os
import time
from cgi import parse_header
from pathlib import Path
from typing import Optional

import requests as req
from PySide6.QtCore import QObject, Signal

from core.utilities.progress_update import (
    ProgressCallback,
    ProgressUpdate,
    safe_run_callback,
)


class Downloader(QObject):
    """
    Class for downloading files from the internet.
    """

    log: logging.Logger = logging.getLogger("Downloader")

    __stop_signal: Signal = Signal()

    __running: bool = False

    CHUNK_SIZE: int = 1024 * 1024  # 1 MB
    TIMEOUT: int = 5  # 5 seconds

    def __init__(self) -> None:
        super().__init__()

        self.__stop_signal.connect(self.__stop_download)

    def download(
        self,
        download_url: str,
        dest_folder: Path,
        user_agent: str,
        file_name: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Path:
        """
        Downloads a file from the internet and saves it at a specified location.

        Args:
            download_url (str): Direct download URL to file.
            dest_folder (Path): Folder, to which the file gets downloaded to.
            user_agent (str): User agent to use.
            file_name (str, optional):
                Name of downloaded file, only required if the server doesn't return it.
            progress_callback (Optional[ProgressCallback], optional):
                Optional function or method to call with a ProgressUpdate. Defaults to None.

        Returns:
            Path: Path to downloaded file.
        """

        dl_path: Path
        headers: dict[str, str] = {"User-Agent": user_agent}

        with req.Session() as session:
            stream = session.get(
                download_url, stream=True, headers=headers, timeout=Downloader.TIMEOUT
            )

            total_size: int = int(stream.headers.get("Content-Length", "0"))

            _content = stream.headers.get("Content-Disposition")
            if _content and file_name is None:
                file_name = parse_header(_content)[1].get("filename", None)

            if file_name is None:
                self.log.debug(f"Stream Headers: {stream.headers}")
                raise ValueError("No filename given!")

            dl_path = dest_folder / file_name

            self.log.info(
                f"Downloading {file_name!r} from {download_url!r} to '{dest_folder}'..."
            )

            if total_size == 0:
                self.log.warning(
                    "Total file size unknown. No progress information available!"
                )

            if dl_path.is_file():
                if dl_path.stat().st_size == total_size and total_size > 0:
                    self.log.info("File already downloaded.")
                    return dl_path
                else:
                    os.remove(dl_path)
                    self.log.warning(f"Removed already existing file from '{dl_path}'!")

            self.__running = True
            current_size: int = 0
            with dl_path.open("wb") as output_file:
                __start: tuple[float, int] = time.time(), 0
                for data in stream.iter_content(Downloader.CHUNK_SIZE):
                    if self.__running:
                        output_file.write(data)
                        current_size += len(data)
                    else:
                        break

                    __duration: float = time.time() - __start[0]
                    if __duration > 0.5:
                        __speed: int = round(
                            (Downloader.CHUNK_SIZE * __start[1]) / __duration
                        )
                        safe_run_callback(
                            progress_callback,
                            ProgressUpdate(
                                current=current_size,
                                maximum=total_size,
                                status_text=self.tr("Downloading..."),
                                speed=__speed,
                            ),
                        )
                        __start = time.time(), 0
                    else:
                        __start = __start[0], __start[1] + 1

        if self.__running and current_size == total_size:
            self.log.info("Download complete!")

        else:
            self.log.warning("Download incomplete!")
            os.remove(dl_path)

        return dl_path

    def __stop_download(self) -> None:
        self.__running = False

    def stop(self) -> None:
        """
        Thread-safe method to send a stop signal to the running download.
        """

        self.__stop_signal.emit()

    @staticmethod
    def single_download(
        url: str,
        dest_folder: Path,
        user_agent: str,
        file_name: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Path:
        """
        Downloads a single file from a given URL to a destination folder.

        Args:
            url (str): URL of the file to download.
            dest_folder (Path): Folder where the downloaded file should be saved.
            user_agent (str): User agent to use.
            file_name (Optional[str], optional):
                Optional filename to use instead of the one in the URL. Defaults to None.
            progress_callback (Optional[ProgressCallback], optional):
                Optional function or method to call with a ProgressUpdate. Defaults to None.

        Returns:
            Path: Path to the downloaded file.
        """

        return Downloader().download(
            url, dest_folder, user_agent, file_name, progress_callback
        )
