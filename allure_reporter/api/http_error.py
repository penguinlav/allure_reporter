from starlette.requests import Request
from starlette.responses import JSONResponse

from ..errors import AllureReportError


def app_error_handler(_: Request, e: AllureReportError) -> JSONResponse:
    return JSONResponse({"detail": [{"msg": f"{e}"}]}, status_code=e.status_code)
