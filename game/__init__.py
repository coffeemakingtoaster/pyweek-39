import logging
from shared.utils.logging import init_logger

# import this first to ensure that logging is setup before anything happens
init_logger()

from game.main_application import MainGame


logger = logging.getLogger(__name__)

def run():
    logger.info("Starting...")
    game = MainGame()
    game.run()
