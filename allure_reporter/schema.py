from pathlib import Path
from typing import Optional

from pydantic import BaseModel, constr, validator

from .config import config
from .errors import RequestError


class SpaceIn(BaseModel):
    project: str
    branch: constr(strict=True, regex=r"[0-9_\-a-zA-Z /]+")
    revision: constr(strict=True, regex=r"[0-9a-zA-Z]+")
    url_email_report: Optional[str] = None

    @validator("project")
    def projects_from_config(cls, project: str) -> str:
        if project not in config().projects:
            raise RequestError("Unregistered project")
        return project

    @validator("branch")
    def branch_validator(cls, branch: str) -> str:
        return branch.replace("/", "_").replace(" ", "_").lower()

    @validator("revision", "project")
    def lower(cls, value: str) -> str:
        return value.lower()


class Space(BaseModel):
    project: Path
    branch: Path
    history: Path
    revisions: Path
    rev: Path
