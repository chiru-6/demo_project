"""Application controller: database setup, CSV import, and main window creation.

This module provides the startup logic: create DB, optionally import CSV,
and create the main window. Used by app.py. Follows Google Python style.
"""

import logging
import os
from typing import Optional

from models.appdata import DEFAULT_CSV_PATHS
from models.db import DatabaseManager
from views.main_window import MainWindow


def get_db(db_path: str = "database.db") -> DatabaseManager:
    """Creates and initializes the database manager.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Initialized DatabaseManager instance.
    """
    return DatabaseManager(db_path=db_path)


def import_csv_if_needed(
    db: DatabaseManager,
    logger: Optional[logging.Logger] = None,
    csv_paths: Optional[tuple] = None,
) -> None:
    """Imports CSV into the database if a file exists and DB is empty.

    Prefers dataset.csv, then LCA_Test_Data.csv. Logs result.

    Args:
        db: DatabaseManager instance.
        logger: Logger to use; if None, uses module logger.
        csv_paths: Tuple of paths to try; defaults to DEFAULT_CSV_PATHS.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    paths = csv_paths or DEFAULT_CSV_PATHS
    csv_path = None
    for p in paths:
        if os.path.exists(p):
            csv_path = p
            break
    if not csv_path:
        logger.info("No CSV file found (%s)", ", ".join(paths))
        return
    ok, msg = db.import_csv(csv_path)
    if ok:
        logger.info("Imported CSV '%s': %s", csv_path, msg)
    else:
        logger.info("CSV import skipped or failed for '%s': %s", csv_path, msg)


def create_main_window(db: DatabaseManager) -> MainWindow:
    """Creates the main application window with the given database.

    Args:
        db: DatabaseManager instance to pass to the window and child views.

    Returns:
        Configured MainWindow instance (not shown).
    """
    return MainWindow(db)
