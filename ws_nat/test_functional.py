import asyncio

from . import receiver, sender, intermediate_server


async def test_all(test_server):
    intermediate_app = intermediate_server.IntermediateServerApp()
    server = await test_server(intermediate_app)

    for i in range(10):
        message = "TEST MESSAGE " + str(i)

        received = []
        receiver_obj = receiver.Receiver(server.make_url('/'), output=received.append)

        sender_obj = sender.Sender(server.make_url('/'))
        sender_obj.data.put_nowait(message)

        await asyncio.gather(asyncio.ensure_future(receiver_obj.run_client_server()),
                             asyncio.ensure_future(sender_obj.run_client_server()))

        assert received == [message]


class NattedReceiver(receiver.Receiver):
    async def handle_server_connection(self, request):
        await asyncio.Future()


class NattedSender(sender.Sender):
    async def handle_server_connection(self, request):
        await asyncio.Future()


async def test_receiver_nat(test_server):
    intermediate_app = intermediate_server.IntermediateServerApp()
    server = await test_server(intermediate_app)

    for i in range(10):
        message = "TEST MESSAGE " + str(i)

        received = []
        receiver_obj = NattedReceiver(server.make_url('/'), output=received.append)

        sender_obj = sender.Sender(server.make_url('/'))
        sender_obj.data.put_nowait(message)

        await asyncio.gather(asyncio.ensure_future(receiver_obj.run_client_server()),
                             asyncio.ensure_future(sender_obj.run_client_server()))

        assert received == [message]


async def test_sender_nat(test_server):
    intermediate_app = intermediate_server.IntermediateServerApp()
    server = await test_server(intermediate_app)

    for i in range(10):
        message = "TEST MESSAGE " + str(i)

        received = []
        receiver_obj = receiver.Receiver(server.make_url('/'), output=received.append)

        sender_obj = NattedSender(server.make_url('/'))
        sender_obj.data.put_nowait(message)

        await asyncio.gather(asyncio.ensure_future(receiver_obj.run_client_server()),
                             asyncio.ensure_future(sender_obj.run_client_server()))

        assert received == [message]
