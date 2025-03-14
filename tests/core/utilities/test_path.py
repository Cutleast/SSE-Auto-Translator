"""
Copyright (c) Cutleast
"""

from core.utilities.path import Path


class TestPath:
    """
    Tests `core.utilities.path.Path`.
    """

    def test_init(self) -> None:
        """
        Tests the creation of a `Path` object.
        """

        # given
        path = Path(".")

        # then
        assert isinstance(path, Path)

    def test_join(self) -> None:
        """
        Tests the concatenation of multiple `Path` object.
        """

        # given
        base = Path(".")
        data = base / "data"

        # then
        assert isinstance(data, Path)

    def test_resolve(self) -> None:
        """
        Tests the resolution of a `Path` object.
        """

        # given
        path = Path(".")

        # then
        assert isinstance(path.resolve(), Path)

    def test_parent(self) -> None:
        """
        Tests the parent-property of a `Path` object.
        """

        # given
        path = Path(".").resolve()

        # then
        assert isinstance(path.parent, Path)

    def test_str(self) -> None:
        """
        Tests the string representation of a `Path` object.
        """

        # given
        path = Path("C:\\Windows/System32") / "kernel32.dll"

        # then
        assert isinstance(str(path), str)
        assert str(path) == "C:\\Windows\\System32\\kernel32.dll"
        assert repr(path) == str(path)
        assert f"{path}" == str(path)
