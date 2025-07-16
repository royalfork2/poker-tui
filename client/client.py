import asyncio

class Client:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send_message(self, message):
        self.writer.write(message.encode())
        await self.writer.drain()

    async def receive_updates(self):
        while True:
            try:
                data = await self.reader.read(1024)
                if not data:
                    break
                # Process received game state update here
            except (ConnectionResetError, BrokenPipeError):
                break
