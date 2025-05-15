import zlib
import binascii
import argparse
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

    if args.file:
        with open(Path(args.file), 'rb') as f:
            data = f.read()

    if args.msg:
        data = bytes(args.msg, "utf-8")

    compressed = zlib.compress(data, level=args.level)

    print(binascii.hexlify(compressed).decode('utf-8'))
