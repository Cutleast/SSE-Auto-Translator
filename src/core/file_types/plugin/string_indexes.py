"""
Copyright (c) Cutleast
"""

import hashlib
from typing import Optional

from bethkit import Record


class StringIndexes:
    """
    Derives text-independent indexes for repeated plugin strings.

    Response, objective, perk and message indexes retain their historical meaning.
    Quest journal indexes depend on the stage number and the conditions of each entry.
    Entries that are otherwise identical within a stage are numbered by occurrence.
    """

    __form_id: Optional[int]
    __indexes: dict[int, int]

    def __init__(self) -> None:  # noqa: D107
        self.__form_id = None
        self.__indexes = {}

    def get(self, record: Record, subrecord_index: int) -> Optional[int]:
        """
        Gets the stable index for a string's exact subrecord position.

        Args:
            record (Record): Source record from the current plugin.
            subrecord_index (int): Position supplied by bethkit.

        Returns:
            Optional[int]: Index, or None for a non-repeated string.
        """

        if record.signature not in [b"INFO", b"QUST", b"PERK", b"MESG"]:
            return None

        if self.__form_id != record.form_id:
            self.__indexes = StringIndexes.__scan(record)
            self.__form_id = record.form_id

        return self.__indexes.get(subrecord_index)

    @staticmethod
    def __scan(record: Record) -> dict[int, int]:
        """
        Indexes repeated strings in a single pass through a record.

        Args:
            record (Record): Source record.

        Returns:
            dict[int, int]: String indexes keyed by subrecord position.
        """

        indexes: dict[int, int] = {}
        response: int = 0
        objective: int = 0
        message: int = 0
        perk_type: Optional[int] = None
        perk_text: int = 0
        pending_button: Optional[int] = None
        stage: bytes = b""
        conditions: list[bytes] = []
        occurrences: dict[bytes, int] = {}

        for position, subrecord in enumerate(record):
            signature: bytes = subrecord.signature
            match record.signature:
                case b"INFO":
                    match signature:
                        case b"TRDT":
                            response = int.from_bytes(
                                subrecord.raw_bytes[12:13], "little"
                            )
                        case b"NAM1":
                            indexes[position] = response

                case b"QUST":
                    match signature:
                        case b"INDX":
                            # Only the stage number; the stage flags are no identity.
                            stage = subrecord.raw_bytes[:2]
                            conditions = []
                        case b"QSDT":
                            conditions = []
                        case b"CTDA":
                            conditions.append(subrecord.raw_bytes)
                        case b"CIS1" | b"CIS2" if conditions:
                            data: bytes = subrecord.raw_bytes
                            conditions[-1] += (
                                signature + len(data).to_bytes(4, "little") + data
                            )
                        case b"CNAM":
                            # Sorting makes condition and journal-entry reordering harmless.
                            entry: bytes = stage + b"".join(
                                len(condition).to_bytes(4, "little") + condition
                                for condition in sorted(conditions)
                            )
                            occurrence: int = occurrences.get(entry, 0)
                            occurrences[entry] = occurrence + 1
                            indexes[position] = int.from_bytes(
                                hashlib.blake2b(
                                    entry + occurrence.to_bytes(4, "little"),
                                    # Indexes only need to be unique within a record.
                                    digest_size=4,
                                ).digest(),
                                "big",
                            )
                        case b"QOBJ":
                            objective = int.from_bytes(
                                subrecord.raw_bytes[:2], "little", signed=True
                            )
                        case b"NNAM":
                            indexes[position] = objective

                case b"PERK":
                    if pending_button is not None and signature == b"EPF3":
                        indexes[pending_button] = int.from_bytes(
                            subrecord.raw_bytes[2:], "little"
                        )

                    pending_button = None

                    match signature:
                        case b"EPFT":
                            perk_type = int.from_bytes(subrecord.raw_bytes[:1], "little")
                        case b"EPFD":
                            indexes[position] = perk_text
                            if perk_type == 7:
                                perk_text += 1
                        case b"EPF2":
                            pending_button = position

                case _ if signature == b"ITXT":
                    indexes[position] = message
                    message += 1

        return indexes
