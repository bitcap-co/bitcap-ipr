# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


class FirmwareImageError(ValueError):
    """Base error raised while loading or selecting a firmware image."""


class InvalidFirmwareImageError(FirmwareImageError):
    """Raised when a recognized firmware image is structurally invalid."""


class FirmwareChecksumError(InvalidFirmwareImageError):
    """Raised when a firmware container fails checksum validation."""


class IncompatibleFirmwareError(FirmwareImageError):
    """Raised when an image has no payload compatible with a miner."""
