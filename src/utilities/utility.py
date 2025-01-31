"""
Copyright (c) Cutleast
"""

import logging
from abc import abstractmethod
from argparse import Namespace, _SubParsersAction
from typing import NoReturn


class Utility:
    """
    Base class for all commandline utilities.
    """

    log: logging.Logger

    def __init__(self) -> None:
        self.log = logging.getLogger(self.__repr__())

    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def add_subparser(self, subparsers: _SubParsersAction) -> None:
        """
        Adds a subparser to the specified subparsers.

        Args:
            subparsers (_SubParsersAction):
                Subparsers to add subparser to
        """

    @abstractmethod
    def run(self, args: Namespace, exit: bool = True) -> None | NoReturn:
        """
        Runs the Utility with the specified commandline arguments.

        Args:
            args (Namespace): Namespace parsed from the argparse.ArgumentParser
            exit (bool, optional):
                Toggles whether the Utility exits the app after its execution
                (only if executed by the user). Defaults to True.
        """
