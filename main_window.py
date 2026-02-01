"""
Main Window for LCA Test Data Management System
"""

from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QStatusBar, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from widgets.dashboard_widget import DashboardWidget
from widgets.add_entry_widget import AddEntryWidget
from widgets.visualizations_widget import VisualizationsWidget
from widgets.chatbot_widget import ChatbotWidget


class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
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
    
    def on_entry_added(self):
        """Handle entry added signal"""
        self.statusBar.showMessage("Entry added successfully!", 3000)
        # Refresh dashboard
        self.dashboard_tab.refresh_data()
        # Refresh visualizations
        self.visualizations_tab.refresh_data()
    
    def closeEvent(self, event):
        """Handle window close event"""
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
