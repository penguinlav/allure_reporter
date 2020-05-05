import asyncio
import logging
import os
import shutil
import signal
import tempfile
import uuid
from functools import wraps
from pathlib import Path
from types import FrameType
from typing import AsyncGenerator, Callable, cast

from aiofiles.os import mkdir
from async_generator import asynccontextmanager
from loguru import logger
from starlette.concurrency import run_in_threadpool

from .errors import FlockError


def run_once(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: tuple, **kwargs: dict):
        if not wrapper.executed:
            wrapper.executed = True
            wrapper.value = func(*args, **kwargs)
        return wrapper.value

    def clear():
        wrapper.executed = None
        wrapper.value = None

    wrapper.cache_clear = clear
    wrapper.cache_clear()
    return wrapper


@asynccontextmanager
async def mktmpdir() -> AsyncGenerator[Path, None]:
    tmp_dir: Path = Path(tempfile.gettempdir()) / str(uuid.uuid4())
    await mkdir(tmp_dir)
    try:
        yield tmp_dir
    finally:
        await run_in_threadpool(shutil.rmtree, tmp_dir, ignore_errors=True)


@asynccontextmanager
async def flock(name: str, acquire_timeout: int) -> AsyncGenerator[None, None]:
    logger.info(f"Try lock '{name}'")
    proc = await asyncio.create_subprocess_exec(
        "flock",
        "-x",
        "-w",
        str(acquire_timeout),
        f"/tmp/{name}.lock",
        "-c",
        'echo "ok"; while :; do sleep 10; done',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    if (await proc.stdout.readline()).strip() == b"ok":
        pass
        logger.info(f"File '{name}' locked")
    else:
        logger.warning(f"File '{name}' blocked")
        raise FlockError(f"File '{name}' locked")
    try:
        yield
    finally:
        logger.info(f"File '{name}' released")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        await proc.wait()


class flock_decorator:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args: tuple, **kwargs: dict):
            async with flock(self.name):
                return await func(*args, **kwargs)

        return wrapper


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
