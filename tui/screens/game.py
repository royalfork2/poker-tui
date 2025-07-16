import asyncio
import socket
from textual import widgets
from textual.screen import Screen
from textual.containers import Container, Grid
from textual.app import ComposeResult
from tui.widgets.seat import SeatWidget
from tui.widgets.table import TableWidget

# Placeholder for missing variables and objects
curr_player_name = "Player1"  # Replace with actual dynamic player name management

class GameScreen(Screen[None]):
    def __init__(self):
        super().__init__()
        self.seats = {}
        self.game_state = {}
        self.ready_players = set()
        self.players_ready = 0
        self.table = TableWidget()
        self.console = widgets.Static("Console Log", id="console")
        self.seat_map = {}
        self.reader, self.writer = None, None  # For socket connection

    def compose(self) -> ComposeResult:
        with Container():
            with Grid(id="content"):
                yield self.table
                yield self.console

    async def on_start(self):
        # Establish socket connection and start listening for updates in a background task
        await self.connect_to_server()
        self.run_worker(self.listen_for_updates, exclusive=True)

    async def connect_to_server(self):
        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', 8888)
        await self.render_message("Connected to server.")

    def create_seat(self, seat_number: int) -> widgets.Static:
        seat_widget = widgets.Static(f"Seat {seat_number} - Empty", classes="box", id=f"seat_{seat_number}")
        self.seats[seat_number] = seat_widget
        return seat_widget

    async def on_mount(self):
        for seat_number in range(1, 7):  # Example for a 6-player game; adjust as needed
            seat_widget = self.create_seat(seat_number)
            join_button = widgets.Button(label="Join Seat", id=f"join_{seat_number}")
            await seat_widget.mount(join_button)
            await self.mount(seat_widget)

    def update_seat(self, seat_number: int, player_name_seated: str):
        seat = self.seats.get(seat_number)
        if seat:
            seat.remove_children()
            seat.update(f"{player_name_seated}")

            position = widgets.Static("Dealer", classes="label")
            nametag = widgets.Static(f"{player_name_seated}", classes="label")
            stack = widgets.Static("100BB", classes="label")

            seat.mount(position, nametag, stack)

            if player_name_seated == curr_player_name:
                for seat_num, widget in self.seats.items():
                    if widget:
                        button = widget.query_one(f"#join_{seat_num}", widgets.Button, default=None)
                        if button:
                            button.remove()
            else:
                button = seat.query_one(f"#join_{seat_number}", widgets.Button, default=None)
                if button:
                    button.remove()

    async def on_button_pressed(self, event: widgets.Button.Pressed):
        button_id = event.button.id
        if button_id.startswith("join_"):
            seat_number = int(button_id.split("_")[1])
            self.update_seat(seat_number, curr_player_name)
            message = f"Join,{seat_number}"
            self.writer.write(message.encode("utf-8"))
            await self.writer.drain()
            await self.mount(widgets.Button(label="Ready", id="ready"))
        elif button_id == "bet":
            input_box = self.query_one("#bet_amount", widgets.Input, default=None)
            if input_box:
                bet_value = input_box.value
                message = f"Bet,{curr_player_name},{bet_value}"
                self.writer.write(message.encode("utf-8"))
                await self.writer.drain()
                input_box.value = ""
        elif button_id == "check":
            message = f"Check,{curr_player_name}"
            self.writer.write(message.encode("utf-8"))
            await self.writer.drain()
        elif button_id == "fold":
            message = f"Fold,{curr_player_name}"
            self.writer.write(message.encode("utf-8"))
            await self.writer.drain()
        elif button_id == "ready":
            await self.handle_ready()

    async def handle_ready(self):
        self.ready_players.add(curr_player_name)
        message = f"Ready,{curr_player_name}"
        self.writer.write(message.encode("utf-8"))
        await self.writer.drain()
        if len(self.ready_players) >= 2:
            await self.start_round()

    async def start_round(self):
        ready_button = self.query_one("#ready", widgets.Button, default=None)
        if ready_button:
            ready_button.remove()
        await self.mount(widgets.Button(label="Fold", id="fold"))
        await self.mount(widgets.Button(label="Check", id="check"))
        await self.mount(widgets.Button(label="Bet", id="bet"))
        await self.mount(widgets.Input(id="bet_amount", placeholder="Enter your bet"))

    async def listen_for_updates(self):
        while True:
            try:
                data = await self.reader.read(1024)
                if not data:
                    break
                message = data.decode("utf-8")
                player_name, action_type, *args = message.split(",")

                if action_type == "Join":
                    seat_number = int(args[0])
                    self.update_seat(seat_number, player_name)
                elif action_type == "Connect":
                    await self.render_message(f"{player_name} connected")
                elif action_type == "Ready":
                    await self.render_message(f"{player_name} is ready!")
            except Exception as e:
                await self.render_message(f"Error: {e}")
                await asyncio.sleep(0.1)
