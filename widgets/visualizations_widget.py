"""
Visualizations Widget - Charts and graphs for data analysis
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd


class VisualizationsWidget(QWidget):
    """Widget for displaying data visualizations"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.df = pd.DataFrame()
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📈 Data Visualizations")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Select Visualization:"))
        self.viz_combo = QComboBox()
        self.viz_combo.addItems([
            "Results Distribution",
            "Test Rigs Analysis",
            "Projects Overview",
            "Division/Group Distribution",
            "Type of Test Analysis",
            "Clearance Status"
        ])
        self.viz_combo.currentTextChanged.connect(self.update_visualization)
        controls_layout.addWidget(self.viz_combo)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(refresh_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
    
    def refresh_data(self):
        """Refresh data from database"""
        try:
            self.df = self.db.get_all_data()
            self.update_visualization()
        except Exception as e:
            self.show_error_plot(str(e))
    
    def update_visualization(self):
        """Update the current visualization"""
        if self.df.empty:
            self.show_error_plot("No data available")
            return
        
        viz_type = self.viz_combo.currentText()
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        try:
            if viz_type == "Results Distribution":
                self.plot_results_distribution(ax)
            elif viz_type == "Test Rigs Analysis":
                self.plot_test_rigs(ax)
            elif viz_type == "Projects Overview":
                self.plot_projects(ax)
            elif viz_type == "Division/Group Distribution":
                self.plot_divisions(ax)
            elif viz_type == "Type of Test Analysis":
                self.plot_test_types(ax)
            elif viz_type == "Clearance Status":
                self.plot_clearance_status(ax)
            
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            self.show_error_plot(f"Error creating visualization: {str(e)}")
    
    def plot_results_distribution(self, ax):
        """Plot pie chart of results distribution"""
        results_counts = self.df['results_remarks'].value_counts()
        colors = ['#2ecc71' if 'OK' in str(idx) else '#e74c3c' for idx in results_counts.index]
        ax.pie(results_counts.values, labels=results_counts.index, autopct='%1.1f%%', 
               colors=colors, startangle=90)
        ax.set_title("Test Results Distribution", fontsize=16, fontweight='bold')
    
    def plot_test_rigs(self, ax):
        """Plot bar chart of test rigs"""
        rig_counts = self.df['test_rig'].value_counts()
        ax.bar(range(len(rig_counts)), rig_counts.values, color='#3498db')
        ax.set_xticks(range(len(rig_counts)))
        ax.set_xticklabels(rig_counts.index, rotation=45, ha='right')
        ax.set_ylabel("Count", fontsize=12)
        ax.set_title("Test Rigs Usage", fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    def plot_projects(self, ax):
        """Plot bar chart of projects"""
        project_counts = self.df['project'].value_counts()
        ax.bar(range(len(project_counts)), project_counts.values, color='#9b59b6')
        ax.set_xticks(range(len(project_counts)))
        ax.set_xticklabels(project_counts.index)
        ax.set_ylabel("Count", fontsize=12)
        ax.set_title("Projects Distribution", fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    def plot_divisions(self, ax):
        """Plot pie chart of divisions"""
        div_counts = self.df['division_group'].value_counts()
        ax.pie(div_counts.values, labels=div_counts.index, autopct='%1.1f%%', startangle=90)
        ax.set_title("Division/Group Distribution", fontsize=16, fontweight='bold')
    
    def plot_test_types(self, ax):
        """Plot bar chart of test types"""
        test_counts = self.df['type_of_test'].value_counts()
        ax.bar(range(len(test_counts)), test_counts.values, color='#e67e22')
        ax.set_xticks(range(len(test_counts)))
        ax.set_xticklabels(test_counts.index, rotation=45, ha='right')
        ax.set_ylabel("Count", fontsize=12)
        ax.set_title("Type of Test Distribution", fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    def plot_clearance_status(self, ax):
        """Plot bar chart of clearance status"""
        cleared = self.df['date_of_clearance'].notna().sum()
        not_cleared = self.df['date_of_clearance'].isna().sum()
        
        ax.bar(['Cleared', 'Not Cleared'], [cleared, not_cleared], 
               color=['#2ecc71', '#f39c12'])
        ax.set_ylabel("Count", fontsize=12)
        ax.set_title("Clearance Status", fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    def show_error_plot(self, message):
        """Show error message on plot"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14)
        ax.axis('off')
        self.canvas.draw()
