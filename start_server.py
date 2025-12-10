import argparse

import fire
import uvicorn
from loguru import logger

from sorawm.configs import LOGS_PATH
from sorawm.server.app import init_app


def start_server(port=8000, host="0.0.0.0", workers=1):
    logger.info(f"Starting server at {host}:{port}")
    app = init_app()
    config = uvicorn.Config(app, host=host, port=port, workers=workers)
    server = uvicorn.Server(config=config)
    try:
        server.run()
    finally:
        logger.info("Server shutdown.")


if __name__ == "__main__":
    fire.Fire(start_server)
