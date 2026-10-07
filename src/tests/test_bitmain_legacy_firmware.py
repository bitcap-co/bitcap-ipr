# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import io
import struct
import tarfile
import unittest
import zlib
from collections.abc import Mapping
from typing import ClassVar

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from mod.ipr_asic.firmware import (
    BitmainLegacyFirmwareImage,
    FirmwareSignatureError,
    IncompatibleFirmwareError,
    InvalidFirmwareImageError,
)


def _tar_gzip(files: Mapping[str, bytes]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, data in files.items():
            member = tarfile.TarInfo(name=name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return output.getvalue()


def _uboot_image(payload: bytes) -> bytes:
    data_crc = zlib.crc32(payload)
    values = (
        0x27051956,
        0,
        0,
        len(payload),
        0,
        0,
        data_crc,
        5,
        2,
        3,
        1,
        b"test initramfs".ljust(32, b"\x00"),
    )
    header = bytearray(struct.pack(">7I4B32s", *values))
    struct.pack_into(">I", header, 4, zlib.crc32(header))
    return bytes(header) + payload


def _device_tree() -> bytes:
    total_size = 64
    header = struct.pack(
        ">10I",
        0xD00DFEED,
        total_size,
        48,
        56,
        40,
        17,
        16,
        0,
        8,
        8,
    )
    return header + bytes(total_size - len(header))


def _flat_legacy_package(*, initramfs: bytes | None = None) -> bytes:
    return _tar_gzip(
        {
            "runme.sh": b"#!/bin/sh\n",
            "initramfs.bin.SD": initramfs or _uboot_image(b"firmware payload"),
            "am335x-boneblack-bitmainer.dtb": _device_tree(),
        }
    )


def _legacy_package(
    key: RSA.RsaKey,
    *,
    inner: bytes | None = None,
    signed_inner: bytes | None = None,
    extra_files: Mapping[str, bytes] | None = None,
) -> bytes:
    if inner is None:
        inner = _tar_gzip(
            {
                "runme.sh": b"#!/bin/sh\n",
                "version": b"201907101440\n",
                "initramfs.bin.SD": b"firmware payload",
            }
        )
    if signed_inner is None:
        signed_inner = inner
    signature = pkcs1_15.new(key).sign(SHA256.new(signed_inner))
    files = {
        "cert.pem": key.public_key().export_key(),
        "cert.pem.sig": b"root signature unavailable",
        "fw.tar.gz": inner,
        "fw.tar.gz.sig": signature,
        "runme.sh": b"#!/bin/sh\n",
        "runme.sh.sig": b"root signature unavailable",
        "version_number": b"V1.0.41\n",
    }
    if extra_files:
        files.update(extra_files)
    return _tar_gzip(files)


class TestBitmainLegacyFirmwareImage(unittest.TestCase):
    key: ClassVar[RSA.RsaKey] = RSA.generate(1024)

    def test_validates_signed_l3_plus_package(self) -> None:
        data = _legacy_package(self.key)

        image = BitmainLegacyFirmwareImage.from_bytes(
            data,
            filename="Antminer-L3+-201907101440-384M.tar.gz",
        )

        self.assertEqual(image.metadata.miner_model, "Antminer L3+")
        self.assertEqual(image.metadata.build_date, "201907101440")
        self.assertEqual(image.metadata.variant, "384M")
        self.assertEqual(image.metadata.package_version, "V1.0.41")
        self.assertEqual(image.metadata.archive_format, "signed")
        self.assertTrue(image.metadata.signature_valid)
        self.assertEqual(image.payload_for("Antminer L3+"), data)

    def test_validates_unsigned_flat_l3_package(self) -> None:
        data = _flat_legacy_package()

        image = BitmainLegacyFirmwareImage.from_bytes(
            data,
            filename="Antminer-L3-201704271449-384M.tar.gz",
        )

        self.assertEqual(image.metadata.miner_model, "Antminer L3")
        self.assertEqual(image.metadata.build_date, "201704271449")
        self.assertEqual(image.metadata.variant, "384M")
        self.assertEqual(image.metadata.archive_format, "flat")
        self.assertFalse(image.metadata.signature_valid)
        self.assertIsNone(image.metadata.signer_fingerprint)
        self.assertIsNone(image.metadata.package_version)
        self.assertEqual(image.payload_for("Antminer L3"), data)

    def test_rejects_flat_package_with_invalid_uboot_crc(self) -> None:
        initramfs = bytearray(_uboot_image(b"firmware payload"))
        initramfs[-1] ^= 0xFF
        data = _flat_legacy_package(initramfs=bytes(initramfs))

        with self.assertRaisesRegex(InvalidFirmwareImageError, "data checksum"):
            _ = BitmainLegacyFirmwareImage.from_bytes(
                data,
                filename="Antminer-L3-201704271449-384M.tar.gz",
            )

    def test_keeps_l3_plus_and_l3_plus_plus_distinct(self) -> None:
        image = BitmainLegacyFirmwareImage.from_bytes(
            _legacy_package(self.key),
            filename="Antminer-L3++-201907151552-450M.tar.gz",
        )

        self.assertEqual(image.metadata.miner_model, "Antminer L3++")
        with self.assertRaises(IncompatibleFirmwareError):
            _ = image.payload_for("Antminer L3+")

    def test_parses_z15_filename(self) -> None:
        image = BitmainLegacyFirmwareImage.from_bytes(
            _legacy_package(self.key),
            filename="Antminer-Z15-user-800M-202007031139_6134.tar.gz",
        )

        self.assertEqual(image.metadata.miner_model, "Antminer Z15")
        self.assertEqual(image.metadata.build_date, "202007031139")
        self.assertEqual(image.metadata.variant, "6134")

    def test_rejects_tampered_inner_firmware(self) -> None:
        signed_inner = _tar_gzip({"version": b"original"})
        tampered_inner = _tar_gzip({"version": b"tampered"})
        data = _legacy_package(
            self.key,
            inner=tampered_inner,
            signed_inner=signed_inner,
        )

        with self.assertRaises(FirmwareSignatureError):
            _ = BitmainLegacyFirmwareImage.from_bytes(
                data,
                filename="Antminer-L3+-201907101440-384M.tar.gz",
            )

    def test_rejects_invalid_inner_archive_after_signature_verification(self) -> None:
        inner = b"not a tar archive"
        data = _legacy_package(self.key, inner=inner)

        with self.assertRaisesRegex(
            InvalidFirmwareImageError, "Invalid inner firmware archive"
        ):
            _ = BitmainLegacyFirmwareImage.from_bytes(
                data,
                filename="Antminer-L3+-201907101440-384M.tar.gz",
            )

    def test_rejects_unsafe_inner_archive_member(self) -> None:
        inner = _tar_gzip({"../escape": b"payload"})
        data = _legacy_package(self.key, inner=inner)

        with self.assertRaisesRegex(InvalidFirmwareImageError, "unsafe member"):
            _ = BitmainLegacyFirmwareImage.from_bytes(
                data,
                filename="Antminer-L3+-201907101440-384M.tar.gz",
            )

    def test_rejects_missing_required_outer_file(self) -> None:
        data = _tar_gzip({"version_number": b"V1"})

        with self.assertRaisesRegex(InvalidFirmwareImageError, "supported layout"):
            _ = BitmainLegacyFirmwareImage.from_bytes(
                data,
                filename="Antminer-L3+-201907101440-384M.tar.gz",
            )

    def test_unknown_filename_requires_override(self) -> None:
        data = _legacy_package(self.key)
        image = BitmainLegacyFirmwareImage.from_bytes(
            data,
            filename="renamed-firmware.tar.gz",
        )

        self.assertIsNone(image.metadata.miner_model)
        with self.assertRaises(IncompatibleFirmwareError):
            _ = image.payload_for("Antminer L3+")
        self.assertEqual(
            image.payload_for("Antminer L3+", enforce_compatibility=False),
            data,
        )

    def test_rejects_invalid_outer_archive(self) -> None:
        with self.assertRaises(InvalidFirmwareImageError):
            _ = BitmainLegacyFirmwareImage.from_bytes(
                b"not a tar archive",
                filename="Antminer-L3+-201907101440-384M.tar.gz",
            )


if __name__ == "__main__":
    _ = unittest.main()
