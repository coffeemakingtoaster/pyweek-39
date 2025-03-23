# This is the most straightforward way of implementing this...
from ast import match_case
import logging
from typing import Dict, Tuple
from enum import Enum

from server.match import Match

class PlayerStates(Enum):
    IN_QUEUE = "in_queue"
    MATCHED = "matched"
    IN_GAME = "in_game"
    UNKNOWN = "unknown"

class MatchMaker():
    def __init__(self) -> None:
        self.queued_players = set()
        self.match_overview: Dict[str, Match] = dict()
        self.player_id_match_lookup = dict()
        self.logger = logging.getLogger(__name__)

    def add_player(self, player_id: str):
        self.logger.info(f"New player in queue ({player_id}). Currently {len(self.queued_players)+1} in queue...")
        self.queued_players.add(player_id)
        self.__try_to_match()

    def remove_player(self, player_id: str):
        if player_id in self.queued_players:
            self.queued_players.remove(player_id)
            return
        if player_id in self.player_id_match_lookup:
            match_id = self.player_id_match_lookup[player_id]
            del self.player_id_match_lookup[player_id]
            self.match_overview[match_id].terminate()

    def __try_to_match(self):
        # couldnt match
        if len(self.queued_players) < 2:
            return
        match = Match()
        self.match_overview[match.id] = match
        #TODO: Does this need locking when a lot of players connect?
        player_1, player_2 = self.queued_players.pop(), self.queued_players.pop()
        self.player_id_match_lookup[player_1] = match.id
        self.player_id_match_lookup[player_2] = match.id
        self.logger.info(f"New match created ({match.id}). Currently {len(self.queued_players)} in queue...")

    def get_player_status(self, player_id: str) -> Tuple[PlayerStates, str]:
        if player_id in self.queued_players:
            return (PlayerStates.IN_QUEUE, "")
        if player_id in self.player_id_match_lookup:
            player_match = self.match_overview.get(self.player_id_match_lookup[player_id])
            # Initial lobby was terminated
            if player_match is None:
                del self.player_id_match_lookup[player_id]
                return (PlayerStates.IN_QUEUE, "")
            if player_match.lobby_ready:
                return (PlayerStates.IN_GAME, player_match.id)
            return (PlayerStates.MATCHED, player_match.id)
        return (PlayerStates.UNKNOWN, "")

    def is_valid_match_id(self, match_id: str) -> bool:
        return match_id in self.match_overview

    def get_match(self, match_id: str) -> Match:
        return self.match_overview.get(match_id)
