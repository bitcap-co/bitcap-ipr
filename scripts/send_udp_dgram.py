import argparse
import socket
import sys
import time


def parse_arguments():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="switch for sending UDP datagram over localhost",
    )
    group.add_argument(
        "-b",
        "--broadcast",
        action="store_true",
        help="switch for sending UDP datagram to broadcast",
    )
    parser.add_argument(
        "-p",
        "--port",
        action="store",
        type=int,
        required=True,
        help="destination port for UDP datagram",
    )
    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument(
        "-m",
        "--msg",
        action="store",
        type=str,
        help="custom string to send as data payload",
    )
    group2.add_argument(
        "-s",
        "--hex",
        action="store",
        type=str,
        help="custom hex string to send as data payload",
    )
    parser.add_argument(
        "-r",
        "--repeat",
        action="store",
        type=int,
        help="repeat datagram sending n times",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if args.local:
        ip_addr = "127.0.0.1"
    elif args.broadcast:
        ip_addr = "255.255.255.255"
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    if args.hex:
        sock.sendto(bytes.fromhex(args.hex), (ip_addr, args.port))
    else:
        sock.sendto(bytes(args.msg, "utf-8"), (ip_addr, args.port))

    if args.repeat:
        for _ in range(args.repeat):
            time.sleep(2)
            sock.sendto(bytes(args.msg, "utf-8"), (ip_addr, args.port))

    sock.close()
    sys.exit(0)
