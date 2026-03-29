"""
File: main.py
Purpose: FastAPI application entry point.
"""

from __future__ import annotations

from importlib import import_module
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)

ROUTER_MODULES = (
    "app.modules.m1_gateway.router",
    "app.modules.m2_intake.router",
    "app.modules.m8_dashboard.router",
    "app.modules.m10_audit.router",
)


def create_application() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
