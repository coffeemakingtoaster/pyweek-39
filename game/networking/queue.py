import json
import logging
from typing import Tuple

from direct.task.Task import Task
from game.const.networking import HOST
import requests

LOGGER = logging.getLogger(__name__)

def join_queue(player_id: str) -> bool:
    url = f'http://{HOST}/queue'
    body = {'player_id': player_id}
    try:
        res = requests.post(url, json = body)
    except Exception as e:
        LOGGER.warning(f"Could not join queue. This may indicate network problems. Either way please play against a bot in the meantime. Error {e}")
        return Task.done
    if res.status_code != 201:
        LOGGER.warning("Could not join queue. This may indicate network problems. Either way please play against a bot in the meantime")
        return Task.done
    return Task.done

def check_queue_status(player_id: str) -> Tuple[ bool, str, str]:
    try:
        res = requests.get(f"http://{HOST}/queue/{player_id}")
    except Exception as e:
        LOGGER.warning(f"Could not join queue. This may indicate network problems. Either way please play against a bot in the meantime. Error {e}")
        return (False, "", "")
    if res.status_code != 200:
        LOGGER.warning("Could not join queue. This may indicate network problems. Either way please play against a bot in the meantime")
        return (False, "", "")
    id = res.json().get("match_id", "")
    return (True, res.json()["status"], id)

def leave_queue(player_id: str) -> bool:
    url = f'http://{HOST}/queue/{player_id}'
    try:
        res = requests.delete(url)
    except Exception as e:
        LOGGER.warning(f"Could not leave queue. This may indicate network problems. Either way please play against a bot in the meantime. Error {e}")
        return False
    if res.status_code != 200:
        LOGGER.warning("Could not leave queue. This may indicate network problems. Either way please play against a bot in the meantime")
        return False
    return True


