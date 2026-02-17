"""Main window module for LCA Test Data Management System.

This module contains the MainWindow class which provides the primary user interface
with a tabbed layout for different functionalities.
"""

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .add_entry_view import AddEntryWidget
from .chatbot_view import ChatbotWidget
from .dashboard_view import DashboardWidget
from .dataset_view import DatasetWidget
from .home_view import HomeWidget
from .visualizations_view import VisualizationsWidget

# Light and dark theme stylesheets (applied app-wide when toggling Dark/Light mode)
# Light: softer background #f8fafc, accent #4f46e5, light #e0e7ff
LIGHT_STYLESHEET = """
    QMainWindow, QWidget { background-color: #f8fafc; }
    #topBar { background-color: #e8eaed; border-bottom: 1px solid #e0e2e5; }
    QTabWidget::pane { border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; top: -1px; }
    QTabBar::tab { background: #e8eaed; color: #2d3748; padding: 10px 20px; margin-right: 4px; border-radius: 6px 6px 0 0; }
    QTabBar::tab:selected { background: #ffffff; color: #4f46e5; font-weight: bold; border: 1px solid #e5e7eb; border-bottom: none; }
    QTabBar::tab:hover:!selected { background: #e0e7ff; }
    QStatusBar { background: #e8eaed; color: #4b5563; }
    QLabel { color: #1f2937; }
    QPushButton { background: #e5e7eb; color: #1f2937; border: 1px solid #d1d5db; padding: 8px 16px; border-radius: 6px; }
    QPushButton:hover { background: #e0e7ff; }
    QPushButton:pressed { background: #c7d2fe; }
    QPushButton#darkModeBtn { background: #4f46e5; color: #fff; font-weight: bold; border: none; }
    QPushButton#darkModeBtn:hover { background: #4338ca; }
    #dashboardRoot { background-color: #f8fafc; border-radius: 12px; }
    QFrame#statsFrame { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; }
    QLabel#statCard { background: #e0e7ff; color: #4f46e5; border: 1px solid #c7d2fe; border-radius: 10px; font-size: 14px; font-weight: 500; padding: 12px 18px; min-width: 180px; }
    QFrame#filtersPanel { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; }
    QPushButton#filterToggle { background: #4f46e5; color: white; }
    QGroupBox { color: #1f2937; border: 1px solid #e5e7eb; border-radius: 6px; margin-top: 8px; font-weight: bold; }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
    QLineEdit, QTextEdit, QPlainTextEdit { background: #ffffff; color: #1f2937; border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px; selection-background-color: #a5b4fc; }
    QComboBox { background: #ffffff; color: #1f2937; border: 1px solid #e5e7eb; padding: 6px 12px; border-radius: 6px; min-height: 20px; }
    QComboBox::drop-down { border: none; background: #e0e7ff; border-radius: 0 6px 6px 0; }
    QComboBox QAbstractItemView { background: #ffffff; color: #1f2937; selection-background-color: #a5b4fc; }
    QTableWidget { background: #ffffff; color: #1f2937; gridline-color: #e5e7eb; border: 1px solid #e5e7eb; }
    QTableWidget::item { padding: 6px; }
    QHeaderView::section { background: #4f46e5; color: white; padding: 10px; border: none; }
    QPushButton#refreshBtn { background: #4f46e5; color: white; border: none; }
    QPushButton#refreshBtn:hover { background: #4338ca; }
    QLabel#infoLabel { background: #e0e7ff; color: #3730a3; }
    QLabel#examplesLabel { color: #6b7280; }
    QTextEdit#chatDisplay { background: #f8fafc; color: #1f2937; }
    #sidebar { background-color: #f1f5f9; border-right: 1px solid #e2e8f0; }
    QPushButton#sidebarButton { background-color: transparent; border: none; color: #111827; font-size: 18px; padding: 6px 8px; }
    QPushButton#sidebarButton:checked { background-color: #e0e7ff; border-radius: 8px; color: #4f46e5; }
    QPushButton#sidebarButton:hover { background-color: #e0e7ff; border-radius: 8px; }
    #homeHeader { font-size: 24px; font-weight: 700; color: #1f2937; }
    #homeSubHeader { color: #6b7280; }
    QFrame#homeCard { background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; }
    #homeCardTitle { font-size: 18px; font-weight: 600; color: #1f2937; }
    #homeCardDesc { color: #6b7280; }
    QPushButton#homeCardButton { background-color: #4f46e5; color: white; border: none; padding: 6px 14px; border-radius: 6px; }
    QPushButton#homeCardButton:hover { background-color: #4338ca; }
    QFrame#insightsFrame { background-color: #e0e7ff; border-radius: 12px; padding: 8px 16px; }
    QFrame#insightCard { background-color: #ffffff; border-radius: 10px; border: 1px solid #e5e7eb; padding: 10px 12px; }
    #insightTitle { font-size: 13px; font-weight: 600; color: #374151; }
    #insightBody { font-size: 13px; color: #1f2937; }
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
    #dashboardRoot { background-color: #111827; border-radius: 12px; }
    QFrame#statsFrame { background: #2d323c; border: 1px solid #404552; border-radius: 12px; }
    QLabel#statCard { background: #363c48; color: #e5e7eb; border: 1px solid #404552; border-radius: 10px; font-size: 14px; font-weight: 500; padding: 12px 18px; min-width: 180px; }
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
    #sidebar { background-color: #111827; border-right: 1px solid #2d323c; }
    QPushButton#sidebarButton { background-color: transparent; border: none; color: #9ca3af; font-size: 18px; padding: 6px 8px; }
    QPushButton#sidebarButton:checked { background-color: #1f2937; border-radius: 8px; color: #f9fafb; }
    QPushButton#sidebarButton:hover { background-color: #1f2937; border-radius: 8px; }
    #homeHeader { font-size: 24px; font-weight: 700; color: #e5e7eb; }
    #homeSubHeader { color: #9ca3af; }
    QFrame#homeCard { background-color: #111827; border-radius: 12px; border: 1px solid #374151; }
    #homeCardTitle { font-size: 18px; font-weight: 600; color: #e5e7eb; }
    #homeCardDesc { color: #9ca3af; }
    QPushButton#homeCardButton { background-color: #4b7bd4; color: #e5e7eb; border: none; padding: 6px 14px; border-radius: 6px; }
    QPushButton#homeCardButton:hover { background-color: #5b8ae4; }
    QFrame#insightsFrame { background-color: #111827; border-radius: 12px; padding: 8px 16px; border: 1px solid #1f2937; }
    QFrame#insightCard { background-color: #1f2937; border-radius: 10px; border: 1px solid #374151; padding: 10px 12px; }
    #insightTitle { font-size: 13px; font-weight: 600; color: #9ca3af; }
    #insightBody { font-size: 13px; color: #e5e7eb; }
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
        self.setWindowTitle("Test Data Management System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget with sidebar + content
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main content area with sidebar + stacked tabs
        content_container = QHBoxLayout()
        content_container.setContentsMargins(0, 0, 0, 0)
        content_container.setSpacing(0)

        # Sidebar (hover to expand and show labels)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(64)
        self.sidebar.installEventFilter(self)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(12)

        # Sidebar buttons: Home, Dashboard, Dataset, Visualizations, Chatbot, Add Entry
        self.sidebar_buttons = []
        self._sidebar_items = [
            ("🏠", "Home"),
            ("📊", "Dashboard"),
            ("🗂", "Dataset"),
            ("📈", "Visualizations"),
            ("➕", "Add Entry"),
            ("🤖", "Chatbot"),
        ]

        for index, (icon, label) in enumerate(self._sidebar_items):
            btn = QPushButton(icon)
            btn.setObjectName("sidebarButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._on_sidebar_clicked(i))
            btn.setToolTip(label)
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)
        sidebar_layout.addStretch()

        # Dark/Light mode toggle at bottom of sidebar
        self.night_mode_btn = QPushButton("🌙")
        self.night_mode_btn.setObjectName("darkModeBtn")
        self.night_mode_btn.setCheckable(True)
        self.night_mode_btn.setCursor(Qt.PointingHandCursor)
        self.night_mode_btn.clicked.connect(self._toggle_night_mode)
        sidebar_layout.addWidget(self.night_mode_btn)

        content_container.addWidget(self.sidebar)

        # Create tab widget (used as stacked pages, tab bar hidden)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.tabBar().hide()
        
        # Create and add tabs (0: Home, 1: Dashboard, 2: Dataset, 3: Visualizations, 4: Add Entry, 5: Chatbot)
        self.home_tab = HomeWidget(self.db)
        self.dashboard_tab = DashboardWidget(self.db)
        self.dataset_tab = DatasetWidget(self.db)
        self.visualizations_tab = VisualizationsWidget(self.db)
        self.add_entry_tab = AddEntryWidget(self.db)
        self.chatbot_tab = ChatbotWidget(self.db)
        
        self.tabs.addTab(self.home_tab, "Home")
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        self.tabs.addTab(self.dataset_tab, "🗂 Dataset")
        self.tabs.addTab(self.visualizations_tab, "📈 Visualizations")
        self.tabs.addTab(self.add_entry_tab, "➕ Add Entry")
        self.tabs.addTab(self.chatbot_tab, "🤖 Chatbot")
        
        content_container.addWidget(self.tabs)
        root_layout.addLayout(content_container)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Connect signals
        self.add_entry_tab.entry_added.connect(self.on_entry_added)
        # Home: navigation and global search
        self.home_tab.go_dashboard.connect(lambda: self._on_sidebar_clicked(1))
        self.home_tab.go_dataset.connect(lambda: self._on_sidebar_clicked(2))
        self.home_tab.go_visualizations.connect(lambda: self._on_sidebar_clicked(3))
        self.home_tab.go_chatbot.connect(lambda: self._on_sidebar_clicked(5))
        self.home_tab.search_requested.connect(self._on_global_search)
        # Dashboard: open dataset with filter when insight card clicked
        self.dashboard_tab.open_dataset_filtered.connect(self._on_open_dataset_filtered)

        # Select Home by default
        if self.sidebar_buttons:
            self.sidebar_buttons[0].setChecked(True)
        self.tabs.setCurrentIndex(0)
        
        # Apply light theme by default so widgets look consistent
        QApplication.instance().setStyleSheet(LIGHT_STYLESHEET)
    
    def _on_sidebar_clicked(self, index: int) -> None:
        """Handle sidebar navigation clicks and keep only one button checked."""
        self.tabs.setCurrentIndex(index)
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)

    def _on_global_search(self, text: str) -> None:
        """Switch to Dataset tab and apply global search filter."""
        self._on_sidebar_clicked(2)
        self.dataset_tab.set_filter_and_search(search_text=text)

    def _on_open_dataset_filtered(self, project: str, test_rig: str) -> None:
        """Switch to Dataset tab and set project/test_rig filters."""
        self._on_sidebar_clicked(2)
        self.dataset_tab.set_filter_and_search(project=project, test_rig=test_rig)

    def eventFilter(self, obj, event):  # type: ignore[override]
        """Expand/collapse sidebar on hover."""
        if obj is self.sidebar:
            if event.type() == QEvent.Enter:
                self._expand_sidebar()
            elif event.type() == QEvent.Leave:
                self._collapse_sidebar()
        return super().eventFilter(obj, event)

    def _expand_sidebar(self) -> None:
        """Show labels and widen sidebar."""
        self.sidebar.setFixedWidth(200)
        for btn, (icon, label) in zip(self.sidebar_buttons, self._sidebar_items):
            btn.setText(f"{icon}  {label}")
            btn.setStyleSheet("text-align: left; padding-left: 8px;")

    def _collapse_sidebar(self) -> None:
        """Hide labels and shrink sidebar."""
        self.sidebar.setFixedWidth(64)
        for btn, (icon, _) in zip(self.sidebar_buttons, self._sidebar_items):
            btn.setText(icon)
            btn.setStyleSheet("")
    
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
        Updates the status bar, recent activity, and refreshes dashboard/visualizations.
        """
        self.statusBar.showMessage("Entry added successfully!", 3000)
        self.home_tab.add_recent_activity("✔ New test added")
        self.dashboard_tab.refresh_data()
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
