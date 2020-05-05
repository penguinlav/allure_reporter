import json
import os
import time
import zipfile
from pathlib import Path
from typing import IO, Dict, List, Optional

import aiofiles
from fastapi import UploadFile
from jinja2 import Template
from starlette.concurrency import run_in_threadpool

from .config import Settings
from .errors import AllureReportError, MakeReportError, ParseError, SaveZipError
from .schema import Space, SpaceIn


class SpaceRepo(object):
    def __init__(self, settings: Settings):
        self.settings: Settings = settings

    def _create_space(self, space_in: SpaceIn) -> Space:
        project_path: Path = self.settings.projectspace / space_in.project
        branch_path: Path = project_path / "branches" / space_in.branch
        history_path: Path = branch_path / "history"
        revisions_path: Path = branch_path / "revisions"
        rev_path: Path = revisions_path / space_in.revision

        branch_path.mkdir(exist_ok=True)
        revisions_path.mkdir(exist_ok=True)
        rev_path.mkdir(exist_ok=True)
        history_path.mkdir(exist_ok=True)
        revisions_path.joinpath(space_in.revision).mkdir(exist_ok=True)

        return Space(
            project=project_path, branch=branch_path, history=history_path, revisions=revisions_path, rev=rev_path
        )

    async def create_space(self, space_in: SpaceIn) -> Space:
        return await run_in_threadpool(self._create_space, space_in)


class ReportRepo(object):
    def __init__(self, settings: Settings, tmp_dir: Path, space: Space, query: SpaceIn):
        self.settings: Settings = settings
        self.tmp_dir: Path = tmp_dir
        self.space: Space = space
        self.query: SpaceIn = query

    def _unzip_results(self, results: IO) -> zipfile.ZipFile:
        try:
            return zipfile.ZipFile(results)
        except Exception as e:
            raise ParseError(f"Error unzip: {e}")

    def _save_results(self, results: IO) -> None:
        z_archive: zipfile.ZipFile = self._unzip_results(results)
        try:
            for z_file_info in z_archive.infolist():
                print(z_file_info.filename)
                if z_file_info.is_dir() or len(Path(z_file_info.filename).parts) > 1:
                    raise ParseError("Report contain folders")

                z_file_path: Path = self.space.rev / z_file_info.filename
                filename, file_datetime = str(z_file_path), z_file_info.date_time
                file_datetime = time.mktime(file_datetime + (0, 0, -1))
                with open(filename, "bw") as f:
                    f.write(z_archive.open(z_file_info.filename).read())
                os.utime(filename, (file_datetime, file_datetime))
        except AllureReportError:
            raise
        except Exception as e:
            raise SaveZipError(f"Cannot save report: {e}")

    def _collect_test_cases(self, test_cases_dir: Path) -> List[Dict]:
        test_cases: List[Dict] = []
        for filename in test_cases_dir.glob("*.json"):
            with open(filename) as f:
                try:
                    test_case: Dict = json.load(f)
                except Exception as e:
                    print(e)
                    continue
                if not test_case.get("hidden"):
                    test_cases.append(test_case)
        return test_cases

    def _render_mail_report(self, test_cases: List[Dict], title: str) -> str:
        with open(self.settings.email.template) as f:
            render = Template(f.read())
        return render.render(
            css=self.settings.email.css,
            title=self.settings.email.title_fmt.format(branch=self.query.branch, rev=self.query.revision),
            serverUrl=self.query.url_email_report or "",
            testCases=test_cases,
        )

    def _make_allure_report(self) -> Path:
        link_history: Path = self.space.rev.joinpath("history").absolute()
        link_history.symlink_to(self.space.history.absolute())
        try:
            if (
                os.system(f"{self.settings.allure} generate {self.space.rev.absolute()} -o {self.tmp_dir.absolute()}")
                != 0
            ):
                raise MakeReportError("Error generate report")
            tmp_history_path: Path = Path(self.tmp_dir) / "history"
        finally:
            link_history.unlink()

        if self.settings.email is not None:
            mail: str = self._render_mail_report(
                self._collect_test_cases(self.tmp_dir / "data/test-cases"), f"Revision: {self.space.rev.parts[-1]}"
            )
            with open(self.tmp_dir / "export" / self.settings.email.export_path, "w") as f:
                f.write(mail)

        if (
            os.system(
                f"cd {tmp_history_path.absolute()} && "
                f"cp --recursive --preserve=timestamps $(ls) {self.space.history.absolute()}"
            )
            != 0
        ):
            raise MakeReportError("Error save history")
        if os.system(f"cd {self.tmp_dir.absolute()} && zip -r report.zip .") != 0:
            raise MakeReportError("Error zip report")
        zip_report: Path = self.tmp_dir / "report.zip"
        if not zip_report.exists():
            raise MakeReportError("Error make report.zip")

        return zip_report

    async def save_results(self, results: UploadFile) -> None:
        await run_in_threadpool(self._save_results, results.file)

    async def make_report(self) -> Path:
        zip_report: Path = await run_in_threadpool(self._make_allure_report)
        return zip_report

    async def get_stats(self) -> Optional[dict]:
        storage: dict = {}
        try:
            async with aiofiles.open(self.tmp_dir / "prometheusData.txt") as f:
                async for line in f:
                    name, value = line.strip().split()
                    storage[name] = value
        except (FileNotFoundError, ValueError):
            return None
        return storage
