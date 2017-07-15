import asyncio
import logging

import aiohttp.web
import yarl

from . import util


LOG = logging.getLogger(__name__)


class Client:
    def __init__(self, registration_url, peers_url):
        self.done = asyncio.Event()
        self.registration_url = registration_url
        self.peers_url = peers_url

    async def main(self, ws_connection):
        pass

    async def handle_server_connection(self, request):
        logger = util.RequestLogger(LOG, request)
        logger.info("Client connected")

        # Workaround for https://github.com/aio-libs/aiohttp/issues/2024
        class DummyApp:
            def __init__(self):
                self.loop = asyncio.get_event_loop()

        request.app = DummyApp()
        # End workaround

        ws_connection = aiohttp.web.WebSocketResponse(**util.WEBSOCKET_TIMEOUTS)
        await ws_connection.prepare(request)

        logger.info("Websocket connection established")

        try:
            await self.main(ws_connection)

            logger.info("Completed successfully")
            self.done.set()

        finally:
            await ws_connection.close()
            logger.info("Websocket connection closed")

        return ws_connection

    async def run_server(self):
        ws_server = aiohttp.web.Server(self.handle_server_connection)
        sock_server = await asyncio.get_event_loop().create_server(ws_server, port=0)

        endpoints = [sock.getsockname() for sock in sock_server.sockets]
        LOG.info("Listening at %s", endpoints)

        try:
            with aiohttp.ClientSession(raise_for_status=True, **util.HTTP_SESSION_TIMEOUTS) as session:
                LOG.info("Connecting to %s", self.registration_url)

                async with session.ws_connect(self.registration_url, **util.WEBSOCKET_TIMEOUTS) as registration_connection:
                    LOG.info("Connected to %s", self.registration_url)
                    await registration_connection.send_json(endpoints)
                    LOG.info("Registered")

                    while not registration_connection.closed:
                        msg = await registration_connection.receive()
                        LOG.info("Received %s", msg)

        finally:
            LOG.info("Stopping server")

            sock_server.close()
            await sock_server.wait_closed()
            await ws_server.shutdown()

    async def run_client(self):
        with aiohttp.ClientSession(raise_for_status=True, **util.HTTP_SESSION_TIMEOUTS) as session:
            while True:
                try:
                    LOG.info("Getting peers from %s", self.peers_url)
                    async with session.get(self.peers_url) as peer_response:
                        peer = await peer_response.json()
                        LOG.info("Got peer %s", peer)

                except asyncio.TimeoutError:
                    LOG.warning("Waiting for peers: timed out")
                    continue

                peer_host = peer['host']
                for peer_sockname in peer['ports']:
                    peer_url = "ws://{}:{}/".format(peer_host, peer_sockname[1])
                    LOG.info("Trying %s", peer_url)

                    try:
                        async with session.ws_connect(peer_url, **util.WEBSOCKET_TIMEOUTS) as ws_connection:
                            LOG.info("Connected to %s", peer_url)
                            await self.main(ws_connection)
                            LOG.info("Done")
                            self.done.set()
                            return

                    except (aiohttp.ClientError, asyncio.TimeoutError) as ex:
                        LOG.warning("Can't connect to %s: %s", peer_url, ex)

                await asyncio.sleep(1)

    async def run_client_and_server(self):
        tasks = [
            asyncio.ensure_future(self.run_server()),
            asyncio.ensure_future(self.run_client())
        ]

        try:
            await self.done.wait()

        finally:
            for task in tasks:
                task.cancel()

            for task in tasks:
                if not task.done():
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass


def parse_command_line(parser):
    parser.add_argument('-v', '--verbose', action='count', default=0, help="More verbose logging")
    parser.add_argument('--intermediate-server', type=yarl.URL, default=yarl.URL('ws://localhost:8000/'),
                        help="Intermediate server URL (default: %(default)s)")

    args = parser.parse_args()
    util.setup_logging(args.verbose)

    return args
