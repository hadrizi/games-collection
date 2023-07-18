import asyncio
import json
import os
import random
import signal

from websockets.legacy.protocol import broadcast
from websockets.server import serve, WebSocketServerProtocol, unix_serve

CONNECTED = set()
PLAYERS = []
CARD_DENOMONATIONS = [str(n) for n in range(2, 11)]
CARD_DENOMONATIONS.extend(["J", "K", "Q", "A"])
CARD_SUITS = ["hearts", "diamonds", "clubs", "spades"]
CARDS = []
for suit in CARD_SUITS:
    for n in CARD_DENOMONATIONS:
        CARDS.append(f"{suit}_{n}")


async def play(websocket: WebSocketServerProtocol):
    async for message in websocket:
        event = json.loads(message)
        # assert event["type"] == "play"
        if event["type"] == "card_draw":
            CARDS.pop()
            broadcast(CONNECTED, json.dumps({
                "type": "top_card",
                "card": CARDS[-1]
            }))

        broadcast(CONNECTED, message)


async def join(websocket: WebSocketServerProtocol, player_id, **_):
    broadcast(CONNECTED, json.dumps({"type": "joined", "player_id": player_id}))
    CONNECTED.add(websocket)
    await websocket.send(json.dumps({
        "type": "top_card",
        "card": CARDS[-1]
    }))
    await websocket.send(json.dumps({
        "type": "players",
        "players": PLAYERS
    }))
    PLAYERS.append(player_id)
    print(f"Player {player_id} joined")
    try:
        await play(websocket)
    finally:
        CONNECTED.remove(websocket)
        PLAYERS.remove(player_id)


async def handler(websocket: WebSocketServerProtocol):
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"

    await join(websocket, **event)


async def main_local():
    random.shuffle(CARDS)
    async with serve(handler, "localhost", 8001):
        print("Listening ws on localhost")
        await asyncio.Future()


async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with serve(
        handler,
        "",
        8001
    ):
        await stop


def run_local():
    asyncio.run(main_local())


def run():
    asyncio.run(main())
