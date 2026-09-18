#!/usr/bin/env python3
# pyright: reportMissingImports=false
# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Inspect and validate Bitmain BMU firmware images without uploading them."""

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mod.ipr_asic.firmware import (
    BitmainFirmwareImage,
    FirmwareImageError,
)


def firmware_paths(inputs: Iterable[Path]) -> list[Path]:
    paths: set[Path] = set()
    for input_path in inputs:
        path = input_path.expanduser().resolve()
        if path.is_file():
            if path.suffix.lower() == ".bmu":
                paths.add(path)
            continue
        if path.is_dir():
            paths.update(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() == ".bmu"
            )
    return sorted(paths)


def inspect_image(
    path: Path,
    miner_model: str | None,
    control_board_model: str | None,
) -> bool:
    print(f"\n{path}")
    try:
        image = BitmainFirmwareImage.from_path(path)
    except FirmwareImageError as ex:
        print(f"  INVALID: {ex}")
        return False

    size = path.stat().st_size
    print(f"  Size: {size:,} bytes ({size / 1024 / 1024:.2f} MiB)")
    if not image.is_container:
        print("  Format: opaque single-image BMU (no container metadata)")
    else:
        header = image.header
        assert header is not None
        print("  Format: multi-image BMU container")
        header_summary = (
            f"magic=0x{header.magic:08x}, version=0x{header.version:x}, "
            + f"items={header.item_count}, item_size={header.item_size}, "
            + f"data_offset={header.data_offset}, crc32=0x{header.crc32:08x}"
        )
        print(f"  Header: {header_summary}")
        for index, item in enumerate(image.items, 1):
            item_summary = (
                f"name={item.name!r}, miner={item.miner_model!r}, "
                + f"control={item.control_board_model!r}, chip={item.chip_model!r}, "
                + f"offset={item.data_offset}, size={item.data_size:,}"
            )
            print(f"  [{index}] {item_summary}")

    if miner_model is not None and control_board_model is not None:
        try:
            payload = image.payload_for(miner_model, control_board_model)
        except FirmwareImageError as ex:
            print(f"  INCOMPATIBLE: {ex}")
            return False
        item_name = payload.item.name if payload.item is not None else "raw image"
        print(f"  Compatible payload: {item_name!r}, {len(payload.data):,} bytes")

    print("  VALID")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        type=Path,
        nargs="+",
        help="BMU file or directory to scan recursively",
    )
    parser.add_argument(
        "--miner-model",
        help="Require a payload matching this exact miner model",
    )
    parser.add_argument(
        "--control-board-model",
        help="Require a payload matching this exact control-board model",
    )
    args = parser.parse_args()
    if (args.miner_model is None) != (args.control_board_model is None):
        parser.error(
            "--miner-model and --control-board-model must be provided together"
        )
    return args


def main() -> int:
    args = parse_args()
    paths = firmware_paths(args.paths)
    if not paths:
        print("No .bmu firmware images found.", file=sys.stderr)
        return 2

    valid = sum(
        inspect_image(path, args.miner_model, args.control_board_model)
        for path in paths
    )
    invalid = len(paths) - valid
    print(f"\nSummary: {valid} valid, {invalid} invalid, {len(paths)} total")
    return 0 if invalid == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
