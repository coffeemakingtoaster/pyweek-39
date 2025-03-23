import logging
from src.main_application import MainGame
from src.utils.logging import init_logger

init_logger()

logger = logging.getLogger(__name__)

def run():
    logger.info("Starting...")
    game = MainGame()
    game.run()
