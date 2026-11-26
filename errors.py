from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


def forbidden(_request: Request, error: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(error)})


def bad_request(_request: Request, error: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


def database_conflict(_request: Request, _error: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Конфликт с данными в базе"})


def invalid_input(_request: Request, error: RequestValidationError):
    details = [
        {"loc": item["loc"], "msg": item["msg"], "type": item["type"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})


exception_handlers = {
    PermissionError: forbidden,
    ValueError: bad_request,
    IntegrityError: database_conflict,
    RequestValidationError: invalid_input,
}
