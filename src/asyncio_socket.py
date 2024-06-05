import asyncio
import socket


class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_con_lost):
        super().__init__()
        self.transport = None
        self.on_con_lost = on_con_lost
        self.output = None

    def connection_made(self, transport) -> "Used by asyncio":
        self.transport = transport

    def datagram_received(self, data, addr) -> "Main entrypoint for processing message":
        # Here is where you would push message to whatever methods/classes you want.
        print(f"Received Syslog message: {data}")
        self.output = data
        self.transport.close()

    def connection_lost(self, exc):
        print('connection closed')
        self.on_con_lost.set_result(True)


async def main():
    loop = asyncio.get_event_loop()

    on_con_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: SyslogProtocol(on_con_lost),
        local_addr=('0.0.0.0', 14235))

    try:
        await on_con_lost
    finally:
        transport.close()
        print(protocol.output)

asyncio.run(main())
