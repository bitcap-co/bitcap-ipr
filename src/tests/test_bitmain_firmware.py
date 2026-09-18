# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from mod.ipr_asic.firmware import (
    BitmainFirmwareImage,
    FirmwareChecksumError,
    IncompatibleFirmwareError,
    InvalidFirmwareImageError,
)

_HEADER_SIZE = 36
_ITEM_SIZE = 172


def _item(
    name: str,
    chip: str,
    control_board: str,
    miner: str,
    data_offset: int,
    data_size: int,
) -> bytes:
    item = bytearray(_ITEM_SIZE)
    values = (
        (name.encode("ascii"), 4, 64),
        (chip.encode("ascii"), 68, 32),
        (control_board.encode("ascii"), 100, 32),
        (miner.encode("ascii"), 132, 32),
    )
    item[:4] = bytes(len(value) for value, _, _ in values)
    for value, offset, maximum in values:
        if len(value) > maximum:
            raise ValueError("test metadata exceeds its fixed-width field")
        item[offset : offset + len(value)] = value
    struct.pack_into("<II", item, 164, data_offset, data_size)
    return bytes(item)


def _apply_crc(data: bytes) -> bytes:
    patched = bytearray(data)
    patched[24:28] = b"\x00\x00\x00\x00"
    crc = zlib.crc32(patched)
    struct.pack_into("<I", patched, 24, crc)
    return bytes(patched)


def _container(
    entries: list[tuple[str, str, str, str, bytes]],
    *,
    payload_offsets: list[int] | None = None,
) -> bytes:
    data_offset = _HEADER_SIZE + len(entries) * _ITEM_SIZE
    next_offset = data_offset
    items: list[bytes] = []
    payload = bytearray()
    for index, (name, chip, control_board, miner, item_payload) in enumerate(entries):
        item_offset = (
            payload_offsets[index] if payload_offsets is not None else next_offset
        )
        items.append(
            _item(
                name,
                chip,
                control_board,
                miner,
                item_offset,
                len(item_payload),
            )
        )
        payload.extend(item_payload)
        next_offset += len(item_payload)

    header = struct.pack(
        "<9I",
        0xABABABAB,
        1,
        _HEADER_SIZE,
        len(entries),
        _ITEM_SIZE,
        data_offset,
        0,
        0,
        0,
    )
    return _apply_crc(header + b"".join(items) + bytes(payload))


class TestBitmainFirmwareImage(unittest.TestCase):
    def test_extracts_matching_image_from_multi_image_container(self) -> None:
        data = _container(
            [
                ("s19", "BM1398", "XILINX", "Antminer S19", b"s19-image"),
                (
                    "s19j-pro",
                    "BM1362",
                    "AMLOGIC",
                    "Antminer S19j Pro",
                    b"s19j-pro-image",
                ),
            ]
        )

        image = BitmainFirmwareImage.from_bytes(data)
        payload = image.payload_for("Antminer S19j Pro", "AMLOGIC")

        self.assertTrue(image.is_container)
        self.assertEqual(len(image.items), 2)
        self.assertEqual(payload.data, b"s19j-pro-image")
        item = payload.item
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.name, "s19j-pro")

    def test_rejects_container_with_bad_checksum(self) -> None:
        data = bytearray(
            _container([("s19", "BM1398", "XILINX", "Antminer S19", b"firmware")])
        )
        data[-1] ^= 0xFF

        with self.assertRaises(FirmwareChecksumError):
            _ = BitmainFirmwareImage.from_bytes(bytes(data))

    def test_rejects_truncated_item_table(self) -> None:
        data_offset = _HEADER_SIZE + 2 * _ITEM_SIZE
        header = struct.pack(
            "<9I",
            0xABABABAB,
            1,
            _HEADER_SIZE,
            2,
            _ITEM_SIZE,
            data_offset,
            0,
            0,
            0,
        )
        data = _apply_crc(header + bytes(_ITEM_SIZE))

        with self.assertRaisesRegex(InvalidFirmwareImageError, "table is truncated"):
            _ = BitmainFirmwareImage.from_bytes(data)

    def test_rejects_item_payload_outside_image(self) -> None:
        data = _container(
            [("s19", "BM1398", "XILINX", "Antminer S19", b"firmware")],
            payload_offsets=[10_000],
        )

        with self.assertRaisesRegex(InvalidFirmwareImageError, "outside the image"):
            _ = BitmainFirmwareImage.from_bytes(data)

    def test_rejects_overlapping_item_payloads(self) -> None:
        data_offset = _HEADER_SIZE + 2 * _ITEM_SIZE
        data = _container(
            [
                ("first", "BM1", "BOARD1", "Miner 1", b"12345678"),
                ("second", "BM2", "BOARD2", "Miner 2", b"abcdefgh"),
            ],
            payload_offsets=[data_offset, data_offset + 4],
        )

        with self.assertRaisesRegex(InvalidFirmwareImageError, "payloads overlap"):
            _ = BitmainFirmwareImage.from_bytes(data)

    def test_reports_available_images_for_incompatible_miner(self) -> None:
        data = _container([("s19", "BM1398", "XILINX", "Antminer S19", b"firmware")])
        image = BitmainFirmwareImage.from_bytes(data)

        with self.assertRaisesRegex(IncompatibleFirmwareError, "Antminer S19/XILINX"):
            _ = image.payload_for("Antminer S21", "AMLOGIC")

    def test_force_selects_only_item_from_container(self) -> None:
        data = _container([("s19", "BM1398", "XILINX", "Antminer S19", b"firmware")])
        image = BitmainFirmwareImage.from_bytes(data)

        payload = image.payload_for(
            "Antminer S21", "AMLOGIC", enforce_compatibility=False
        )

        self.assertEqual(payload.data, b"firmware")

    def test_force_cannot_choose_between_multiple_container_items(self) -> None:
        data = _container(
            [
                ("first", "BM1", "BOARD1", "Miner 1", b"first"),
                ("second", "BM2", "BOARD2", "Miner 2", b"second"),
            ]
        )
        image = BitmainFirmwareImage.from_bytes(data)

        with self.assertRaises(IncompatibleFirmwareError):
            _ = image.payload_for("Other", "Other", enforce_compatibility=False)

    def test_raw_image_requires_explicit_compatibility_override(self) -> None:
        image = BitmainFirmwareImage.from_bytes(b"opaque single-miner image")

        self.assertFalse(image.is_container)
        with self.assertRaises(IncompatibleFirmwareError):
            _ = image.payload_for("Antminer S19", "XILINX")

        payload = image.payload_for(
            "Antminer S19", "XILINX", enforce_compatibility=False
        )
        self.assertEqual(payload.data, b"opaque single-miner image")
        self.assertIsNone(payload.item)

    def test_loads_image_from_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "firmware.bmu"
            _ = path.write_bytes(b"opaque image")

            image = BitmainFirmwareImage.from_path(path)

        self.assertEqual(image.source, path)

    def test_rejects_empty_image(self) -> None:
        with self.assertRaisesRegex(InvalidFirmwareImageError, "empty"):
            _ = BitmainFirmwareImage.from_bytes(b"")


if __name__ == "__main__":
    _ = unittest.main()
