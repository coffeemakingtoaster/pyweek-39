import asyncio
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from server.player import Player
from shared.types.status_message import GameStatus, StatusMessages

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

    async def __add_player(self, id: str, name: str, websocket: WebSocket):
        if self.player_1_slot is None:
            self.player_1_slot = Player(id, name, websocket)
            await self.player_1_slot.send_control_message(GameStatus(message=StatusMessages.PLAYER_1))
            self.logger.debug("Player 1 joined")
            return self.player_1_slot
        else:
            self.player_2_slot = Player(id, name, websocket)
            await self.player_2_slot.send_control_message(GameStatus(message=StatusMessages.PLAYER_2))
            self.logger.debug("Player 2 joined")
            self.lobby_ready = True
            return self.player_2_slot

    async def __broadcast(self, message: GameStatus):
        if self.player_1_slot is None or self.player_2_slot is None:
            self.logger.error("Attempted broadcast but not all clients present")
            return
        await self.player_1_slot.send_control_message(message)
        await self.player_2_slot.send_control_message(message)

    async def __safe_broadcast(self, message: GameStatus):
        if self.player_1_slot is not None:
            await self.player_1_slot.send_control_message(message)
        if self.player_2_slot is not None:
            await self.player_2_slot.send_control_message(message)

    async def terminate(self):
        self.logger.info("Game terminated!")
        if self.player_1_slot is not None:
            await self.player_1_slot.send_control_message(GameStatus(StatusMessages.TERMINATED))
            await self.player_1_slot.disconnect()
        if self.player_2_slot is not None:
            await self.player_2_slot.send_control_message(GameStatus(StatusMessages.TERMINATED))
            await self.player_2_slot.disconnect()
        self.game_finished = True
        self.lobby_ready = True
        self.terminated = True

    def ready_to_die(self) -> bool:
        return self.game_finished or self.terminated

    async def match_loop(self):
        while not self.lobby_ready:
            await asyncio.sleep(1)
            # This can only happen for first player...
            await self.__safe_broadcast(GameStatus(StatusMessages.LOBBY_WAITING))

        self.logger.debug("All players joined! Starting game...")
        await self.player_1_slot.send_control_message(GameStatus(StatusMessages.PLAYER_NAME, self.player_2_slot.name))
        await self.player_2_slot.send_control_message(GameStatus(StatusMessages.PLAYER_NAME, self.player_1_slot.name))
        await self.__broadcast(GameStatus("lobby_starting"))
        while not self.game_finished and not self.terminated:
            if not self.player_1_slot.is_still_in_match():
                self.logger.debug("Player 2 won because player 1 is no longer connected")
                await self.player_2_slot.declare_victor()
                self.game_finished = True
                continue
            if not self.player_2_slot.is_still_in_match():
                self.logger.debug("Player 1 won because player 1 is no longer connected")
                await self.player_1_slot.declare_victor()
                self.game_finished = True
                continue

            try:
                send_tasks = []
                if (p1_msg:=self.player_1_slot.flush_last_message()) is not None:
                    send_tasks.append(self.player_2_slot.send_player_info(p1_msg))
                    if p1_msg.health <= 0.0:
                        send_tasks.append(self.player_2_slot.declare_victor())
                        send_tasks.append(self.player_1_slot.declare_loser())
                        self.game_finished = True
                if (p2_msg:=self.player_2_slot.flush_last_message()) is not None:
                    send_tasks.append(self.player_1_slot.send_player_info(p2_msg))
                    if p2_msg.health <= 0.0:
                        send_tasks.append(self.player_1_slot.declare_victor())
                        send_tasks.append(self.player_2_slot.declare_loser())
                        self.game_finished = True

                if len(send_tasks) > 0:
                    await asyncio.gather(*send_tasks)
                else:
                    await asyncio.sleep(0.001)

            except WebSocketDisconnect: 
               self.logger.info("One player left mid match...the remaining player will be declared the winner")
            except Exception as e:
                self.logger.warning(f"An error occured when communicating actions between players. This likely means a player has disconnected. {e}")

        self.logger.debug("Game finished")

    async def accept_player(self, id: str, name:str, websocket: WebSocket):
        player = await self.__add_player(id, name, websocket)

        while not self.game_finished and not self.terminated:
            await player.receive_data()


