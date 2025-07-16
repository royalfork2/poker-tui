from textual.app import App
from client.client import Client
from tui.screens.game import GameScreen


class PokerApp(App):
    async def on_start(self):
        self.client = Client("127.0.0.1", 8888)
        await self.client.connect()

        print("loading")
        self.load_screen(GameScreen())

        # Use a worker to listen for server updates
        self.run_worker(self.receive_updates, exclusive=True)

    async def receive_updates(self):
        async for update in self.client.receive_updates():
            self.screen.update_game_state(update)
