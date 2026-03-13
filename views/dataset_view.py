"""Dataset view: raw test data table with filters, LRU detail panel, and Add Entry popup."""

import os

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .add_entry_comprehensive import ComprehensiveAddEntryWidget
from .dataset_relations_panel import DatasetRelationsPanel
from .lru_detail_panel import LRUDetailPanel


class _TableWithOverlayButton(QWidget):
    """Table widget with a floating Add Entry button overlayed at bottom-right (no extra row)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.add_entry_btn = QPushButton("+")
        self.add_entry_btn.setObjectName("floatingAddBtn")
        self.add_entry_btn.setFixedSize(52, 52)
        self.add_entry_btn.setCursor(Qt.PointingHandCursor)
        self.add_entry_btn.setStyleSheet(
            "#floatingAddBtn { background-color: #4f46e5; color: white; "
            "border-radius: 26px; font-size: 26px; font-weight: bold; border: none; "
            "padding: 0; min-width: 52px; min-height: 52px; max-width: 52px; max-height: 52px; }"
            "#floatingAddBtn:hover { background-color: #4338ca; }"
        )
        self.add_entry_btn.setParent(self)
        self.add_entry_btn.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = 16
        self.add_entry_btn.move(
            self.width() - self.add_entry_btn.width() - margin,
            self.height() - self.add_entry_btn.height() - margin,
        )


class AddEntryPopup(QWidget):
    """Resizable popup window for Add Entry form."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add New Entry")
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
        )
        self.setMinimumSize(520, 500)
        self.resize(600, 700)
        layout = QVBoxLayout(self)
        self.form = ComprehensiveAddEntryWidget(db)
        layout.addWidget(self.form)
        self.form.entry_added.connect(self._on_entry_added)

    def _on_entry_added(self):
        self.form.clear_form()
        self.close()

    def closeEvent(self, event):
        """Clear form when popup is closed (with or without adding)."""
        self.form.clear_form()
        event.accept()


class DatasetWidget(QWidget):
    """Dataset widget: table with filters, clickable LRU details, Add Entry popup."""

    # CSV column name variants for filtering (dataset.csv uses "Project", db uses "project")
    _COL_PROJECT = ("project", "Project")
    _COL_TEST_RIG = ("test_rig", "Test Rig")
    _COL_RESULTS = ("results_remarks", "Results & Remarks")
    _COL_LRU = ("lru_name", "LRU Name")
    _COL_TYPE_OF_TEST = ("type_of_test", "Type of Test")

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.df = pd.DataFrame()
        self._csv_path = None
        self._filters_visible = True
        self._search_text = ""
        self.entry_added_signal = None
        self._add_entry_popup = None

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(20, 10, 20, 20)

        # Header: title + filter toggle (tight spacing so no big gap when filters are collapsed)
        header = QWidget()
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        title = QLabel("🗂 Dataset — Raw Test Data")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; padding: 12px 0; letter-spacing: 0.5px;"
        )
        header_layout.addWidget(title)
        self.filter_toggle_btn = QPushButton("▼ Hide Filters")
        self.filter_toggle_btn.setObjectName("filterToggle")
        self.filter_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.filter_toggle_btn.clicked.connect(self._toggle_filters)
        header_layout.addWidget(self.filter_toggle_btn)
        layout.addWidget(header)

        # Filters panel
        self.filters_panel = QFrame()
        self.filters_panel.setObjectName("filtersPanel")
        self.filters_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        fl = QHBoxLayout(self.filters_panel)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(16)

        fl.addWidget(QLabel("Project:"))
        self.project_filter = QComboBox()
        self.project_filter.setMinimumWidth(160)
        self.project_filter.addItem("All")
        self.project_filter.currentTextChanged.connect(self.apply_filters)
        fl.addWidget(self.project_filter)
        pb = QPushButton("✕")
        pb.setFixedSize(24, 24)
        pb.setToolTip("Reset Project filter")
        pb.setObjectName("filterResetBtn")
        pb.clicked.connect(lambda: self._reset_filter("project"))
        fl.addWidget(pb)

        fl.addWidget(QLabel("Test Rig:"))
        self.rig_filter = QComboBox()
        self.rig_filter.setMinimumWidth(160)
        self.rig_filter.addItem("All")
        self.rig_filter.currentTextChanged.connect(self.apply_filters)
        fl.addWidget(self.rig_filter)
        rb = QPushButton("✕")
        rb.setFixedSize(24, 24)
        rb.setToolTip("Reset Test Rig filter")
        rb.setObjectName("filterResetBtn")
        rb.clicked.connect(lambda: self._reset_filter("rig"))
        fl.addWidget(rb)

        fl.addWidget(QLabel("Results:"))
        self.results_filter = QComboBox()
        self.results_filter.setMinimumWidth(140)
        self.results_filter.addItem("All")
        self.results_filter.currentTextChanged.connect(self.apply_filters)
        fl.addWidget(self.results_filter)
        resb = QPushButton("✕")
        resb.setFixedSize(24, 24)
        resb.setToolTip("Reset Results filter")
        resb.setObjectName("filterResetBtn")
        resb.clicked.connect(lambda: self._reset_filter("results"))
        fl.addWidget(resb)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        fl.addWidget(refresh_btn)
        fl.addStretch()
        layout.addWidget(self.filters_panel)

        # Tabs: Raw Data | Relations & Analytics
        self.content_tabs = QTabWidget()
        self.content_tabs.setObjectName("datasetTabs")

        # Tab 1: Raw Data (table | LRU detail)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        left = _TableWithOverlayButton()
        self.table = left.table
        self.table.setObjectName("dashboardTable")
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.add_entry_btn = left.add_entry_btn
        self.add_entry_btn.clicked.connect(self._open_add_entry)
        splitter.addWidget(left)
        self.detail_panel = LRUDetailPanel(self.db)
        self.detail_panel.setMaximumWidth(0)
        self.detail_panel.setVisible(False)
        self.detail_panel.close_btn.clicked.connect(self._hide_detail_panel)
        self.detail_panel.minimize_btn.clicked.connect(self._hide_detail_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        self.content_tabs.addTab(splitter, "📋 Raw Data")

        # Tab 2: Relations & Analytics (entity tables, sub-tables, pivots)
        self.relations_panel = DatasetRelationsPanel()
        self.content_tabs.addTab(self.relations_panel, "🔗 Relations & Analytics")

        layout.addWidget(self.content_tabs, 1)

        self.refresh_data()

    def _open_add_entry(self):
        if self._add_entry_popup is None:
            self._add_entry_popup = AddEntryPopup(self.db, self)
            self._add_entry_popup.form.entry_added.connect(self._on_entry_added)
        self._add_entry_popup.form.clear_form()
        self._add_entry_popup.form._populate_dropdowns()
        # Ensure LRU combo starts empty (placeholder visible)
        self._add_entry_popup.form.lru_name_combo.setCurrentIndex(-1)
        self._add_entry_popup.form.lru_name_combo.lineEdit().clear()
        self._add_entry_popup.show()
        self._add_entry_popup.raise_()
        self._add_entry_popup.activateWindow()

    def _on_entry_added(self):
        self.refresh_data()
        if self.entry_added_signal:
            self.entry_added_signal.emit()

    def _on_cell_clicked(self, row, col):
        col_lru = self._col(self._COL_LRU)
        if not col_lru:
            return
        idx = list(self.df.columns).index(col_lru) if col_lru in self.df.columns else -1
        if idx < 0 or col != idx:
            return
        item = self.table.item(row, col)
        if not item:
            return
        lru_name = item.text()
        self.detail_panel.show_lru(lru_name)
        self.detail_panel.setVisible(True)
        self.detail_panel.setMaximumWidth(400)
        # Also update Relations tab with LRU filter
        self.relations_panel.set_filter("LRU Name", lru_name)

    def _hide_detail_panel(self):
        self.detail_panel.setMaximumWidth(0)
        self.detail_panel.setVisible(False)

    def _reset_filter(self, which):
        if which == "project":
            self.project_filter.setCurrentText("All")
        elif which == "rig":
            self.rig_filter.setCurrentText("All")
        elif which == "results":
            self.results_filter.setCurrentText("All")
        self.apply_filters()

    def _toggle_filters(self):
        self._filters_visible = not self._filters_visible
        self.filters_panel.setVisible(self._filters_visible)
        self.filter_toggle_btn.setText(
            "▼ Hide Filters" if self._filters_visible else "▶ Show Filters"
        )

    def _get_csv_path(self):
        """Return path to dataset.csv or LCA_Test_Data.csv in project directory."""
        project_dir = os.path.dirname(os.path.abspath(self.db.db_path))
        for name in ("dataset.csv", "LCA_Test_Data.csv"):
            p = os.path.join(project_dir, name)
            if os.path.exists(p):
                return p
        return None

    def _load_from_csv(self):
        """Load data live from dataset.csv. Returns DataFrame or empty."""
        csv_path = self._get_csv_path()
        if not csv_path:
            return pd.DataFrame()
        self._csv_path = csv_path
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        return df

    def _col(self, choices):
        """Return first column name that exists in df, from choices."""
        for c in choices:
            if c in self.df.columns:
                return c
        return None

    def refresh_data(self):
        """Load data live from dataset.csv (reflects file changes)."""
        try:
            self.df = self._load_from_csv()
            if self.df.empty:
                QMessageBox.information(
                    self, "No Data",
                    "No dataset.csv or LCA_Test_Data.csv found, or file is empty."
                )
                return
            self._update_filters()
            self.apply_filters()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading data: {str(e)}")

    def _update_filters(self):
        self.project_filter.clear()
        self.project_filter.addItem("All")
        col = self._col(self._COL_PROJECT)
        if col:
            self.project_filter.addItems(
                sorted(self.df[col].dropna().unique().astype(str).tolist())
            )
        self.rig_filter.clear()
        self.rig_filter.addItem("All")
        col = self._col(self._COL_TEST_RIG)
        if col:
            self.rig_filter.addItems(
                sorted(self.df[col].dropna().unique().astype(str).tolist())
            )
        self.results_filter.clear()
        self.results_filter.addItem("All")
        col = self._col(self._COL_RESULTS)
        if col:
            self.results_filter.addItems(
                sorted(self.df[col].dropna().unique().astype(str).tolist())
            )

    def apply_filters(self):
        if self.df.empty:
            return
        df = self.df.copy()
        col_p = self._col(self._COL_PROJECT)
        if col_p and self.project_filter.currentText() != "All":
            df = df[df[col_p].astype(str) == self.project_filter.currentText()]
        col_r = self._col(self._COL_TEST_RIG)
        if col_r and self.rig_filter.currentText() != "All":
            df = df[df[col_r].astype(str) == self.rig_filter.currentText()]
        col_res = self._col(self._COL_RESULTS)
        if col_res and self.results_filter.currentText() != "All":
            df = df[df[col_res].astype(str) == self.results_filter.currentText()]
        if self._search_text:
            q = self._search_text.lower()
            mask = pd.Series(False, index=df.index)
            for choices in (self._COL_PROJECT, self._COL_TEST_RIG, self._COL_TYPE_OF_TEST):
                col = self._col(choices)
                if col and col in df.columns:
                    mask |= df[col].astype(str).str.lower().str.contains(q, na=False)
            df = df[mask]
        self._populate_table(df)
        self.relations_panel.set_data(df)

    def set_filter_and_search(self, project="", test_rig="", search_text=""):
        self._search_text = (search_text or "").strip()
        self.refresh_data()
        if project and self.project_filter.findText(project) >= 0:
            self.project_filter.setCurrentText(project)
        if test_rig and self.rig_filter.findText(test_rig) >= 0:
            self.rig_filter.setCurrentText(test_rig)
        self.apply_filters()

    def _populate_table(self, df):
        """Populate table with all columns from df (live from dataset.csv)."""
        display_df = df.copy()
        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(len(display_df.columns))
        self.table.setHorizontalHeaderLabels(list(display_df.columns))
        col_lru = self._col(self._COL_LRU)
        lru_idx = list(display_df.columns).index(col_lru) if col_lru and col_lru in display_df.columns else None
        for i, row in enumerate(display_df.itertuples(index=False)):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if pd.notna(val) else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if lru_idx is not None and j == lru_idx:
                    font = QFont()
                    font.setUnderline(True)
                    item.setFont(font)
                    item.setForeground(Qt.GlobalColor.blue)
                    item.setToolTip("Click to view LRU details")
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()
        # Ensure date columns are clearly visible (min width for dates)
        for date_col in ("date_of_clearance", "Date of Clearance", "date_of_pi", "Date of PI"):
            if date_col in display_df.columns:
                col_idx = list(display_df.columns).index(date_col)
                self.table.setColumnWidth(col_idx, max(120, self.table.columnWidth(col_idx)))
