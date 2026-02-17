"""Backward-compatibility shim for database access.

New code should use: from models.db import DatabaseManager
"""

from models.db import DatabaseManager

__all__ = ["DatabaseManager"]
