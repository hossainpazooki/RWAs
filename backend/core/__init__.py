"""Core package - Shared configuration and domain types.

Database utilities require explicit import:
    from backend.core.database import get_engine, get_session, init_sqlmodel_tables
"""

from .config import Settings, get_settings, ml_available

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "ml_available",
]
