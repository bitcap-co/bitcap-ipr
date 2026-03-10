#!/usr/bin/env python3
## udp_send -- send custom UDP datagram messages

import argparse
import socket
import time


def parse_args():
    parser = argparse.ArgumentParser(description="Send a UDP datagram message.")
    parser.add_argument("message", help="The message payload to send.")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        required=True,
        help="Destination UDP port.",
    )

    parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=1,
        help="Number of times to send the message (default: 1).",
    )

    parser.add_argument(
        "--hex",
        "-x",
        action="store_true",
        help="Treat message as a hex string",
    )

    dest_group = parser.add_mutually_exclusive_group()
    dest_group.add_argument(
        "--broadcast",
        "-b",
        action="store_true",
        help="Send to broadcast address (255.255.255.255)",
    )
    dest_group.add_argument(
        "--host",
        "-H",
        default=None,
        help="Explicit destination host (overrides --broadcast and localhost default).",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.host:
        host = args.host
        is_broadcast = False
    elif args.broadcast:
        host = "255.255.255.255"
        is_broadcast = True
    else:
        host = "127.0.0.1"
        is_broadcast = False

    if args.hex:
        try:
            data = bytes.fromhex(args.message)
        except ValueError as e:
            print(f"Error: invalid hex string — {e}")
            raise SystemExit(1)
    else:
        data = args.message.encode("utf-8")

    def send_loop():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            if is_broadcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            for i in range(args.count):
                sock.sendto(data, (host, args.port))
                print(
                    f"[{i + 1}/{args.count}] Sent {len(data)} byte(s) to {host}:{args.port}"
                )
                if i < args.count - 1:
                    time.sleep(2)

    try:
        send_loop()
    except KeyboardInterrupt:
        print("\nCancelled send.")


if __name__ == "__main__":
    main()
