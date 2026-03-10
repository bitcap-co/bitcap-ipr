#!/usr/bin/env python3
## send_raw_udp -- send raw UDP packets with spoofable source IP using scapy

import argparse
import time

from scapy.all import IP, UDP, Raw, send


def parse_args():
    parser = argparse.ArgumentParser(description="Send a raw UDP packet via scapy.")
    parser.add_argument("message", help="The message payload to send.")
    parser.add_argument(
        "--src",
        "-s",
        type=str,
        default="127.0.0.1",
        help="Source IP address (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--dst",
        "-d",
        type=str,
        default="255.255.255.255",
        help="Destination IP address (default: 255.255.255.255).",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        required=True,
        help="Destination UDP port.",
    )
    parser.add_argument(
        "--sport",
        type=int,
        default=0,
        help="Source UDP port (default: 0).",
    )
    parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=1,
        help="Number of times to send the packet (default: 1).",
    )
    parser.add_argument(
        "--hex",
        "-x",
        action="store_true",
        help="Treat message as a hex string.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.hex:
        try:
            payload = bytes.fromhex(args.message)
        except ValueError as e:
            print(f"Error: invalid hex string — {e}")
            raise SystemExit(1)
    else:
        payload = args.message.encode("utf-8")

    packet = (
        IP(src=args.src, dst=args.dst)
        / UDP(sport=args.sport, dport=args.port)
        / Raw(load=payload)
    )

    packet.show()

    try:
        for i in range(args.count):
            send(packet, verbose=False)
            print(
                f"[{i + 1}/{args.count}] Sent {len(payload)} byte(s) to {args.dst}:{args.port}"
            )
            if i < args.count - 1:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nCancelled.")


if __name__ == "__main__":
    main()
