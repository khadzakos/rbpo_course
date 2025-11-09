import uuid

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import router
from .config import create_tables
from .security import (
    ERROR_TYPES,
    SecureHTTPException,
    create_error_response,
    setup_security_logging,
)

app = FastAPI(
    title="Chore Tracker API",
    description="API для управления пользователями, задачами и назначениями между участниками",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Middleware для добавления correlation ID к каждому запросу"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    error_response = create_error_response(
        request=request,
        error_type=ERROR_TYPES["validation_error"],
        title="API Error",
        detail=exc.message,
        status_code=exc.status,
    )
    return JSONResponse(
        status_code=error_response["status_code"],
        content=error_response["content"],
        headers=error_response["headers"],
    )


@app.exception_handler(SecureHTTPException)
async def secure_http_exception_handler(request: Request, exc: SecureHTTPException):
    error_response = create_error_response(
        request=request,
        error_type=exc.error_type,
        title=exc.title,
        detail=exc.detail,
        status_code=exc.status_code,
        correlation_id=exc.correlation_id,
    )
    return JSONResponse(
        status_code=error_response["status_code"],
        content=error_response["content"],
        headers=error_response["headers"],
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"

    if exc.status_code == 404:
        error_type = ERROR_TYPES["not_found_error"]
        title = "Not Found"
    elif exc.status_code == 401:
        error_type = ERROR_TYPES["authentication_error"]
        title = "Authentication Error"
    elif exc.status_code == 403:
        error_type = ERROR_TYPES["authorization_error"]
        title = "Authorization Error"
    else:
        error_type = ERROR_TYPES["internal_error"]
        title = "Internal Server Error"

    error_response = create_error_response(
        request=request,
        error_type=error_type,
        title=title,
        detail=detail,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=error_response["status_code"],
        content=error_response["content"],
        headers=error_response["headers"],
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик для всех необработанных исключений"""
    error_response = create_error_response(
        request=request,
        error_type=ERROR_TYPES["internal_error"],
        title="Internal Server Error",
        detail="An unexpected error occurred",
        status_code=500,
    )
    return JSONResponse(
        status_code=error_response["status_code"],
        content=error_response["content"],
        headers=error_response["headers"],
    )


@app.on_event("startup")
async def startup_event():
    create_tables()
    setup_security_logging()


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
