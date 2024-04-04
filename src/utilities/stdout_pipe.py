"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import sys

from main import MainApp


class StdoutPipe:
    """
    Class that copies sys.stdout and
    sys.stderr to file and/or console.

    Internal use only!
    """

    _lines: list[str] = []

    def __init__(self, app: MainApp, tag="stdout", encoding="utf8"):
        self.app = app
        self.tag = tag
        self.encoding = encoding
        self.file = open(
            self.app.log_path / self.app.log_name, mode="a", encoding=encoding
        )
        self.last_line = ""
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

    def close(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()

    def write(self, string: str):
        """
        Writes <string> to file and console.
        """

        from . import trim_string

        # Avoid spamming log file
        if string != self.last_line:
            try:
                self.file.write(string)
            except Exception as ex:
                print(f"Logging error occured: {str(ex)}")

        self._lines.append(string)

        try:
            self.stdout.write(string)
            if self.app.statusbar is not None and string.strip():
                self.app.log_signal.emit(
                    trim_string(
                        string.removeprefix("\n").removesuffix("\n"), max_length=200
                    ),
                )
        except AttributeError:
            pass

        self.last_line = string

    def flush(self):
        """
        Flush.
        """

        self.file.flush()
