"""Models package for Test Data Management System.

This package contains data access, domain logic, and application data:
    - db: DatabaseManager for SQLite operations
    - logic: Reusable business logic (statistics, transformations)
    - appdata: Application-level data structures and constants
"""

from .db import DatabaseManager

__all__ = ["DatabaseManager"]
