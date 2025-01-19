"""
Copyright (c) Cutleast
"""


class Clipboard:
    """
    Mocked clipboard for ui-related tests.
    """

    __content: str = ""

    def copy(self, text: str) -> None:
        self.__content = text

    def paste(self) -> str:
        return self.__content
