"""
Copyright (c) Cutleast
"""

import os
from dataclasses import dataclass
from io import BufferedReader, BytesIO
from pathlib import Path

import lz4.frame

from core.utilities.filesystem import glob

from .datatypes import Integer, String
from .file_name_block import FileNameBlock
from .file_record import FileRecord, FileRecordBlock
from .folder_record import FolderRecord
from .header import Header


@dataclass
class Archive:
    """
    Contains parsed archive data.
    """

    archive_path: Path
    data_stream: BufferedReader

    def match_names(self) -> dict[str, FileRecord]:
        """
        Matches file names to their records.
        """

        result: dict[str, FileRecord] = {}

        index = 0
        for file_record_block in self.file_record_blocks:
            for file_record in file_record_block.file_records:
                file_path = file_record_block.name.decode()[:-1]
                file_name = self.file_name_block.file_names[index]
                file = str(Path(file_path) / file_name).replace("\\", "/")
                result[file] = file_record
                index += 1

        return result

    def process_compression_flags(self) -> None:
        """
        Processes compression flags in files.
        """

        for file_record in self.files.values():
            has_compression_flag = file_record.has_compression_flag()

            if has_compression_flag:
                file_record.compressed = not self.header.archive_flags[
                    "Compressed Archive"
                ]
            else:
                file_record.compressed = self.header.archive_flags["Compressed Archive"]

    def parse(self) -> "Archive":
        self.header = Header(self.data_stream).parse()
        self.folders = [
            FolderRecord(self.data_stream).parse()
            for i in range(self.header.folder_count)
        ]
        self.file_record_blocks = [
            FileRecordBlock(self.data_stream).parse(self.folders[i].count)
            for i in range(len(self.folders))
        ]
        self.file_name_block = FileNameBlock(self.data_stream).parse(
            self.header.file_count
        )
        self.files = self.match_names()

        self.process_compression_flags()

        return self

    def glob(self, pattern: str, case_sensitive: bool = False) -> list[str]:
        """
        Returns a list of file paths that match a specified glob pattern.

        Args:
            pattern (str): Glob pattern.
            case_sensitive (bool, optional): Case sensitive. Defaults to False.

        Returns:
            list[str]: List of matching filenames
        """

        return glob(pattern, list(self.files.keys()), case_sensitive)

    def extract_file(self, filename: str | Path, dest_folder: Path) -> None:
        """
        Extracts `filename` from archive to `dest_folder`.
        """

        filename = str(filename).replace("\\", "/")

        if filename not in self.files:
            raise FileNotFoundError(f"{filename!r} is not in archive!")

        file_record = self.files[filename]

        # Go to file raw data
        self.data_stream.seek(file_record.offset)

        if self.header.archive_flags["Embed File Names"]:
            filename = String.bstring(self.data_stream).decode(errors="ignore")

        if file_record.compressed:
            original_size = Integer.ulong(self.data_stream)  # noqa: F841
            data = self.data_stream.read(file_record.size - 4)
            data = lz4.frame.decompress(data)
        else:
            data = self.data_stream.read(file_record.size)

        destination = dest_folder / filename
        os.makedirs(destination.parent, exist_ok=True)
        with open(destination, "wb") as file:
            file.write(data)

        if not destination.is_file():
            raise Exception(
                f"Failed to extract file '{filename}' from archive '{self.archive_path}'!"
            )

    def get_file_stream(self, filename: str | Path) -> BytesIO:
        """
        Instead of extracting the file this returns a file stream to the file data.
        """

        filename = Path(filename).name

        if filename not in self.files:
            raise FileNotFoundError("File is not in archive!")

        file_record = self.files[filename]

        # Get current index
        cur_index = self.data_stream.tell()

        # Go to file raw data
        self.data_stream.seek(file_record.offset)

        if self.header.archive_flags["Embed File Names"]:
            filename = String.bstring(self.data_stream).decode(errors="ignore")

        if file_record.compressed:
            original_size = Integer.ulong(self.data_stream)  # noqa: F841
            data = self.data_stream.read(file_record.size - 4)
            data = lz4.frame.decompress(data)
        else:
            data = self.data_stream.read(file_record.size)

        # Go back to current index
        self.data_stream.seek(cur_index)

        return BytesIO(data)
