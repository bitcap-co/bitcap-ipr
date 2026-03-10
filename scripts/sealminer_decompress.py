import argparse
import json
import sys
import zlib
from pathlib import Path

ZLIB_DEFAULT_MAGIC = b"\x78\x9c"


def parse_arguments():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", action="store", type=str)
    group.add_argument("-m", "--msg", action="store", type=str)
    parser.add_argument("-r", "--raw", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    data = bytes()
    if args.file:
        with open(Path(args.file).resolve(), "rb") as f:
            data = f.read()

    if args.msg:
        data = bytes.fromhex(args.msg)

    if ZLIB_DEFAULT_MAGIC in data:
        data_start = data.index(ZLIB_DEFAULT_MAGIC)
        print(data_start)
        data = data[data_start:]
        try:
            out = zlib.decompress(data)
        except zlib.error as err:
            print(err)
        else:
            if args.raw:
                print(out)
                sys.exit(0)
            out = out.replace(b"\x00", b"")
            out = out.replace(b"}{", b"}, {")
            out = b"[" + out + b"]"
            try:
                obj = json.loads(out)
            except json.JSONDecodeError as err:
                print(f"Failed to decode to JSON: {err}")
                sys.exit(1)
            else:
                print(obj)
    sys.exit(0)
