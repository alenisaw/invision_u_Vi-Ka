"""Compatibility package for top-level ``app`` imports.

The backend source lives under ``backend/app``. This package makes
``import app...`` resolve correctly when commands are run from the
repository root, while still keeping the existing backend layout intact.
"""

from pathlib import Path


_BACKEND_APP_DIR = Path(__file__).resolve().parent.parent / "backend" / "app"

# Point this package at the real backend application package.
__path__ = [str(_BACKEND_APP_DIR)]
