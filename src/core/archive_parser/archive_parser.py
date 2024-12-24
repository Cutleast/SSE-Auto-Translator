"""
Copyright (c) Cutleast
"""

from io import BufferedReader
from pathlib import Path
from typing import Optional

from .archive import Archive


class ArchiveParser:
    """
    Class for archive parser.
    Used to parse Bethesda archives (.bsa).
    """

    """
    File structure:
    - Header
    - folderRecords
    - fileRecordBlocks
    - fileNameBlock
    """

    archive_path: Path
    archive_stream: Optional[BufferedReader] = None
    parsed_data: Optional[Archive] = None

    def __init__(self, archive_path: Path):
        self.archive_path = archive_path

    def open_stream(self) -> BufferedReader:
        """
        Opens file stream if not already open.
        """

        if self.archive_stream is None:
            self.archive_stream = open(self.archive_path, "rb")

        return self.archive_stream

    def close_stream(self) -> None:
        """
        Closes file stream if opened.
        """

        if self.archive_stream:
            self.archive_stream.close()
            self.archive_stream = None

    def parse_archive(self) -> Archive:
        """
        Parses raw data and returns parsed
        Archive instance.
        """

        stream: BufferedReader = self.open_stream()
        self.parsed_data = Archive(self.archive_path, stream).parse()

        return self.parsed_data
