import argparse
import asyncio
import functools
import logging
import random

import aiohttp.web

from . import util


LOG = logging.getLogger(__name__)


class PeerSet(object):
    def __init__(self):
        self.connected = []
        self.available = asyncio.Event()

    async def register(self, request):
        ws_connection = aiohttp.web.WebSocketResponse(**util.WEBSOCKET_TIMEOUTS)
        await ws_connection.prepare(request)

        peername = request.transport.get_extra_info('peername')

        logger = util.RequestLogger(LOG, request)
        logger.info("Client connected")

        try:
            ports = await ws_connection.receive_json()
            logger.info("Received ports: %s", ports)

            endpoints = {'host': peername[0], 'ports': ports}
            self.connected.append(endpoints)
            self.available.set()

            logger.info("Added %s", endpoints)

            try:
                while not ws_connection.closed:
                    msg = await ws_connection.receive()
                    logger.info("Received %s", msg)

            finally:
                self.connected.remove(endpoints)
                if not self.connected:
                    self.available.clear()

                logger.info("Removed %s", endpoints)

        finally:
            await ws_connection.close()
            logger.info("Connection closed")

        return ws_connection

    async def get(self, request):
        logger = util.RequestLogger(LOG, request)
        logger.info("Peer requested")

        await self.available.wait()
        peer = random.choice(self.connected)
        logger.info("Got peer %s", peer)

        return aiohttp.web.json_response(peer)


class IntermediateServerApp(aiohttp.web.Application):
    def __init__(self):
        super().__init__()

        self.senders = PeerSet()
        self.receivers = PeerSet()

        self.router.add_get('/sender/register', self.senders.register)
        self.router.add_get('/sender', self.senders.get)

        self.router.add_get('/receiver/register', self.receivers.register)
        self.router.add_get('/receiver', self.receivers.get)


def run():
    parser = argparse.ArgumentParser(description="Intermediate server")
    parser.add_argument('-v', '--verbose', action='count', default=0, help="More verbose logging")
    parser.add_argument('--host', default=None, help="TCP/IP interface to serve on (default: %(default)r)")
    parser.add_argument('--port', default=8000, help="TCP/IP port to serve on (default: %(default)r)")

    args = parser.parse_args()
    util.setup_logging(args.verbose)
    aiohttp.web.run_app(IntermediateServerApp(), host=args.host, port=args.port)


if __name__ == '__main__':
    run()
