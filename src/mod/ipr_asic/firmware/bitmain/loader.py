# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pathlib import Path

from ..errors import InvalidFirmwareImageError
from .bmu import BitmainFirmwareImage
from .legacy import BitmainLegacyFirmwareImage

BitmainFirmware = BitmainFirmwareImage | BitmainLegacyFirmwareImage


def load_bitmain_firmware(path: Path) -> BitmainFirmware:
    """Load a Bitmain firmware image based on its package extension."""
    filename = path.name.lower()
    if filename.endswith(".tar.gz"):
        return BitmainLegacyFirmwareImage.from_path(path)
    if path.suffix.lower() in {".bmu"}:
        return BitmainFirmwareImage.from_path(path)
    raise InvalidFirmwareImageError(
        f"Unsupported Bitmain firmware file type: {path.name!r}"
    )
