"""
Copyright (c) Cutleast

This package contains utility modules that can be accessed and run
via the SSE-AT commandline.
"""

from utilities.db_gen.main import DbGen

from .esp2dsd.main import Esp2Dsd
from .utility import Utility

UTILS: list[type[Utility]] = [
    Esp2Dsd,
    DbGen,
]
"""
List of currently enabled commandline utilities.
"""
