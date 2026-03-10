#!/usr/bin/env python3
## pcap_dump -- read and display packet info from .pcap/.pcapng files

import argparse
import datetime
import zlib

from scapy.all import ICMP, IP, TCP, UDP, Ether, IPv6, Raw, rdpcap


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    # packet header
    HEADER = "\033[1;97m"  # bold white
    TS = "\033[0;90m"  # dark gray
    # layer name colors
    ETHER = "\033[0;33m"  # yellow
    IPV4 = "\033[0;36m"  # cyan
    IPV6 = "\033[0;96m"  # bright cyan
    UDP = "\033[0;32m"  # green
    TCP = "\033[0;34m"  # blue
    ICMP = "\033[0;35m"  # magenta
    DATA = "\033[0;37m"  # light gray
    # misc
    KEY = "\033[0;90m"  # dark gray for field keys
    VAL = "\033[0;97m"  # bright white for field values
    ZLIB = "\033[0;93m"  # yellow for zlib info
    DECODED = "\033[0;92m"  # green for decoded text
    OFFSET = "\033[0;90m"  # dark gray for hex offsets
    HEX = "\033[0;97m"  # bright white for hex bytes
    ASCII = "\033[0;32m"  # green for ascii column
    SEP = "\033[0;90m"  # dark gray for separators


def parse_args():
    parser = argparse.ArgumentParser(
        description="Dump packet info from a pcap/pcapng file."
    )
    parser.add_argument("file", help="Path to the .pcap or .pcapng file.")
    parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=None,
        help="Max number of packets to display (default: all).",
    )
    parser.add_argument(
        "--filter",
        "-f",
        type=str,
        default=None,
        help="Only show packets containing this protocol (e.g. UDP, TCP, ICMP).",
    )
    parser.add_argument(
        "--dst-ip",
        type=str,
        default=None,
        help="Only show packets with this destination IP.",
    )
    parser.add_argument(
        "--src-ip",
        type=str,
        default=None,
        help="Only show packets with this source IP.",
    )
    parser.add_argument(
        "--dport",
        type=int,
        default=None,
        help="Only show packets with this destination port.",
    )
    parser.add_argument(
        "--sport",
        type=int,
        default=None,
        help="Only show packets with this source port.",
    )
    parser.add_argument(
        "--no-hexdump",
        action="store_true",
        help="Skip the hex dump of packet data.",
    )
    return parser.parse_args()


LAYER_COLORS = {
    Ether: (C.ETHER, "Ethernet"),
    IP: (C.IPV4, "IPv4"),
    IPv6: (C.IPV6, "IPv6"),
    UDP: (C.UDP, "UDP"),
    TCP: (C.TCP, "TCP"),
    ICMP: (C.ICMP, "ICMP"),
    Raw: (C.DATA, "Data"),
}


def describe_layer(layer):
    color, name = LAYER_COLORS.get(type(layer), (C.DATA, type(layer).__name__))
    fields = {}

    if isinstance(layer, Ether):
        fields = {"src": layer.src, "dst": layer.dst, "type": hex(layer.type)}
    elif isinstance(layer, IP):
        fields = {
            "src": layer.src,
            "dst": layer.dst,
            "proto": layer.proto,
            "ttl": layer.ttl,
        }
    elif isinstance(layer, IPv6):
        fields = {"src": layer.src, "dst": layer.dst, "nh": layer.nh}
    elif isinstance(layer, UDP):
        fields = {"sport": layer.sport, "dport": layer.dport, "len": layer.len}
    elif isinstance(layer, TCP):
        fields = {
            "sport": layer.sport,
            "dport": layer.dport,
            "flags": str(layer.flags),
            "seq": layer.seq,
        }
    elif isinstance(layer, ICMP):
        fields = {"type": layer.type, "code": layer.code}
    elif isinstance(layer, Raw):
        fields = {"length": len(layer.load)}

    field_str = "  ".join(
        f"{C.KEY}{k}{C.RESET}={C.VAL}{v}{C.RESET}" for k, v in fields.items()
    )
    colored_name = f"{color}[{name}]{C.RESET}"
    return colored_name, field_str


def hex_dump(data, width=16):
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(
            f"  {C.OFFSET}{i:04x}{C.RESET}  "
            f"{C.HEX}{hex_part:<{width * 3}}{C.RESET}  "
            f"{C.ASCII}{ascii_part}{C.RESET}"
        )
    return "\n".join(lines)


def main():
    args = parse_args()

    try:
        packets = rdpcap(args.file)
    except FileNotFoundError:
        print(f"Error: file not found — {args.file}")
        raise SystemExit(1)
    except Exception as e:
        print(f"Error reading pcap: {e}")
        raise SystemExit(1)

    filter_proto = args.filter.upper() if args.filter else None
    proto_map = {
        "UDP": UDP,
        "TCP": TCP,
        "ICMP": ICMP,
        "IP": IP,
        "IPV6": IPv6,
        "ETHER": Ether,
    }

    displayed = 0
    for idx, pkt in enumerate(packets):
        if args.count is not None and displayed >= args.count:
            break

        if filter_proto:
            proto_cls = proto_map.get(filter_proto)
            if proto_cls is None:
                print(
                    f"Unknown protocol filter '{args.filter}'. Valid options: {', '.join(proto_map)}"
                )
                raise SystemExit(1)
            if not pkt.haslayer(proto_cls):
                continue

        if args.dst_ip and not (pkt.haslayer(IP) and pkt[IP].dst == args.dst_ip):
            continue
        if args.src_ip and not (pkt.haslayer(IP) and pkt[IP].src == args.src_ip):
            continue
        if args.dport:
            if not (
                (pkt.haslayer(UDP) and pkt[UDP].dport == args.dport)
                or (pkt.haslayer(TCP) and pkt[TCP].dport == args.dport)
            ):
                continue
        if args.sport:
            if not (
                (pkt.haslayer(UDP) and pkt[UDP].sport == args.sport)
                or (pkt.haslayer(TCP) and pkt[TCP].sport == args.sport)
            ):
                continue

        displayed += 1
        ts = datetime.datetime.fromtimestamp(float(pkt.time)).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        sep = f"{C.SEP}{'=' * 60}{C.RESET}"
        print(sep)
        print(
            f"{C.HEADER}Packet #{idx + 1}{C.RESET}  "
            f"{C.DIM}({len(pkt)} bytes){C.RESET}  "
            f"{C.TS}{ts}{C.RESET}"
        )
        print(sep)

        layer = pkt
        while layer:
            name, fields = describe_layer(layer)
            print(f"  {name}  {fields}")
            layer = layer.payload if layer.payload else None

        if pkt.haslayer(Raw):
            payload = pkt[Raw].load
            decompressed = None
            zlib_offset = -1
            for i in range(0, min(20, len(payload) - 1)):
                if payload[i] == 0x78 and payload[i + 1] in (0x01, 0x9C, 0xDA, 0x5E):
                    try:
                        decompressed = zlib.decompress(payload[i:])
                        zlib_offset = i
                        break
                    except zlib.error:
                        continue
            if decompressed is not None:
                print(
                    f"\n  {C.ZLIB}Payload (zlib at offset {zlib_offset}, "
                    f"decompressed {len(payload) - zlib_offset} -> {len(decompressed)} bytes):{C.RESET}"
                )
                if zlib_offset > 0:
                    print(f"  {C.DIM}Prefix ({zlib_offset} bytes):{C.RESET}")
                    print(hex_dump(payload[:zlib_offset]))
                print(f"  {C.ZLIB}Decompressed:{C.RESET}")
                print(hex_dump(decompressed))
                try:
                    print(
                        f"\n  {C.DECODED}Decoded: {decompressed.decode('utf-8')}{C.RESET}"
                    )
                except UnicodeDecodeError:
                    pass
            else:
                print(f"\n  {C.DIM}Payload ({len(payload)} bytes):{C.RESET}")
                print(hex_dump(payload))
                try:
                    print(f"\n  {C.DECODED}Decoded: {payload.decode('utf-8')}{C.RESET}")
                except UnicodeDecodeError:
                    pass

        if not args.no_hexdump:
            raw_bytes = bytes(pkt)
            print(f"\n  {C.DIM}Full packet hex dump ({len(raw_bytes)} bytes):{C.RESET}")
            print(hex_dump(raw_bytes))

        print()

    print(f"{C.DIM}Displayed {displayed} of {len(packets)} packet(s).{C.RESET}")


if __name__ == "__main__":
    main()
