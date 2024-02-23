import argparse
import socket


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', action='store', type=int, required=True)
    parser.add_argument('-m', '--msg', action='store', type=str, required=True)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(args.msg, 'utf-8'), ("127.0.0.1", args.port))
