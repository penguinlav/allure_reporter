import logging
import sys
from typing import List

from fastapi import FastAPI
from loguru import logger

from ..config import Settings, config, setup_projectspace
from ..errors import AllureReportError
from ..utils import InterceptHandler
from .http_error import app_error_handler
from .routers import router


def create_app() -> FastAPI:
    conf: Settings = config()

    log_level: int = logging.DEBUG if conf.debug else logging.INFO
    LOGGERS = ("uvicorn.asgi", "uvicorn.access", "fastapi")
    for logging_logger in list(map(lambda log_name: logging.getLogger(log_name), LOGGERS)) + [logging.getLogger()]:
        logging_logger.handlers = [InterceptHandler(level=log_level)]

    handlers: List[dict] = [{"sink": sys.stdout, "level": log_level, "enqueue": True}]
    if conf.log_file is not None:
        handlers.append({"sink": conf.log_file, "level": log_level})
    logger.configure(handlers=handlers)

    setup_projectspace(conf)
    application = FastAPI()
    application.include_router(router, prefix=conf.api_prefix)
    application.add_exception_handler(AllureReportError, app_error_handler)
    return application
