"""
Copyright (c) Cutleast
"""

from typing import Optional

import pytest
from bethkit import Game, Plugin, PluginWriter, Record, WritableGroup, WritableRecord

from core.file_types.plugin.string_indexes import StringIndexes


class TestStringIndexes:
    """
    Tests stable indexes using real bethkit records.
    """

    @staticmethod
    def __get_indexes(
        signature: bytes, subrecords: list[tuple[bytes, bytes]], string_type: bytes
    ) -> list[Optional[int]]:
        """
        Builds a plugin and indexes its selected string subrecords.

        Args:
            signature (bytes): Record signature.
            subrecords (list[tuple[bytes, bytes]]): Subrecord signatures and payloads.
            string_type (bytes): Signature of the strings to index.

        Returns:
            list[Optional[int]]: Indexes in source order.
        """

        with (
            PluginWriter(Game.SKYRIM_SE) as writer,
            WritableGroup.new(signature) as group,
            WritableRecord.new(signature, form_id=0x1234) as writable,
        ):
            for subrecord_type, data in subrecords:
                writable.add_subrecord(subrecord_type, data)

            group.add_record(writable)
            writer.add_group(group)
            data: bytes = writer.write_to_bytes()

        with Plugin.from_bytes(data, Game.SKYRIM_SE, name="Test.esp") as plugin:
            record: Optional[Record] = plugin.find_record(0x1234)
            assert record is not None
            indexes = StringIndexes()
            return [
                indexes.get(record, position)
                for position, subrecord in enumerate(record)
                if subrecord.signature == string_type
            ]

    @pytest.mark.parametrize("condition", [None, bytes(32)])
    def test_identical_journal_entries_are_numbered(
        self, condition: Optional[bytes]
    ) -> None:
        """
        Tests that otherwise identical entries of a stage are numbered by occurrence.
        """

        # given
        subrecords: list[tuple[bytes, bytes]] = [(b"INDX", b"\x0a\0\0\0")]
        for text in (b"First\0", b"Second\0", b"\0", b"First\0"):
            subrecords.append((b"QSDT", b"\0"))
            if condition is not None:
                subrecords.append((b"CTDA", condition))

            subrecords.append((b"CNAM", text))

        # when
        indexes: list[Optional[int]] = TestStringIndexes.__get_indexes(
            b"QUST", subrecords, b"CNAM"
        )

        # then
        assert len(set(indexes)) == 4
        assert None not in indexes

    def test_distinct_journal_conditions_are_unique(self) -> None:
        """
        Tests retaining distinct condition identities without checksum reduction.
        """

        # given
        subrecords: list[tuple[bytes, bytes]] = [(b"INDX", b"\x0a\0\0\0")]
        for condition in range(200):
            subrecords.extend(
                [
                    (b"QSDT", b"\0"),
                    (b"CTDA", condition.to_bytes(4, "little") + bytes(28)),
                    (b"CNAM", b"Journal entry\0"),
                ]
            )

        # when
        indexes: list[Optional[int]] = TestStringIndexes.__get_indexes(
            b"QUST", subrecords, b"CNAM"
        )

        # then
        assert len(set(indexes)) == 200
        assert None not in indexes

    def test_stage_numbers_distinguish_journal_entries(self) -> None:
        """
        Tests that differing stage numbers distinguish identical conditions.
        """

        # given
        subrecords: list[tuple[bytes, bytes]] = []
        for stage in range(200):
            subrecords.extend(
                [
                    (b"INDX", stage.to_bytes(2, "little") + b"\0\0"),
                    (b"QSDT", b"\0"),
                    (b"CNAM", b"Journal entry\0"),
                ]
            )

        # when
        indexes: list[Optional[int]] = TestStringIndexes.__get_indexes(
            b"QUST", subrecords, b"CNAM"
        )

        # then
        assert len(set(indexes)) == 200

    def test_journal_ids_ignore_translation_and_unrelated_fields(self) -> None:
        """
        Tests text independence and stability after inserting unrelated subrecords.
        """

        # given
        original: list[tuple[bytes, bytes]] = [
            (b"INDX", b"\x0a\0\0\0"),
            (b"QSDT", b"\0"),
            (b"CTDA", bytes(32)),
            (b"CNAM", b"First entry\0"),
            (b"QSDT", b"\0"),
            (b"CTDA", bytes([1]) + bytes(31)),
            (b"CNAM", b"Second entry\0"),
        ]
        translated: list[tuple[bytes, bytes]] = [
            (b"EDID", b"QuestEditorId\0"),
            (b"INDX", b"\x14\0\0\0"),
            (b"QSDT", b"\0"),
            (b"CNAM", b"New stage\0"),
            (b"INDX", b"\x0a\0\x01\0"),
            (b"QSDT", b"\x01"),
            (b"CTDA", bytes(32)),
            (b"CNAM", b"Erster Eintrag\0"),
            (b"NAM0", b"Unrelated data\0"),
            (b"QSDT", b"\0"),
            (b"CTDA", bytes([1]) + bytes(31)),
            (b"CNAM", b"Zweiter Eintrag\0"),
        ]

        # when
        original_indexes: list[Optional[int]] = TestStringIndexes.__get_indexes(
            b"QUST", original, b"CNAM"
        )
        translated_indexes: list[Optional[int]] = TestStringIndexes.__get_indexes(
            b"QUST", translated, b"CNAM"
        )

        # then
        assert original_indexes == translated_indexes[1:]
        assert len(set(original_indexes)) == 2

    def test_journal_conditions_are_scoped_to_each_entry(self) -> None:
        """
        Tests reordered entries, reordered conditions and an inserted sibling entry.
        """

        # given
        stage: list[tuple[bytes, bytes]] = [(b"INDX", b"\x0a\0\0\0")]
        first: list[tuple[bytes, bytes]] = [
            (b"QSDT", b"\0"),
            (b"CTDA", bytes(32)),
            (b"CTDA", bytes([1]) + bytes(31)),
            (b"CNAM", b"First\0"),
        ]
        second: list[tuple[bytes, bytes]] = [
            (b"QSDT", b"\0"),
            (b"CTDA", bytes([2]) + bytes(31)),
            (b"CNAM", b"Second\0"),
        ]
        inserted: list[tuple[bytes, bytes]] = [
            (b"QSDT", b"\0"),
            (b"CNAM", b"Inserted\0"),
        ]

        # when
        before: list[Optional[int]] = TestStringIndexes.__get_indexes(
            b"QUST", stage + first + second, b"CNAM"
        )
        after: list[Optional[int]] = TestStringIndexes.__get_indexes(
            b"QUST",
            stage + second + inserted + [first[0], first[2], first[1], first[3]],
            b"CNAM",
        )

        # then
        assert before == [after[2], after[0]]
        assert len(set(after)) == 3

    @pytest.mark.parametrize(
        "signature, subrecords, string_type, expected",
        [
            (b"BOOK", [(b"FULL", b"Book\0")], b"FULL", [None]),
            (
                b"INFO",
                [(b"TRDT", bytes(12) + b"\x07"), (b"NAM1", b"Response\0")],
                b"NAM1",
                [7],
            ),
            (
                b"QUST",
                [(b"QOBJ", b"\x2a\0"), (b"NNAM", b"Objective\0")],
                b"NNAM",
                [42],
            ),
            (
                b"PERK",
                [(b"EPF2", b"Button\0"), (b"EPF3", b"\0\0\x03\0")],
                b"EPF2",
                [3],
            ),
            (
                b"PERK",
                [(b"EPFT", b"\x07"), (b"EPFD", b"First\0"), (b"EPFD", b"Next\0")],
                b"EPFD",
                [0, 1],
            ),
            (
                b"MESG",
                [(b"ITXT", b"Yes\0"), (b"CTDA", bytes(32)), (b"ITXT", b"No\0")],
                b"ITXT",
                [0, 1],
            ),
        ],
    )
    def test_existing_indexes(
        self,
        signature: bytes,
        subrecords: list[tuple[bytes, bytes]],
        string_type: bytes,
        expected: list[Optional[int]],
    ) -> None:
        """
        Tests that non-journal strings keep their historical indexes.
        """

        # when
        indexes: list[Optional[int]] = TestStringIndexes.__get_indexes(
            signature, subrecords, string_type
        )

        # then
        assert indexes == expected
