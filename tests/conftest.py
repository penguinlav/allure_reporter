import zipfile
from pathlib import Path
from typing import IO, Generator

import requests
from fastapi.testclient import TestClient
from pytest import fixture, yield_fixture

from allure_reporter.config import config

DATA_DIR = Path(__file__).parent.absolute() / "data"


def is_responsive(url):
    try:
        response = requests.get(f"{url}/api/ping")
        if response.status_code == 200:
            return True
    except requests.ConnectionError:
        return False


@fixture(scope="session")
def http_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("allure-reporter", 8000)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(timeout=5, pause=0.1, check=lambda: is_responsive(url))
    return url


def pytest_addoption(parser):
    parser.addoption("--allure", default="allure", help="Cmd for allure execution")


@yield_fixture
def local_client(request) -> TestClient:
    config(allure=request.config.getoption("--allure"), projects=["pytest_project"])
    from allure_reporter.api import app

    yield TestClient(app)
    config.cache_clear()


@yield_fixture
def simple_results(tmp_path) -> Generator[IO, None, None]:
    tmp_z_file_path: Path = tmp_path / "simple_results.zip"
    with zipfile.ZipFile(tmp_z_file_path, "w") as z_file:
        results_dir: Path = DATA_DIR / "simple_results"
        for filename in results_dir.iterdir():
            z_file.write(filename, filename.relative_to(results_dir))
    yield tmp_z_file_path
