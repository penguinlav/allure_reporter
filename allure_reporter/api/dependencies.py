from pathlib import Path
from typing import AsyncGenerator

from fastapi import Depends

from ..config import Settings, config
from ..repos import ReportRepo, SpaceRepo
from ..schema import Space, SpaceIn
from ..utils import flock, mktmpdir


async def get_settings() -> Settings:
    return config()


async def get_temporary_folder() -> AsyncGenerator[Path, None]:
    async with mktmpdir() as tmp_dir:
        yield tmp_dir


async def get_workspace(settings: Settings = Depends(get_settings), space: SpaceIn = Depends()) -> Space:
    repo: SpaceRepo = SpaceRepo(settings)
    return await repo.create_space(space)


async def get_flock_branch(settings: Settings = Depends(get_settings), query: SpaceIn = Depends()) -> None:
    async with flock(f"{query.branch}.{query.revision}.lock", settings.flock_timeout_sec):
        yield


def get_report_repo(
    query: SpaceIn = Depends(),
    settings: Settings = Depends(get_settings),
    space: Space = Depends(get_workspace),
    tmp_dir: Path = Depends(get_temporary_folder),
) -> ReportRepo:
    return ReportRepo(settings, tmp_dir, space, query)
