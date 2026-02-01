"""
Dashboard Widget - Display and filter test data
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
import pandas as pd


class DashboardWidget(QWidget):
    """Dashboard widget showing all test data with filters"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize the UI"""
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
        
        for label in [self.total_label, self.projects_label, self.rigs_label, self.ok_label]:
            label.setStyleSheet("font-size: 14px; padding: 5px; background-color: #f0f0f0; border-radius: 5px;")
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
    
    def refresh_data(self):
        """Refresh data from database"""
        try:
            self.df = self.db.get_all_data()
            
            if self.df.empty:
                QMessageBox.information(self, "No Data", "No data found in the database.")
                return
            
            # Update statistics
            stats = self.db.get_statistics()
            self.total_label.setText(f"Total Records: {stats.get('total_records', 0)}")
            self.projects_label.setText(f"Projects: {len(stats.get('projects', {}))}")
            self.rigs_label.setText(f"Test Rigs: {len(stats.get('test_rigs', {}))}")
            ok_count = stats.get('results', {}).get('OK', 0)
            not_ok_count = stats.get('results', {}).get('NOT OK', 0)
            self.ok_label.setText(f"OK Results: {ok_count}/{ok_count + not_ok_count}")
            
            # Update filter dropdowns
            self.update_filters()
            
            # Apply filters and update table
            self.apply_filters()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading data: {str(e)}")
    
    def update_filters(self):
        """Update filter dropdown options"""
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
    
    def apply_filters(self):
        """Apply filters to the data table"""
        if self.df.empty:
            return
        
        filtered_df = self.df.copy()
        
        # Apply project filter
        if self.project_filter.currentText() != "All":
            filtered_df = filtered_df[filtered_df['project'] == self.project_filter.currentText()]
        
        # Apply test rig filter
        if self.rig_filter.currentText() != "All":
            filtered_df = filtered_df[filtered_df['test_rig'] == self.rig_filter.currentText()]
        
        # Apply results filter
        if self.results_filter.currentText() != "All":
            filtered_df = filtered_df[filtered_df['results_remarks'] == self.results_filter.currentText()]
        
        # Update table
        self.populate_table(filtered_df)
    
    def populate_table(self, df):
        """Populate table with dataframe"""
        # Remove internal columns
        display_df = df.drop(columns=['id', 'created_at', 'updated_at'], errors='ignore')
        
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
