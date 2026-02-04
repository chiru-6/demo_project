"""Main window module for LCA Test Data Management System.

This module contains the MainWindow class which provides the primary user interface
with a tabbed layout for different functionalities.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMessageBox,
                             QPushButton, QStatusBar, QTabWidget, QVBoxLayout,
                             QWidget)

from widgets.add_entry_widget import AddEntryWidget
from widgets.chatbot_widget import ChatbotWidget
from widgets.dashboard_widget import DashboardWidget
from widgets.visualizations_widget import VisualizationsWidget

# Light and dark theme stylesheets (applied app-wide when toggling Dark/Light mode)
LIGHT_STYLESHEET = """
    QMainWindow, QWidget { background-color: #f5f6f8; }
    #topBar { background-color: #e8eaed; border-bottom: 1px solid #e0e2e5; }
    QTabWidget::pane { border: 1px solid #e0e2e5; border-radius: 8px; background: #ffffff; top: -1px; }
    QTabBar::tab { background: #e8eaed; color: #2d3748; padding: 10px 20px; margin-right: 4px; border-radius: 6px 6px 0 0; }
    QTabBar::tab:selected { background: #ffffff; color: #2563eb; font-weight: bold; border: 1px solid #e0e2e5; border-bottom: none; }
    QTabBar::tab:hover:!selected { background: #d1d5db; }
    QStatusBar { background: #e8eaed; color: #4b5563; }
    QLabel { color: #1f2937; }
    QPushButton { background: #e5e7eb; color: #1f2937; border: 1px solid #d1d5db; padding: 8px 16px; border-radius: 6px; }
    QPushButton:hover { background: #d1d5db; }
    QPushButton:pressed { background: #9ca3af; }
    QPushButton#darkModeBtn { background: #1f2937; color: #f9fafb; font-weight: bold; border: none; }
    QPushButton#darkModeBtn:hover { background: #374151; }
    QFrame#statsFrame { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; }
    QLabel#statCard { background: #f9fafb; color: #374151; border: 1px solid #e5e7eb; }
    QFrame#filtersPanel { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; }
    QPushButton#filterToggle { background: #4b5563; color: white; }
    QGroupBox { color: #1f2937; border: 1px solid #e5e7eb; border-radius: 6px; margin-top: 8px; font-weight: bold; }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
    QLineEdit, QTextEdit, QPlainTextEdit { background: #ffffff; color: #1f2937; border: 1px solid #d1d5db; border-radius: 6px; padding: 6px; selection-background-color: #93c5fd; }
    QComboBox { background: #ffffff; color: #1f2937; border: 1px solid #d1d5db; padding: 6px 12px; border-radius: 6px; min-height: 20px; }
    QComboBox::drop-down { border: none; background: #f3f4f6; border-radius: 0 6px 6px 0; }
    QComboBox QAbstractItemView { background: #ffffff; color: #1f2937; selection-background-color: #93c5fd; }
    QTableWidget { background: #ffffff; color: #1f2937; gridline-color: #e5e7eb; border: 1px solid #e5e7eb; }
    QTableWidget::item { padding: 6px; }
    QHeaderView::section { background: #4b5563; color: white; padding: 10px; border: none; }
    QPushButton#refreshBtn { background: #2563eb; color: white; border: none; }
    QPushButton#refreshBtn:hover { background: #1d4ed8; }
    QLabel#infoLabel { background: #dbeafe; color: #1e40af; }
    QLabel#examplesLabel { color: #6b7280; }
    QTextEdit#chatDisplay { background: #f9fafb; color: #1f2937; }
"""
DARK_STYLESHEET = """
    QMainWindow, QWidget { background-color: #1a1d23; }
    #topBar { background-color: #22262e; border-bottom: 1px solid #2d323c; }
    QTabWidget::pane { border: 1px solid #2d323c; border-radius: 8px; background: #22262e; top: -1px; }
    QTabBar::tab { background: #2d323c; color: #b0b8c4; padding: 10px 20px; margin-right: 4px; border-radius: 6px 6px 0 0; }
    QTabBar::tab:selected { background: #22262e; color: #7eb6fa; font-weight: bold; border: 1px solid #2d323c; border-bottom: none; }
    QTabBar::tab:hover:!selected { background: #363c48; }
    QStatusBar { background: #2d323c; color: #9ca3af; }
    QLabel { color: #e5e7eb; }
    QPushButton { background: #363c48; color: #e5e7eb; border: 1px solid #404552; padding: 8px 16px; border-radius: 6px; }
    QPushButton:hover { background: #404552; color: #f3f4f6; }
    QPushButton:pressed { background: #2d323c; }
    QPushButton#darkModeBtn { background: #7eb6fa; color: #1a1d23; font-weight: bold; border: none; }
    QPushButton#darkModeBtn:hover { background: #93c5fd; color: #111827; }
    #dashboardTitle { color: #e5e7eb; }
    QFrame#statsFrame { background: #2d323c; border: 1px solid #404552; border-radius: 12px; }
    QLabel#statCard { background: #363c48; color: #e5e7eb; border: 1px solid #404552; }
    QFrame#filtersPanel { background: #2d323c; border: 1px solid #404552; border-radius: 10px; }
    QPushButton#filterToggle { background: #404552; color: #e5e7eb; }
    QPushButton#filterToggle:hover { background: #4b5563; }
    QGroupBox { color: #e5e7eb; border: 1px solid #404552; border-radius: 6px; margin-top: 8px; font-weight: bold; }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #e5e7eb; }
    QLineEdit, QTextEdit, QPlainTextEdit { background: #2d323c; color: #e5e7eb; border: 1px solid #404552; border-radius: 6px; padding: 6px; selection-background-color: #4b7bd4; }
    QComboBox { background: #2d323c; color: #e5e7eb; border: 1px solid #404552; padding: 6px 12px; border-radius: 6px; min-height: 20px; }
    QComboBox:hover { border-color: #7eb6fa; }
    QComboBox::drop-down { border: none; background: #363c48; border-radius: 0 6px 6px 0; }
    QComboBox QAbstractItemView { background: #2d323c; color: #e5e7eb; selection-background-color: #4b7bd4; }
    QTableWidget { background: #2d323c; color: #e5e7eb; gridline-color: #404552; border: 1px solid #404552; }
    QTableWidget::item { padding: 6px; }
    QTableWidget::item:alternate { background: #363c48; }
    QHeaderView::section { background: #404552; color: #e5e7eb; padding: 10px; border: none; }
    QPushButton#refreshBtn { background: #4b7bd4; color: #e5e7eb; border: none; }
    QPushButton#refreshBtn:hover { background: #5b8ae4; }
    QLabel#infoLabel { background: #2d3a4a; color: #93c5fd; border: 1px solid #404552; }
    QLabel#examplesLabel { color: #9ca3af; }
    QTextEdit#chatDisplay { background: #252930; color: #e5e7eb; border: 1px solid #404552; }
    QScrollBar:vertical { background: #252930; width: 12px; border-radius: 6px; margin: 0; }
    QScrollBar::handle:vertical { background: #404552; border-radius: 6px; min-height: 24px; }
    QScrollBar::handle:vertical:hover { background: #4b5563; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


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
        self._night_mode = False
        self.init_ui()
    
    def init_ui(self) -> None:
        """Initializes the user interface.
        
        Creates and configures all UI elements including tabs, widgets,
        and status bar. Also connects signals between widgets.
        """
        self.setWindowTitle("LCA Test Data Management System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget with top bar + tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar with Dark/Light mode toggle
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(48)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(16, 8, 16, 8)
        top_bar_layout.addStretch()
        self.night_mode_btn = QPushButton("🌙 Dark mode")
        self.night_mode_btn.setObjectName("darkModeBtn")
        self.night_mode_btn.setCheckable(True)
        self.night_mode_btn.setCursor(Qt.PointingHandCursor)
        self.night_mode_btn.clicked.connect(self._toggle_night_mode)
        top_bar_layout.addWidget(self.night_mode_btn)
        layout.addWidget(top_bar)
        
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
        
        # Apply light theme by default so widgets look consistent
        QApplication.instance().setStyleSheet(LIGHT_STYLESHEET)
    
    def _toggle_night_mode(self) -> None:
        """Toggle dark/light mode and apply the corresponding stylesheet."""
        self._night_mode = self.night_mode_btn.isChecked()
        if self._night_mode:
            QApplication.instance().setStyleSheet(DARK_STYLESHEET)
            self.night_mode_btn.setText("☀️ Light mode")
        else:
            QApplication.instance().setStyleSheet(LIGHT_STYLESHEET)
            self.night_mode_btn.setText("🌙 Dark mode")
        # Redraw visualizations so chart background matches theme
        self.visualizations_tab.refresh_data()
    
    def is_dark_mode(self) -> bool:
        """Return True if dark mode is currently active."""
        return self.night_mode_btn.isChecked()
    
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
