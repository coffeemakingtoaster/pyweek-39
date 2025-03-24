import logging
from typing import Dict, Tuple
import time

from server.match import Match
from shared.const.queue_status import QueueStatus

PLAYER_LIVETIME_S = 5

class MatchMaker():
    def __init__(self) -> None:
        self.queued_players = set()
        self.queued_players_live = dict()
        self.match_overview: Dict[str, Match] = dict()
        self.player_id_match_lookup = dict()
        self.logger = logging.getLogger(__name__)

    def add_player(self, player_id: str):
        self.logger.info(f"New player in queue ({player_id}). Currently {len(self.queued_players)+1} in queue (Pending cleanup)")
        self.queued_players.add(player_id)
        self.queued_players_live[player_id] = time.time()
        self.__try_to_match()

    def remove_player(self, player_id: str):
        if player_id in self.queued_players:
            self.queued_players.remove(player_id)
            del self.queued_players_live[player_id]
            self.logger.info(f"Player left queue ({player_id}). Currently {len(self.queued_players)} in queue...")
            return
        if player_id in self.player_id_match_lookup:
            match_id = self.player_id_match_lookup[player_id]
            self.logger.info(f"Player left in limbo between game and queue ({player_id}). Terminating game ({match_id})...")
            del self.player_id_match_lookup[player_id]
            _ = self.match_overview[match_id].terminate()

    def cleanup(self):
        self.__queue_cleanup()
        self.__match_cleanup()

    def __queue_cleanup(self):
        """Remove dead players from queue"""
        cleanup_ids = []
        for player_id, last_heartbeat in self.queued_players_live.items():
            if time.time() - last_heartbeat > PLAYER_LIVETIME_S:
                cleanup_ids.append(player_id)
        for id in cleanup_ids:
            del self.queued_players_live[id]
            self.queued_players.remove(id)

        if len(cleanup_ids) > 0:
            self.logger.info(f"Removed {len(cleanup_ids)} from queue")

    def __match_cleanup(self):
        """Remove finished/terminated matches from queue"""
        cleanup_ids = []
        for match_id, match in self.match_overview.items():
            if match.ready_to_die():
                cleanup_ids.append(match_id)
        for id in cleanup_ids:
            match = self.match_overview.pop(id)
            if match.player_1_slot is not None:
                del self.player_id_match_lookup[match.player_1_slot.id]
            if match.player_2_slot is not None:
                del self.player_id_match_lookup[match.player_2_slot.id]

        if len(cleanup_ids) > 0:
            self.logger.info(f"Removed {len(cleanup_ids)} from match pool")

    def __try_to_match(self):
        self.cleanup()
        # couldn't match
        if len(self.queued_players) < 2:
            return
        match = Match()
        self.match_overview[match.id] = match
        #TODO: Does this need locking when a lot of players connect?
        player_1, player_2 = self.queued_players.pop(), self.queued_players.pop()
        self.player_id_match_lookup[player_1] = match.id
        self.player_id_match_lookup[player_2] = match.id
        del self.queued_players_live[player_1]
        del self.queued_players_live[player_2]
        self.logger.info(f"New match created ({match.id}). Currently {len(self.queued_players)} in queue...")

    def get_player_status(self, player_id: str) -> Tuple[QueueStatus, str]:
        if player_id in self.queued_players:
            self.queued_players_live[player_id] = time.time()
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
