"""Dataset view: raw test data table with filters."""

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DatasetWidget(QWidget):
    """Dataset widget showing all test data with filters and a table view."""

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self.df = pd.DataFrame()
        self._filters_visible = True
        self._search_text = ""
        self.init_ui()
        self.refresh_data()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("🗂 Dataset — Raw Test Data")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; padding: 8px 0; letter-spacing: 0.5px;"
        )
        layout.addWidget(title)
        self.filter_toggle_btn = QPushButton("▼ Hide Filters")
        self.filter_toggle_btn.setObjectName("filterToggle")
        self.filter_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.filter_toggle_btn.clicked.connect(self._toggle_filters)
        layout.addWidget(self.filter_toggle_btn)
        self.filters_panel = QFrame()
        self.filters_panel.setObjectName("filtersPanel")
        filters_layout = QHBoxLayout(self.filters_panel)
        filters_layout.setContentsMargins(16, 14, 16, 14)
        filters_layout.setSpacing(16)
        filters_layout.addWidget(QLabel("Project:"))
        self.project_filter = QComboBox()
        self.project_filter.setMinimumWidth(160)
        self.project_filter.addItem("All")
        self.project_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.project_filter)
        filters_layout.addWidget(QLabel("Test Rig:"))
        self.rig_filter = QComboBox()
        self.rig_filter.setMinimumWidth(160)
        self.rig_filter.addItem("All")
        self.rig_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.rig_filter)
        filters_layout.addWidget(QLabel("Results:"))
        self.results_filter = QComboBox()
        self.results_filter.setMinimumWidth(140)
        self.results_filter.addItem("All")
        self.results_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.results_filter)
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        filters_layout.addWidget(refresh_btn)
        filters_layout.addStretch()
        layout.addWidget(self.filters_panel)
        self.table = QTableWidget()
        self.table.setObjectName("dashboardTable")
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        layout.addWidget(self.table)

    def _toggle_filters(self) -> None:
        self._filters_visible = not self._filters_visible
        self.filters_panel.setVisible(self._filters_visible)
        self.filter_toggle_btn.setText(
            "▼ Hide Filters" if self._filters_visible else "▶ Show Filters"
        )

    def refresh_data(self) -> None:
        try:
            self.df = self.db.get_all_data()
            if self.df.empty:
                QMessageBox.information(
                    self, "No Data", "No data found in the database."
                )
                return
            self._update_filters()
            self.apply_filters()
        except Exception as error:
            QMessageBox.critical(
                self, "Error", f"Error loading data: {str(error)}"
            )

    def _update_filters(self) -> None:
        self.project_filter.clear()
        self.project_filter.addItem("All")
        if "project" in self.df.columns:
            projects = sorted(self.df["project"].dropna().unique().tolist())
            self.project_filter.addItems(projects)
        self.rig_filter.clear()
        self.rig_filter.addItem("All")
        if "test_rig" in self.df.columns:
            rigs = sorted(self.df["test_rig"].dropna().unique().tolist())
            self.rig_filter.addItems(rigs)
        self.results_filter.clear()
        self.results_filter.addItem("All")
        if "results_remarks" in self.df.columns:
            results = sorted(
                self.df["results_remarks"].dropna().unique().tolist()
            )
            self.results_filter.addItems(results)

    def apply_filters(self) -> None:
        if self.df.empty:
            return
        filtered_df = self.df.copy()
        if self.project_filter.currentText() != "All":
            filtered_df = filtered_df[
                filtered_df["project"] == self.project_filter.currentText()
            ]
        if self.rig_filter.currentText() != "All":
            filtered_df = filtered_df[
                filtered_df["test_rig"] == self.rig_filter.currentText()
            ]
        if self.results_filter.currentText() != "All":
            filtered_df = filtered_df[
                filtered_df["results_remarks"]
                == self.results_filter.currentText()
            ]
        if self._search_text:
            q = self._search_text.lower()
            mask = pd.Series(False, index=filtered_df.index)
            for col in ("project", "test_rig", "type_of_test"):
                if col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.lower().str.contains(
                        q, na=False
                    )
            filtered_df = filtered_df[mask]
        self._populate_table(filtered_df)

    def set_filter_and_search(
        self,
        project: str = "",
        test_rig: str = "",
        search_text: str = "",
    ) -> None:
        """Set filters and/or global search, refresh data, and apply. Call when switching from Home/Dashboard."""
        self._search_text = (search_text or "").strip()
        self.refresh_data()
        if project and self.project_filter.findText(project) >= 0:
            self.project_filter.setCurrentText(project)
        if test_rig and self.rig_filter.findText(test_rig) >= 0:
            self.rig_filter.setCurrentText(test_rig)
        self.apply_filters()

    def _populate_table(self, df: pd.DataFrame) -> None:
        display_df = df.drop(
            columns=["id", "created_at", "updated_at"], errors="ignore"
        )
        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(len(display_df.columns))
        headers = [col.replace("_", " ").title() for col in display_df.columns]
        self.table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(display_df.itertuples(index=False)):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()
