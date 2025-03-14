"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from typing import override

import pytest

from core.utilities.container_utils import ReferenceDict


class TestContainerUtils:
    """
    Tests `core.utilities.container_utils`.
    """

    def test_reference_dict(self) -> None:
        """
        Tests hashing and indexing of mutable objects with changing hashes in
        `core.utilities.container_utils.ReferenceDict`.
        """

        @dataclass
        class TestObject:
            name: str
            age: int
            num_of_children: int

            @override
            def __hash__(self) -> int:
                return hash((self.name, self.age, self.num_of_children))

        # given
        test_dict: ReferenceDict[TestObject, str] = ReferenceDict({})
        regular_dict: dict[TestObject, str] = {}

        # when
        test_object: TestObject = TestObject(
            name="Test",
            age=1,
            num_of_children=0,
        )
        test_dict[test_object] = "test"
        regular_dict[test_object] = "test"

        test_object.num_of_children += 1

        # then
        assert test_dict[test_object] == "test"
        assert list(test_dict.items())[0] == (test_object, "test")

        with pytest.raises(KeyError):
            regular_dict[test_object]
