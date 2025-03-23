import asyncio
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from server.player import Player

class Match():
    player_1_slot: Player | None = None
    player_2_slot: Player | None = None

    lobby_ready = False

    game_finished = False

    terminated = False

    is_primary = False

    def __init__(self) -> None:
        self.id = str(uuid.uuid4())
        self.logger = logging.getLogger(f"{__name__}: {self.id}")
        # run background task
        asyncio.create_task(self.match_loop())

    async def __add_player(self, id: str, websocket: WebSocket):
        if self.player_1_slot is None:
            self.player_1_slot = Player(id, websocket)
            await self.player_1_slot.send_message("Joined as player 1")
            self.logger.debug("Player 1 joined")
        else:
            self.player_2_slot = Player(id, websocket)
            await self.player_2_slot.send_message("Joined as player 2")
            self.logger.debug("Player 2 joined")
            self.lobby_ready = True

    async def __broadcast(self, message: str):
        if self.player_1_slot is None or self.player_2_slot is None:
            self.logger.error("Attempted broadcast but not all clients present")
            return
        await self.player_1_slot.send_message(message)
        await self.player_2_slot.send_message(message)

    async def __safe_broadcast(self, message: str):
        if self.player_1_slot is not None:
            await self.player_1_slot.send_message(message)
        if self.player_2_slot is not None:
            await self.player_2_slot.send_message(message)


    async def terminate(self):
        self.logger.info("Game terminated!")
        if self.player_1_slot is not None:
            await self.player_1_slot.send_message("Game terminated...")
            await self.player_1_slot.disconnect()
        if self.player_2_slot is not None:
            await self.player_2_slot.send_message("Game terminated...")
            await self.player_2_slot.disconnect()
        self.game_finished = True
        self.lobby_ready = True
        self.terminated = True

    async def match_loop(self):
        while not self.lobby_ready:
            await asyncio.sleep(1)
            # This can only happen for first player...
            await self.__safe_broadcast("Waiting for players...")

        self.logger.debug("All players joined! Starting game...")
        await self.__broadcast("All players joined! Starting game...")
        while not self.game_finished and not self.terminated:
            if not self.player_1_slot.is_still_in_match():
                self.logger.debug("Player 2 won because player 1 is no longer connected")
                await self.player_2_slot.declare_victor(False)
                self.game_finished = True
                continue
            if not self.player_2_slot.is_still_in_match():
                self.logger.debug("Player 1 won because player 1 is no longer connected")
                await self.player_1_slot.declare_victor(False)
                self.game_finished = True
                continue
            self.logger.debug("Communicating actions")

            try:
                # TODO: this is probably not ideal! We will just use this for now until we have a game to test this on
                await self.player_1_slot.send_data(await self.player_2_slot.receive_data())
                await self.player_2_slot.send_data(await self.player_1_slot.receive_data())
            except WebSocketDisconnect: 
               self.logger.info("One player left mid match...the remaining player will be declared the winner")
            except Exception as e:
                self.logger.warning(f"An error occured when communicating actions between players {e}")

        self.logger.debug("Game finished")

    async def accept_player(self, id: str, websocket: WebSocket):
        await self.__add_player(id, websocket)

        while not self.game_finished and not self.terminated:
            await asyncio.sleep(1)


