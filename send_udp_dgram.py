import argparse
import socket
import sys
import time

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', action='store', type=int, required=True)
    parser.add_argument('-m', '--msg', action='store', type=str, required=True)
    parser.add_argument('-r', '--repeat', action='store', type=int)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if (args.repeat):
        for _ in range(args.repeat):
            sock.sendto(bytes(args.msg, 'utf-8'), ("127.0.0.1", args.port))
            time.sleep(2)
        sys.exit(0)
    sock.sendto(bytes(args.msg, 'utf-8'), ("127.0.0.1", args.port))
