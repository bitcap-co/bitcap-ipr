# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import argparse
import binascii
import zlib
from pathlib import Path


def parse_arguments():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", action="store", type=str)
    group.add_argument("-m", "--msg", action="store", type=str)
    parser.add_argument("-l", "--level", action="store", type=int, default=-1)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    data = bytes()
    if args.file:
        with open(Path(args.file).resolve(), "rb") as f:
            data = f.read()

    if args.msg:
        data = bytes(args.msg, "utf-8")

    compressed = zlib.compress(data, level=args.level)
    print(binascii.hexlify(compressed).decode("utf-8"))
