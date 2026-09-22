# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import hashlib
import io
import re
import struct
import tarfile
import zlib
from pathlib import Path, PurePosixPath
from typing import ClassVar, Literal, Self, cast

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from pydantic import BaseModel, ConfigDict

from .errors import (
    FirmwareSignatureError,
    IncompatibleFirmwareError,
    InvalidFirmwareImageError,
)

_REQUIRED_SIGNED_FILES = frozenset(
    {
        "cert.pem",
        "cert.pem.sig",
        "fw.tar.gz",
        "fw.tar.gz.sig",
        "runme.sh",
        "runme.sh.sig",
        "version_number",
    }
)
_REQUIRED_FLAT_FILES = frozenset(
    {"am335x-boneblack-bitmainer.dtb", "initramfs.bin.SD", "runme.sh"}
)
_UBOOT_MAGIC = 0x27051956
_DTB_MAGIC = 0xD00DFEED
_UBOOT_HEADER_SIZE = 64
_UBOOT_HEADER_STRUCT = struct.Struct(">7I4B32s")
_DTB_HEADER_STRUCT = struct.Struct(">10I")
_MAX_OUTER_MEMBERS = 64
_MAX_INNER_MEMBERS = 512
_MAX_MEMBER_SIZE = 512 * 1024 * 1024
_MAX_EXPANDED_SIZE = 1024 * 1024 * 1024

_FILENAME_PATTERNS = (
    re.compile(
        r"^Antminer-(?P<model>L3\+\+|L3\+|L3)-"
        + r"(?P<build_date>\d{12})-(?P<variant>[A-Za-z0-9._-]+)\.tar\.gz$"
    ),
    re.compile(
        r"^Antminer-(?P<model>Z15)(?:-[A-Za-z0-9.+]+)*-"
        + r"(?P<build_date>\d{12})(?:_(?P<variant>[A-Za-z0-9._-]+))?\.tar\.gz$"
    ),
)


class BitmainLegacyMetadata(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    filename: str
    miner_model: str | None
    build_date: str | None
    variant: str | None
    package_version: str | None
    signer_fingerprint: str | None
    archive_format: Literal["signed", "flat"]
    signature_valid: bool


class BitmainLegacyFirmwareImage:
    """A validated legacy Bitmain tar firmware package."""

    def __init__(
        self, data: bytes, source: Path | None, metadata: BitmainLegacyMetadata
    ):
        self._data: bytes = data
        self._source: Path | None = source
        self._metadata: BitmainLegacyMetadata = metadata

    @property
    def source(self) -> Path | None:
        return self._source

    @property
    def metadata(self) -> BitmainLegacyMetadata:
        return self._metadata

    @classmethod
    def from_path(cls, path: Path) -> Self:
        try:
            data = path.read_bytes()
        except OSError as ex:
            raise InvalidFirmwareImageError(
                f"Failed to read firmware image '{path}': {ex}"
            ) from ex
        return cls.from_bytes(data, filename=path.name, source=path)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        *,
        filename: str,
        source: Path | None = None,
    ) -> Self:
        if not data:
            raise InvalidFirmwareImageError("Firmware archive is empty")

        outer = cls._read_archive(
            data,
            archive_name="firmware package",
            max_members=_MAX_OUTER_MEMBERS,
        )
        package_version: str | None
        signer_fingerprint: str | None
        archive_format: Literal["signed", "flat"]
        signature_valid: bool
        if _REQUIRED_SIGNED_FILES.issubset(outer):
            public_key = cls._load_public_key(outer["cert.pem"])
            cls._verify_signature(
                public_key,
                outer["fw.tar.gz"],
                outer["fw.tar.gz.sig"],
            )
            _ = cls._read_archive(
                outer["fw.tar.gz"],
                archive_name="inner firmware archive",
                max_members=_MAX_INNER_MEMBERS,
            )
            try:
                package_version = outer["version_number"].decode("ascii").strip()
            except UnicodeDecodeError as ex:
                raise InvalidFirmwareImageError(
                    "Firmware package version_number is not ASCII"
                ) from ex
            if not package_version:
                raise InvalidFirmwareImageError(
                    "Firmware package version_number is empty"
                )
            canonical_key = public_key.public_key().export_key(format="DER")
            signer_fingerprint = hashlib.sha256(canonical_key).hexdigest()
            archive_format = "signed"
            signature_valid = True
        elif _REQUIRED_FLAT_FILES.issubset(outer):
            cls._validate_uboot_image(outer["initramfs.bin.SD"])
            cls._validate_dtb(outer["am335x-boneblack-bitmainer.dtb"])
            package_version = None
            signer_fingerprint = None
            archive_format = "flat"
            signature_valid = False
        else:
            signed_missing = sorted(_REQUIRED_SIGNED_FILES.difference(outer))
            flat_missing = sorted(_REQUIRED_FLAT_FILES.difference(outer))
            raise InvalidFirmwareImageError(
                "Firmware package does not match a supported layout; "
                + f"signed layout missing: {', '.join(signed_missing)}; "
                + f"flat layout missing: {', '.join(flat_missing)}"
            )

        miner_model, build_date, variant = cls._parse_filename(filename)
        metadata = BitmainLegacyMetadata(
            filename=filename,
            miner_model=miner_model,
            build_date=build_date,
            variant=variant,
            package_version=package_version,
            signer_fingerprint=signer_fingerprint,
            archive_format=archive_format,
            signature_valid=signature_valid,
        )
        return cls(data=data, source=source, metadata=metadata)

    @classmethod
    def _read_archive(
        cls,
        data: bytes,
        *,
        archive_name: str,
        max_members: int,
    ) -> dict[str, bytes]:
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
                members = archive.getmembers()
                if len(members) > max_members:
                    raise InvalidFirmwareImageError(
                        f"{archive_name.capitalize()} contains too many members"
                    )

                files: dict[str, bytes] = {}
                expanded_size = 0
                for member in members:
                    name = cls._safe_member_name(member.name, archive_name)
                    if name in files:
                        raise InvalidFirmwareImageError(
                            f"{archive_name.capitalize()} contains duplicate member "
                            + repr(name)
                        )
                    if member.isdir():
                        continue
                    if not member.isfile():
                        raise InvalidFirmwareImageError(
                            f"{archive_name.capitalize()} contains unsupported member "
                            + repr(name)
                        )
                    if member.size < 0 or member.size > _MAX_MEMBER_SIZE:
                        raise InvalidFirmwareImageError(
                            f"{archive_name.capitalize()} member {name!r} "
                            + "has an invalid size"
                        )
                    expanded_size += member.size
                    if expanded_size > _MAX_EXPANDED_SIZE:
                        raise InvalidFirmwareImageError(
                            f"{archive_name.capitalize()} expands beyond the size limit"
                        )
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        raise InvalidFirmwareImageError(
                            f"Failed to read {archive_name} member {name!r}"
                        )
                    content = extracted.read()
                    if len(content) != member.size:
                        raise InvalidFirmwareImageError(
                            f"{archive_name.capitalize()} member {name!r} is truncated"
                        )
                    files[name] = content
                return files
        except InvalidFirmwareImageError:
            raise
        except (tarfile.TarError, EOFError, OSError) as ex:
            raise InvalidFirmwareImageError(f"Invalid {archive_name}: {ex}") from ex

    @staticmethod
    def _safe_member_name(name: str, archive_name: str) -> str:
        if "\\" in name:
            raise InvalidFirmwareImageError(
                f"{archive_name.capitalize()} contains unsafe member {name!r}"
            )
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise InvalidFirmwareImageError(
                f"{archive_name.capitalize()} contains unsafe member {name!r}"
            )
        normalized = PurePosixPath(*(part for part in path.parts if part != "."))
        if not normalized.parts:
            raise InvalidFirmwareImageError(
                f"{archive_name.capitalize()} contains an empty member name"
            )
        return normalized.as_posix()

    @staticmethod
    def _load_public_key(data: bytes) -> RSA.RsaKey:
        try:
            key = RSA.import_key(data)
        except (ValueError, IndexError, TypeError) as ex:
            raise InvalidFirmwareImageError(
                "Firmware package contains an invalid signing key"
            ) from ex
        if key.has_private():
            raise InvalidFirmwareImageError(
                "Firmware package unexpectedly contains a private signing key"
            )
        return key

    @staticmethod
    def _verify_signature(
        public_key: RSA.RsaKey, payload: bytes, signature: bytes
    ) -> None:
        try:
            pkcs1_15.new(public_key).verify(SHA256.new(payload), signature)
        except (ValueError, TypeError) as ex:
            raise FirmwareSignatureError(
                "Legacy Bitmain firmware payload signature is invalid"
            ) from ex

    @staticmethod
    def _validate_uboot_image(data: bytes) -> None:
        if len(data) < _UBOOT_HEADER_SIZE:
            raise InvalidFirmwareImageError("U-Boot initramfs image is truncated")

        values = cast(
            tuple[int, int, int, int, int, int, int, int, int, int, int, bytes],
            _UBOOT_HEADER_STRUCT.unpack_from(data),
        )
        magic = values[0]
        header_crc = values[1]
        data_size = values[3]
        data_crc = values[6]
        if magic != _UBOOT_MAGIC:
            raise InvalidFirmwareImageError(
                f"Invalid U-Boot initramfs magic: 0x{magic:08x}"
            )
        if len(data) != _UBOOT_HEADER_SIZE + data_size:
            raise InvalidFirmwareImageError(
                "U-Boot initramfs payload size does not match its header"
            )

        header = bytearray(data[:_UBOOT_HEADER_SIZE])
        header[4:8] = b"\x00\x00\x00\x00"
        calculated_header_crc = zlib.crc32(header)
        if calculated_header_crc != header_crc:
            raise InvalidFirmwareImageError(
                "Invalid U-Boot initramfs header checksum: "
                + f"expected 0x{header_crc:08x}, "
                + f"calculated 0x{calculated_header_crc:08x}"
            )

        calculated_data_crc = zlib.crc32(data[_UBOOT_HEADER_SIZE:])
        if calculated_data_crc != data_crc:
            raise InvalidFirmwareImageError(
                "Invalid U-Boot initramfs data checksum: "
                + f"expected 0x{data_crc:08x}, "
                + f"calculated 0x{calculated_data_crc:08x}"
            )

    @staticmethod
    def _validate_dtb(data: bytes) -> None:
        if len(data) < _DTB_HEADER_STRUCT.size:
            raise InvalidFirmwareImageError("Device tree blob is truncated")

        values = cast(
            tuple[int, int, int, int, int, int, int, int, int, int],
            _DTB_HEADER_STRUCT.unpack_from(data),
        )
        magic = values[0]
        total_size = values[1]
        struct_offset = values[2]
        strings_offset = values[3]
        reserve_offset = values[4]
        strings_size = values[8]
        struct_size = values[9]
        if magic != _DTB_MAGIC:
            raise InvalidFirmwareImageError(f"Invalid device tree magic: 0x{magic:08x}")
        if total_size != len(data):
            raise InvalidFirmwareImageError(
                "Device tree size does not match its header"
            )
        if any(
            offset < _DTB_HEADER_STRUCT.size or offset >= total_size
            for offset in (struct_offset, strings_offset, reserve_offset)
        ):
            raise InvalidFirmwareImageError(
                "Device tree contains an invalid section offset"
            )
        if struct_offset + struct_size > total_size:
            raise InvalidFirmwareImageError(
                "Device tree structure section exceeds the image"
            )
        if strings_offset + strings_size > total_size:
            raise InvalidFirmwareImageError(
                "Device tree strings section exceeds the image"
            )

    @staticmethod
    def _parse_filename(filename: str) -> tuple[str | None, str | None, str | None]:
        for pattern in _FILENAME_PATTERNS:
            if match := pattern.fullmatch(filename):
                model = match.group("model")
                return (
                    f"Antminer {model}",
                    match.group("build_date"),
                    match.groupdict().get("variant"),
                )
        return None, None, None

    def payload_for(
        self, miner_model: str, *, enforce_compatibility: bool = True
    ) -> bytes:
        declared_model = self._metadata.miner_model
        if enforce_compatibility and declared_model is None:
            raise IncompatibleFirmwareError(
                "Unrecognized legacy Bitmain firmware filename: "
                + f"{self._metadata.filename!r}"
            )
        if enforce_compatibility and declared_model != miner_model:
            raise IncompatibleFirmwareError(
                f"Firmware for {declared_model!r} is incompatible with {miner_model!r}"
            )
        return self._data
