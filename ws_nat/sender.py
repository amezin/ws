import argparse
import asyncio

from . import client


class Sender(client.Client):
    def __init__(self, intermediate_server_url):
        super().__init__(registration_url=intermediate_server_url / 'sender/register',
                         peers_url=intermediate_server_url / 'receiver')
        self.data = asyncio.Queue()

    async def main(self, ws_connection):
        message = await self.data.get()
        try:
            await ws_connection.send_str(message)
        except Exception:
            self.data.put_nowait(message)
            raise


def run():
    parser = argparse.ArgumentParser(description="Send a message")
    parser.add_argument('message', help="Message to send")
    args = client.parse_command_line(parser)

    sender = Sender(args.intermediate_server)
    sender.data.put_nowait(args.message)
    asyncio.get_event_loop().run_until_complete(sender.run_client_server())


if __name__ == '__main__':
    run()
