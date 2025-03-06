import argparse
import socket
import sys
import time


def parse_arguments():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--local", action="store_true")
    group.add_argument("-b", "--broadcast", action="store_true")
    parser.add_argument("-p", "--port", action="store", type=int, required=True)
    parser.add_argument("-m", "--msg", action="store", type=str, required=True)
    parser.add_argument("-r", "--repeat", action="store", type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if args.local:
        ip_addr = "127.0.0.1"
    elif args.broadcast:
        ip_addr = "255.255.255.255"
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.sendto(bytes(args.msg, "utf-8"), (ip_addr, args.port))

    if args.repeat:
        for _ in range(args.repeat):
            time.sleep(2)
            sock.sendto(bytes(args.msg, "utf-8"), (ip_addr, args.port))

    sock.close()
    sys.exit(0)
