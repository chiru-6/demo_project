"""Dashboard widget module for displaying and filtering test data.

This module provides the DashboardWidget class which displays all test data
in a table format with filtering capabilities and summary statistics.
"""

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QHeaderView, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)


class DashboardWidget(QWidget):
    """Dashboard widget showing all test data with filters.
    
    This widget provides a comprehensive view of all test data with:
        - Summary statistics (total records, projects, test rigs, OK results)
        - Filtering by project, test rig, and results
        - Sortable data table
        - Refresh functionality
    
    Attributes:
        db: DatabaseManager instance for database operations.
        df: DataFrame containing all test data.
        total_label: QLabel displaying total records count.
        projects_label: QLabel displaying unique projects count.
        rigs_label: QLabel displaying unique test rigs count.
        ok_label: QLabel displaying OK results ratio.
        project_filter: QComboBox for filtering by project.
        rig_filter: QComboBox for filtering by test rig.
        results_filter: QComboBox for filtering by results.
        table: QTableWidget displaying the filtered data.
    """
    
    def __init__(self, db) -> None:
        """Initializes the dashboard widget.
        
        Args:
            db: DatabaseManager instance for database operations.
        """
        super().__init__()
        self.db = db
        self.df = pd.DataFrame()
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self) -> None:
        """Initializes the user interface.
        
        Creates and configures all UI elements including title, statistics labels,
        filter dropdowns, and data table.
        """
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📊 Dashboard - Test Data Overview")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Statistics row
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("Total Records: 0")
        self.projects_label = QLabel("Projects: 0")
        self.rigs_label = QLabel("Test Rigs: 0")
        self.ok_label = QLabel("OK Results: 0")
        
        stat_labels = [self.total_label, self.projects_label, 
                      self.rigs_label, self.ok_label]
        for label in stat_labels:
            label.setStyleSheet(
                "font-size: 14px; padding: 5px; "
                "background-color: #f0f0f0; border-radius: 5px;"
            )
            stats_layout.addWidget(label)
        
        layout.addLayout(stats_layout)
        
        # Filters
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Filter by Project:"))
        self.project_filter = QComboBox()
        self.project_filter.addItem("All")
        self.project_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.project_filter)
        
        filters_layout.addWidget(QLabel("Filter by Test Rig:"))
        self.rig_filter = QComboBox()
        self.rig_filter.addItem("All")
        self.rig_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.rig_filter)
        
        filters_layout.addWidget(QLabel("Filter by Results:"))
        self.results_filter = QComboBox()
        self.results_filter.addItem("All")
        self.results_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.results_filter)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        filters_layout.addWidget(refresh_btn)
        
        layout.addLayout(filters_layout)
        
        # Data table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
    
    def refresh_data(self) -> None:
        """Refreshes data from database.
        
        Loads all data from the database, updates statistics labels,
        refreshes filter options, and applies current filters to the table.
        
        Displays a message box if no data is found or if an error occurs.
        """
        try:
            self.df = self.db.get_all_data()
            
            if self.df.empty:
                QMessageBox.information(
                    self, 
                    "No Data", 
                    "No data found in the database."
                )
                return
            
            # Update statistics
            stats = self.db.get_statistics()
            total_records = stats.get('total_records', 0)
            projects_count = len(stats.get('projects', {}))
            rigs_count = len(stats.get('test_rigs', {}))
            ok_count = stats.get('results', {}).get('OK', 0)
            not_ok_count = stats.get('results', {}).get('NOT OK', 0)
            
            self.total_label.setText(f"Total Records: {total_records}")
            self.projects_label.setText(f"Projects: {projects_count}")
            self.rigs_label.setText(f"Test Rigs: {rigs_count}")
            self.ok_label.setText(f"OK Results: {ok_count}/{ok_count + not_ok_count}")
            
            # Update filter dropdowns
            self.update_filters()
            
            # Apply filters and update table
            self.apply_filters()
            
        except Exception as error:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error loading data: {str(error)}"
            )
    
    def update_filters(self) -> None:
        """Updates filter dropdown options.
        
        Populates the filter dropdowns with unique values from the current
        dataset for projects, test rigs, and results.
        """
        # Projects
        self.project_filter.clear()
        self.project_filter.addItem("All")
        if 'project' in self.df.columns:
            projects = sorted(self.df['project'].dropna().unique().tolist())
            self.project_filter.addItems(projects)
        
        # Test Rigs
        self.rig_filter.clear()
        self.rig_filter.addItem("All")
        if 'test_rig' in self.df.columns:
            rigs = sorted(self.df['test_rig'].dropna().unique().tolist())
            self.rig_filter.addItems(rigs)
        
        # Results
        self.results_filter.clear()
        self.results_filter.addItem("All")
        if 'results_remarks' in self.df.columns:
            results = sorted(self.df['results_remarks'].dropna().unique().tolist())
            self.results_filter.addItems(results)
    
    def apply_filters(self) -> None:
        """Applies filters to the data table.
        
        Filters the data based on selected values in the filter dropdowns
        and updates the table display.
        """
        if self.df.empty:
            return
        
        filtered_df = self.df.copy()
        
        # Apply project filter
        if self.project_filter.currentText() != "All":
            filtered_df = filtered_df[
                filtered_df['project'] == self.project_filter.currentText()
            ]
        
        # Apply test rig filter
        if self.rig_filter.currentText() != "All":
            filtered_df = filtered_df[
                filtered_df['test_rig'] == self.rig_filter.currentText()
            ]
        
        # Apply results filter
        if self.results_filter.currentText() != "All":
            filtered_df = filtered_df[
                filtered_df['results_remarks'] == self.results_filter.currentText()
            ]
        
        # Update table
        self.populate_table(filtered_df)
    
    def populate_table(self, df: pd.DataFrame) -> None:
        """Populates table with dataframe.
        
        Args:
            df: DataFrame containing the data to display.
        """
        # Remove internal columns
        display_df = df.drop(
            columns=['id', 'created_at', 'updated_at'], 
            errors='ignore'
        )
        
        # Set table dimensions
        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(len(display_df.columns))
        
        # Set headers
        headers = [col.replace('_', ' ').title() for col in display_df.columns]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Populate data
        for i, row in enumerate(display_df.itertuples(index=False)):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, item)
        
        # Resize columns
        self.table.resizeColumnsToContents()
