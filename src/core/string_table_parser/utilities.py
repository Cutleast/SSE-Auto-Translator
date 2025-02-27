"""
Copyright (c) Cutleast
"""

import os

from core.plugin_interface.datatypes import Stream


def get_stream_size(stream: Stream) -> int:
    """
    Gets length of `stream`.
    """

    cur_offset = stream.tell()

    length = stream.seek(0, os.SEEK_END)

    stream.seek(cur_offset)

    return length
