"""Main window module for LCA Test Data Management System.

This module contains the MainWindow class which provides the primary user interface
with a tabbed layout for different functionalities.
"""

from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QStatusBar, QTabWidget,
                             QVBoxLayout, QWidget)

from widgets.add_entry_widget import AddEntryWidget
from widgets.chatbot_widget import ChatbotWidget
from widgets.dashboard_widget import DashboardWidget
from widgets.visualizations_widget import VisualizationsWidget


class MainWindow(QMainWindow):
    """Main application window with tabbed interface.
    
    This class creates the main window containing four tabs:
        - Dashboard: View and filter test data
        - Add Entry: Form to add new test records
        - Visualizations: Charts and graphs
        - Chatbot: AI assistant for querying data
    
    Attributes:
        db: DatabaseManager instance for database operations.
        tabs: QTabWidget containing all application tabs.
        dashboard_tab: Dashboard widget instance.
        add_entry_tab: Add entry form widget instance.
        visualizations_tab: Visualizations widget instance.
        chatbot_tab: Chatbot widget instance.
    """
    
    def __init__(self, db) -> None:
        """Initializes the main window.
        
        Args:
            db: DatabaseManager instance for database operations.
        """
        super().__init__()
        self.db = db
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initializes the user interface.
        
        Creates and configures all UI elements including tabs, widgets,
        and status bar. Also connects signals between widgets.
        """
        self.setWindowTitle("LCA Test Data Management System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Create and add tabs
        self.dashboard_tab = DashboardWidget(self.db)
        self.add_entry_tab = AddEntryWidget(self.db)
        self.visualizations_tab = VisualizationsWidget(self.db)
        self.chatbot_tab = ChatbotWidget(self.db)
        
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        self.tabs.addTab(self.add_entry_tab, "➕ Add Entry")
        self.tabs.addTab(self.visualizations_tab, "📈 Visualizations")
        self.tabs.addTab(self.chatbot_tab, "🤖 Chatbot")
        
        layout.addWidget(self.tabs)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Connect signals
        self.add_entry_tab.entry_added.connect(self.on_entry_added)
    
    def on_entry_added(self) -> None:
        """Handles the entry added signal.
        
        Called when a new entry is successfully added to the database.
        Updates the status bar and refreshes the dashboard and visualizations.
        """
        self.statusBar.showMessage("Entry added successfully!", 3000)
        # Refresh dashboard
        self.dashboard_tab.refresh_data()
        # Refresh visualizations
        self.visualizations_tab.refresh_data()
    
    def closeEvent(self, event) -> None:
        """Handles the window close event.
        
        Prompts the user for confirmation before closing the application.
        
        Args:
            event: QCloseEvent instance.
        """
        reply = QMessageBox.question(
            self,
            'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
