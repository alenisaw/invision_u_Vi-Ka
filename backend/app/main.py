"""
File: main.py
Purpose: FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from importlib import import_module
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.modules.auth.service import AuthService
from app.schemas.common import error_response


logger = logging.getLogger(__name__)

ROUTER_MODULES = (
    "app.modules.auth.router",
    "app.modules.admin.router",
    "app.modules.demo.router",
    "app.modules.gateway.router",
    "app.modules.intake.router",
    "app.modules.workspace.router",
    "app.modules.review.router",
)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        service = AuthService(session)
        await service.bootstrap_admin_user()
    yield


def create_application() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        lifespan=_lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)
    _register_core_routes(app)
    _include_available_routers(app)
    return app


def _get_allowed_origins(settings: Settings) -> list[str]:
    return settings.backend_cors_origins


def _register_core_routes(app: FastAPI) -> None:
    settings: Settings = app.state.settings

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "status": "ok",
            "version": settings.app_version,
        }

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code, message, details = _http_exception_payload(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code=code, message=message, details=details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_response(
                code="VALIDATION_ERROR",
                message="Invalid request payload",
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled exception while processing %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=error_response(
                code="INTERNAL_SERVER_ERROR",
                message="Internal server error",
            ),
        )


def _http_exception_payload(
    exc: StarletteHTTPException,
) -> tuple[str, str, dict[str, object]]:
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 409:
        code = "CONFLICT"
    elif exc.status_code == 422:
        code = "VALIDATION_ERROR"
    elif exc.status_code == 503:
        code = "SERVICE_UNAVAILABLE"
    else:
        code = f"HTTP_{exc.status_code}"

    if isinstance(exc.detail, dict):
        message = str(
            exc.detail.get("message")
            or exc.detail.get("detail")
            or "Request failed"
        )
        details = {
            key: value
            for key, value in exc.detail.items()
            if key not in {"message", "detail"}
        }
        if "code" in exc.detail and isinstance(exc.detail["code"], str):
            code = exc.detail["code"]
    elif exc.detail is None:
        message = "Request failed"
        details = {}
    else:
        message = str(exc.detail)
        details = {}
    return code, message, details


def _include_available_routers(app: FastAPI) -> None:
    for module_path in ROUTER_MODULES:
        router = _load_router(module_path)
        if router is not None:
            app.include_router(router)


def _load_router(module_path: str) -> APIRouter | None:
    try:
        module = import_module(module_path)
    except Exception as exc:  # pragma: no cover - defensive bootstrap path
        logger.warning("Failed to import router module %s: %s", module_path, exc)
        return None

    router = getattr(module, "router", None)
    if router is None:
        logger.info("Router module %s is present but router is not defined yet", module_path)
        return None

    if not isinstance(router, APIRouter):
        logger.warning("Module %s defines non-APIRouter 'router', skipping", module_path)
        return None

    return router


app = create_application()
