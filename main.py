"""
LCA Test Data Management System - Main Entry Point
PyQt5 Desktop Application
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from main_window import MainWindow
from database import DatabaseManager

def main():
    """Main application entry point"""
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
