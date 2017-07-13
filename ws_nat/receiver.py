import argparse
import asyncio

from . import client


class Receiver(client.Client):
    def __init__(self, intermediate_server_url, output=print):
        super().__init__(registration_url=intermediate_server_url / 'receiver/register',
                         peers_url=intermediate_server_url / 'sender')
        self.output = output

    async def main(self, ws_connection):
        msg = await ws_connection.receive_str()
        self.output(msg)


def run():
    args = client.parse_command_line(argparse.ArgumentParser(description="Receive a message and print it to stdout"))
    asyncio.get_event_loop().run_until_complete(Receiver(args.intermediate_server).run_client_server())


if __name__ == '__main__':
    run()
