"""Main entry point for LCA Test Data Management System.

This module serves as the entry point for the PyQt5 desktop application.
It initializes the application, database, and main window.

Typical usage:
    python main.py
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from database import DatabaseManager
from main_window import MainWindow


def main() -> None:
    """Initializes and runs the main application.
    
    This function performs the following:
        1. Enables high DPI scaling for better display on high-resolution screens
        2. Creates the Qt application instance
        3. Initializes the database and imports CSV data if available
        4. Creates and displays the main window
        5. Starts the application event loop
    """
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("LCA Test Data Management System")
    app.setOrganizationName("HAL")
    
    # Initialize database and import CSV if needed
    db = DatabaseManager()
    if os.path.exists("LCA_Test_Data.csv"):
        db.import_csv("LCA_Test_Data.csv")
    
    # Create and show main window
    window = MainWindow(db)
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
