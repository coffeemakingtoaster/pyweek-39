import logging
from server import server
from shared.utils.logging import init_logger
import uvicorn

PORT = 3000
HOST = "0.0.0.0"

# import this first to ensure that logging is setup before anything happens
init_logger()

logger = logging.getLogger(__name__)

def run():
    logger.info("Starting...")
    uvicorn.run(server.app, port=PORT, host=HOST, log_level='warning')
