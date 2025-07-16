import asyncio


class Server:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port
        self.clients = []
        self.game_state = {}  # Maintain game state here

    async def handle_client(self, reader, writer):
        client_address = writer.get_extra_info('peername')
        print(f"[INFO] New client connected from {client_address}")
        self.clients.append(writer)

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    print(f"[INFO] Client {client_address} disconnected.")
                    break

                message = data.decode('utf-8')
                print(f"[RECEIVED] Message from {client_address}: {message}")

                # Process the player's action and update the game state here
                self.process_player_action(message)

                # Broadcast the updated game state to all clients
                await self.broadcast_game_state()

        except asyncio.CancelledError:
            print(f"[ERROR] Connection to {client_address} cancelled unexpectedly.")
        except Exception as e:
            print(f"[ERROR] Exception for {client_address}: {e}")

        finally:
            writer.close()
            await writer.wait_closed()
            self.clients.remove(writer)
            print(f"[INFO] Connection closed for {client_address}")

    def process_player_action(self, message):
        # Dummy processing for demonstration
        print(f"[PROCESS] Processing player action: {message}")
        # Here you'd parse the message, update self.game_state, etc.
        self.game_state = {"status": f"Updated with {message}"}

    async def broadcast_game_state(self):
        print("[BROADCAST] Broadcasting game state to all clients")
        for client in self.clients:
            try:
                client.write(self.game_state["status"].encode())
                await client.drain()
                print(f"[SENT] Game state sent to {client.get_extra_info('peername')}")
            except Exception as e:
                print(f"[ERROR] Failed to send to {client.get_extra_info('peername')}: {e}")

    async def start_server(self):
        print(f"[START] Server starting on {self.host}:{self.port}")
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        async with server:
            print("[READY] Server is ready to accept connections")
            await server.serve_forever()


if __name__ == "__main__":
    server = Server()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("[SHUTDOWN] Server shutting down.")
