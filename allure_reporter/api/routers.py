from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from loguru import logger
from starlette.responses import FileResponse

from ..config import Settings
from ..repos import ReportRepo
from .dependencies import get_flock_branch, get_report_repo, get_settings

__all__ = ("router",)

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"result": "ok"}


@router.post("/generate", tags=["generates"], dependencies=[Depends(get_flock_branch)])
async def generate(
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    results: UploadFile = File(...),
    repo: ReportRepo = Depends(get_report_repo),
):
    await repo.save_results(results)
    file_report: Path = await repo.make_report()

    if settings.stats_handler_maker is not None:
        logger.info("Added stats handler for response")
        background_tasks.add_task(settings.stats_handler_maker(await repo.get_stats()))

    return FileResponse(str(file_report))
