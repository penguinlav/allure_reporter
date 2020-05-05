from starlette.status import HTTP_400_BAD_REQUEST, HTTP_408_REQUEST_TIMEOUT, HTTP_500_INTERNAL_SERVER_ERROR


class AllureReportError(Exception):
    status_code = HTTP_400_BAD_REQUEST


class RequestError(AllureReportError):
    status_code = HTTP_400_BAD_REQUEST


class FlockError(AllureReportError):
    status_code = HTTP_408_REQUEST_TIMEOUT


class ParseError(AllureReportError):
    status_code = HTTP_400_BAD_REQUEST


class SaveZipError(AllureReportError):
    status_code = HTTP_500_INTERNAL_SERVER_ERROR


class MakeReportError(AllureReportError):
    status_code = HTTP_500_INTERNAL_SERVER_ERROR
