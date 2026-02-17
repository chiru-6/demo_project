"""Application entry point for the Test Data Management System.

Run this module to start the app: python app.py

Typical usage:
    python app.py
or:
    python main.py   # main.py delegates to app.main()
"""

import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from controllers.controller import create_main_window, get_db, import_csv_if_needed


def setup_logging() -> None:
    """Configure application-wide logging to file and console."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    """Initializes and runs the main application.

    1. Configures logging
    2. Enables high DPI scaling
    3. Creates the Qt application instance
    4. Initializes the database and imports CSV if available
    5. Creates and displays the main window
    6. Starts the application event loop
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Test Data Management System")

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Test Data Management System")
    app.setOrganizationName("org")

    db = get_db()
    import_csv_if_needed(db, logger=logger)

    window = create_main_window(db)
    window.show()
    logger.info("Main window shown")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
