import sys
import argparse
from scapy.all import send, IP, UDP, Raw


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--dport",
        action="store",
        type=int,
        required=True,
        help="dst port for UDP packet.",
    )
    parser.add_argument(
        "-s",
        "--src",
        action="store",
        type=str,
        default="127.0.0.1",
        help="src address for UDP packet.",
    )
    parser.add_argument(
        "-m",
        "--msg",
        action="store",
        type=str,
        help="optional data to attach to the UDP datagram.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    p = (
        IP(src=args.src, dst="127.0.0.1")
        / UDP(sport=0, dport=args.dport)
        / Raw(load=args.msg)
    )
    if p:
        print(p.show())
        send(p)

    sys.exit(0)
