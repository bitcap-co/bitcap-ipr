# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import struct
import zlib
from pathlib import Path
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict

from .errors import (
    FirmwareChecksumError,
    IncompatibleFirmwareError,
    InvalidFirmwareImageError,
)

_CONTAINER_MAGIC = 0xABABABAB
_HEADER_SIZE = 36
_HEADER_STRUCT = struct.Struct("<9I")
_CRC_OFFSET = 24
_ITEM_MIN_SIZE = 172
_ITEM_NAME_SIZE = 64
_ITEM_CHIP_SIZE = 32
_ITEM_CONTROL_BOARD_SIZE = 32
_ITEM_MINER_SIZE = 32
_MAX_ITEM_COUNT = 1024


class BitmainContainerHeader(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    magic: int
    version: int
    header_size: int
    item_count: int
    item_size: int
    data_offset: int
    crc32: int


class BitmainContainerItem(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    chip_model: str
    control_board_model: str
    miner_model: str
    data_offset: int
    data_size: int


class BitmainFirmwarePayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, arbitrary_types_allowed=True
    )

    data: bytes
    item: BitmainContainerItem | None = None


class BitmainFirmwareImage:
    """A raw Bitmain image or a validated multi-miner BMU container."""

    def __init__(
        self,
        data: bytes,
        source: Path | None,
        header: BitmainContainerHeader | None,
        items: tuple[BitmainContainerItem, ...],
    ) -> None:
        self._data: bytes = data
        self._source: Path | None = source
        self._header: BitmainContainerHeader | None = header
        self._items: tuple[BitmainContainerItem, ...] = items

    @property
    def source(self) -> Path | None:
        return self._source

    @property
    def header(self) -> BitmainContainerHeader | None:
        return self._header

    @property
    def items(self) -> tuple[BitmainContainerItem, ...]:
        return self._items

    @property
    def is_container(self) -> bool:
        return self._header is not None

    @classmethod
    def from_path(cls, path: Path) -> Self:
        try:
            data = path.read_bytes()
        except OSError as ex:
            raise InvalidFirmwareImageError(
                f"Failed to read firmware image '{path}': {ex}"
            ) from ex
        return cls.from_bytes(data, source=path)

    @classmethod
    def from_bytes(cls, data: bytes, source: Path | None = None) -> Self:
        if not data:
            raise InvalidFirmwareImageError("Firmware image is empty")

        header = cls._candidate_header(data)
        if header is None:
            return cls(data=data, source=source, header=None, items=())

        cls._validate_checksum(data, header)
        items = cls._parse_items(data, header)
        return cls(data=data, source=source, header=header, items=items)

    @staticmethod
    def _candidate_header(data: bytes) -> BitmainContainerHeader | None:
        if len(data) < _HEADER_SIZE:
            return None

        values: tuple[int, ...] = _HEADER_STRUCT.unpack_from(data)
        header = BitmainContainerHeader(
            magic=values[0],
            version=values[1],
            header_size=values[2],
            item_count=values[3],
            item_size=values[4],
            data_offset=values[5],
            crc32=values[6],
        )

        if header.magic != _CONTAINER_MAGIC:
            return None
        if header.header_size != _HEADER_SIZE:
            raise InvalidFirmwareImageError(
                f"Unsupported BMU container header size: {header.header_size}"
            )
        if not 0 < header.item_count <= _MAX_ITEM_COUNT:
            raise InvalidFirmwareImageError(
                f"Invalid BMU container item count: {header.item_count}"
            )
        if header.item_size < _ITEM_MIN_SIZE:
            raise InvalidFirmwareImageError(
                f"Invalid BMU container item size: {header.item_size}"
            )
        if header.data_offset < header.header_size:
            raise InvalidFirmwareImageError(
                "BMU container data offset overlaps its header"
            )
        return header

    @staticmethod
    def _validate_checksum(data: bytes, header: BitmainContainerHeader) -> None:
        crc = zlib.crc32(data[:_CRC_OFFSET])
        crc = zlib.crc32(b"\x00\x00\x00\x00", crc)
        crc = zlib.crc32(data[_CRC_OFFSET + 4 :], crc)
        if crc != header.crc32:
            raise FirmwareChecksumError(
                "Invalid BMU container checksum: "
                + f"expected 0x{header.crc32:08x}, calculated 0x{crc:08x}"
            )

    @classmethod
    def _parse_items(
        cls, data: bytes, header: BitmainContainerHeader
    ) -> tuple[BitmainContainerItem, ...]:
        table_end = header.header_size + header.item_count * header.item_size
        if table_end > len(data):
            raise InvalidFirmwareImageError("BMU container item table is truncated")
        if header.data_offset < table_end:
            raise InvalidFirmwareImageError(
                "BMU container data overlaps the item table"
            )
        if header.data_offset > len(data):
            raise InvalidFirmwareImageError(
                "BMU container data offset is outside the image"
            )

        items: list[BitmainContainerItem] = []
        ranges: list[tuple[int, int]] = []
        for index in range(header.item_count):
            offset = header.header_size + index * header.item_size
            item_data = data[offset : offset + header.item_size]
            item = cls._parse_item(item_data, index)
            if item.data_size == 0:
                raise InvalidFirmwareImageError(
                    f"BMU container item {index} has an empty payload"
                )
            item_end = item.data_offset + item.data_size
            if item.data_offset < header.data_offset or item_end > len(data):
                raise InvalidFirmwareImageError(
                    f"BMU container item {index} payload is outside the image"
                )
            items.append(item)
            ranges.append((item.data_offset, item_end))

        previous_end = header.data_offset
        for start, end in sorted(ranges):
            if start < previous_end:
                raise InvalidFirmwareImageError("BMU container item payloads overlap")
            previous_end = end

        return tuple(items)

    @classmethod
    def _parse_item(cls, data: bytes, index: int) -> BitmainContainerItem:
        if len(data) < _ITEM_MIN_SIZE:
            raise InvalidFirmwareImageError(f"BMU container item {index} is truncated")

        name_len, chip_len, control_len, miner_len = data[:4]
        lengths = (
            ("name", name_len, _ITEM_NAME_SIZE),
            ("chip model", chip_len, _ITEM_CHIP_SIZE),
            ("control board model", control_len, _ITEM_CONTROL_BOARD_SIZE),
            ("miner model", miner_len, _ITEM_MINER_SIZE),
        )
        for field, length, maximum in lengths:
            if length > maximum:
                raise InvalidFirmwareImageError(
                    f"BMU container item {index} {field} length exceeds {maximum}"
                )

        return BitmainContainerItem(
            name=cls._decode_item_text(data, 4, name_len, index, "name"),
            chip_model=cls._decode_item_text(data, 68, chip_len, index, "chip model"),
            control_board_model=cls._decode_item_text(
                data, 100, control_len, index, "control board model"
            ),
            miner_model=cls._decode_item_text(
                data, 132, miner_len, index, "miner model"
            ),
            data_offset=struct.unpack_from("<I", data, 164)[0],
            data_size=struct.unpack_from("<I", data, 168)[0],
        )

    @staticmethod
    def _decode_item_text(
        data: bytes, offset: int, length: int, index: int, field: str
    ) -> str:
        try:
            return data[offset : offset + length].decode("ascii")
        except UnicodeDecodeError as ex:
            raise InvalidFirmwareImageError(
                f"BMU container item {index} has invalid {field} metadata"
            ) from ex

    def payload_for(
        self,
        miner_model: str,
        control_board_model: str,
        *,
        enforce_compatibility: bool = True,
    ) -> BitmainFirmwarePayload:
        if self._header is None:
            if enforce_compatibility:
                raise IncompatibleFirmwareError(
                    "Raw Bitmain firmware does not contain compatibility metadata"
                )
            return BitmainFirmwarePayload(data=self._data)

        matches = tuple(
            item
            for item in self._items
            if item.miner_model == miner_model
            and item.control_board_model == control_board_model
        )
        if len(matches) > 1:
            raise InvalidFirmwareImageError(
                "BMU container has multiple entries for "
                + f"{miner_model!r}/{control_board_model!r}"
            )
        if matches:
            return self._payload(matches[0])

        if not enforce_compatibility and len(self._items) == 1:
            return self._payload(self._items[0])

        available = ", ".join(
            f"{item.miner_model}/{item.control_board_model}" for item in self._items
        )
        detail = f" Available images: {available}." if available else ""
        raise IncompatibleFirmwareError(
            "No firmware image matches "
            + f"{miner_model!r}/{control_board_model!r}.{detail}"
        )

    def _payload(self, item: BitmainContainerItem) -> BitmainFirmwarePayload:
        end = item.data_offset + item.data_size
        return BitmainFirmwarePayload(
            data=self._data[item.data_offset : end],
            item=item,
        )
