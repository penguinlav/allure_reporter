import os
import shlex
import subprocess
from pathlib import Path
from typing import List, Optional

from loguru import logger
from pydantic import AnyHttpUrl
from pydantic import BaseSettings as _BaseSettins
from pydantic import DirectoryPath, FilePath, PositiveInt, PyObject, conlist, constr, validator
from pydantic.error_wrappers import ValidationError

from .utils import run_once

__all__ = ("Settings", "config")

BASE = Path(__file__).parent.absolute()


class BaseSettings(_BaseSettins):
    class Config:
        env_prefix = "AL_"


class EmailSettings(BaseSettings):
    template: FilePath = BASE.joinpath("./templates/mail.html").absolute()
    css: AnyHttpUrl = "https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/cosmo/bootstrap.css"
    export_path: str = "mail.html"
    title_fmt: str = "Branch: {branch} rev: {rev}"


# def make_stats_handler(stats: Optional[dict]):
#     async def send():
#         """Async func for sending metrics"""
#
#     return send


class Settings(BaseSettings):
    debug: bool = False
    log_file: Optional[str] = None
    api_prefix: str = "/api"
    projects: conlist(constr(strict=True, regex=r"[0-9_\-a-zA-Z]+"), min_items=1) = ["pulse-lenta"]
    projectspace: DirectoryPath = BASE.joinpath("../projectspace").absolute()
    email: Optional[EmailSettings] = EmailSettings()
    allure: str
    flock_timeout_sec: PositiveInt = 60
    stats_handler_maker: Optional[PyObject] = None  # staticmethod(make_stats_handler)

    @validator("projects")
    def projects_validator(cls, projects: List[str]) -> List[str]:
        return [project.lower() for project in projects]

    @validator("allure")
    def escape_cmd(cls, value: str) -> str:
        if shlex.quote(value) != value:
            raise RuntimeError("Allure cmd should be escaped")
        try:
            version: str = subprocess.check_output([value, "--version"]).decode("utf-8")
            logger.info(f"Allure version: {version}")
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError(f"Invalid allure cmd '{value}'")
        return value


def setup_projectspace(conf: Settings) -> None:
    for project in conf.projects:
        project_path: Path = conf.projectspace / project
        project_path.mkdir(exist_ok=True)
        project_path.joinpath("branches").mkdir(exist_ok=True)
        logger.info(f"Project '{project}' added")


@run_once
def config(**kwargs):
    try:
        return Settings(**kwargs)
    except ValidationError as e:
        raise RuntimeError(f"Improper configuration, {e}")
