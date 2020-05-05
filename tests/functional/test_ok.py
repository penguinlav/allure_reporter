import requests


def test_ok(http_service, simple_results):
    # FIXME: mock os, impossible run from ci

    project: str = "pytest_project"
    branch: str = "branch_name"
    revision: str = "rev_12"
    url_email_report: str = "http%3A%2F%2Flocalhost%3A8080%2Frep"

    response = requests.post(
        f"{http_service}/api/generate?branch={branch}&revision={revision}&project={project}&url_email_report={url_email_report}",
        files={"results": open(simple_results, "rb")},
    )

    assert response.status_code == 200
