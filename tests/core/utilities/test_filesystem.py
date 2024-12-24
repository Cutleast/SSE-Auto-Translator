"""
Copyright (c) Cutleast
"""

from typing import TypeVar

from src.core.utilities.filesystem import glob

T = TypeVar("T")


class TestFilesystem:
    """
    Tests `core.utilities.filesystem`.
    """

    @staticmethod
    def compare_lists(list1: list[T], list2: list[T]) -> bool:
        """
        Compares two lists and checks if they contain the same elements.

        Args:
            list1 (list[T]): The first list
            list2 (list[T]): The second list

        Returns:
            bool: `True` if the lists are equal, `False` otherwise
        """

        return set(list1) == set(list2)

    def test_glob_flat(self) -> None:
        """
        Tests `core.utilities.filesystem.glob()` with a flat list.
        """

        # given
        pattern: str = "*.txt"
        files: list[str] = ["a.txt", "b.txt", "c.png"]
        expected_output: list[str] = ["a.txt", "b.txt"]

        # when
        real_output: list[str] = glob(pattern, files)

        # then
        assert TestFilesystem.compare_lists(real_output, expected_output)

    def test_glob_nested(self) -> None:
        """
        Tests `core.utilities.filesystem.glob()` with a single-level folder structure.
        """

        # given
        pattern: str = "*/*.txt"
        files: list[str] = ["a/b.txt", "c/d.png", "e/f.txt"]
        expected_output: list[str] = ["a/b.txt", "e/f.txt"]

        # when
        real_output: list[str] = glob(pattern, files)

        # then
        assert TestFilesystem.compare_lists(real_output, expected_output)

    def test_glob_deep(self) -> None:
        """
        Tests `core.utilities.filesystem.glob()` with a deep folder structure.
        """

        # given
        pattern: str = "**/*.txt"
        files: list[str] = ["a/b/c/d/e/f.txt", "g/h/i/j/k/l/m.txt", "n/o/p/q/r/s/t.png"]
        expected_output: list[str] = ["a/b/c/d/e/f.txt", "g/h/i/j/k/l/m.txt"]

        # when
        real_output: list[str] = glob(pattern, files)

        # then
        assert TestFilesystem.compare_lists(real_output, expected_output)
