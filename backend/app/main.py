"""
File: main.py
Purpose: FastAPI application entry point.

Notes:
- Start with health and M6 gateway routes.
- Expand router registration as other modules become real.
"""

from __future__ import annotations

from fastapi import FastAPI

from backend.app.modules.m1_gateway.router import router as pipeline_router
from backend.app.schemas.common import API_VERSION

app = FastAPI(
    title="inVision U Candidate Selection System",
    version=API_VERSION,
)

app.include_router(pipeline_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Basic health probe for local development."""

    return {
        "status": "ok",
        "version": API_VERSION,
    }


# File summary: main.py
# Registers the initial FastAPI app and M6-first gateway endpoints.
