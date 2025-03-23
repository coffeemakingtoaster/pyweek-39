# This is the most straightforward way of implementing this...
from ast import match_case
import logging
from typing import Dict, Tuple
from enum import Enum

from server.match import Match
from shared.const.queue_status import QueueStatus

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
            self.logger.info(f"Player left queue ({player_id}). Currently {len(self.queued_players)} in queue...")
            return
        if player_id in self.player_id_match_lookup:
            match_id = self.player_id_match_lookup[player_id]
            self.logger.info(f"Player left in limbo between game and queue ({player_id}). Terminating game ({match_id})...")
            del self.player_id_match_lookup[player_id]
            _ = self.match_overview[match_id].terminate()

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

    def get_player_status(self, player_id: str) -> Tuple[QueueStatus, str]:
        if player_id in self.queued_players:
            return (QueueStatus.IN_QUEUE, "")
        if player_id in self.player_id_match_lookup:
            player_match = self.match_overview.get(self.player_id_match_lookup[player_id])
            # Initial lobby was terminated
            if player_match is None:
                del self.player_id_match_lookup[player_id]
                return (QueueStatus.IN_QUEUE, "")
            if player_match.lobby_ready:
                return (QueueStatus.IN_GAME, player_match.id)
            return (QueueStatus.MATCHED, player_match.id)
        return (QueueStatus.UNKNOWN, "")

    def is_valid_match_id(self, match_id: str) -> bool:
        return match_id in self.match_overview

    def get_match(self, match_id: str) -> Match:
        return self.match_overview.get(match_id)
