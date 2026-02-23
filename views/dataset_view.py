"""Dataset view: raw test data table with filters, LRU detail panel, and Add Entry popup."""

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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .add_entry_comprehensive import ComprehensiveAddEntryWidget
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
        self.add_entry_btn.setFixedSize(56, 56)
        self.add_entry_btn.setCursor(Qt.PointingHandCursor)
        self.add_entry_btn.setStyleSheet(
            "#floatingAddBtn { background-color: #4f46e5; color: white; "
            "border-radius: 28px; font-size: 28px; border: none; padding: 0; }"
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
        self.form.entry_added.connect(self.close)


class DatasetWidget(QWidget):
    """Dataset widget: table with filters, clickable LRU details, Add Entry popup."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.df = pd.DataFrame()
        self._filters_visible = True
        self._search_text = ""
        self.entry_added_signal = None

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

        # Content: splitter (table | LRU detail)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: table with Add Entry button overlayed at bottom-right (no extra row)
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

        # Right: LRU detail panel (hidden by default)
        self.detail_panel = LRUDetailPanel(self.db)
        self.detail_panel.setMaximumWidth(0)
        self.detail_panel.setVisible(False)
        self.detail_panel.close_btn.clicked.connect(self._hide_detail_panel)
        self.detail_panel.minimize_btn.clicked.connect(self._hide_detail_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        self.refresh_data()

    def _open_add_entry(self):
        popup = AddEntryPopup(self.db, self)
        popup.form.entry_added.connect(self._on_entry_added)
        popup.show()

    def _on_entry_added(self):
        self.refresh_data()
        if self.entry_added_signal:
            self.entry_added_signal.emit()

    def _on_cell_clicked(self, row, col):
        h = []
        for i in range(self.table.columnCount()):
            hi = self.table.horizontalHeaderItem(i)
            if hi:
                h.append(hi.text().lower().replace(" ", "_"))
        if "lru_name" not in h:
            return
        idx = h.index("lru_name")
        if col != idx:
            return
        item = self.table.item(row, col)
        if not item:
            return
        self.detail_panel.show_lru(item.text())
        self.detail_panel.setVisible(True)
        self.detail_panel.setMaximumWidth(400)

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

    def refresh_data(self):
        try:
            self.df = self.db.get_all_data()
            if self.df.empty:
                QMessageBox.information(self, "No Data", "No data found in the database.")
                return
            self._update_filters()
            self.apply_filters()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading data: {str(e)}")

    def _update_filters(self):
        self.project_filter.clear()
        self.project_filter.addItem("All")
        if "project" in self.df.columns:
            self.project_filter.addItems(
                sorted(self.df["project"].dropna().unique().tolist())
            )
        self.rig_filter.clear()
        self.rig_filter.addItem("All")
        if "test_rig" in self.df.columns:
            self.rig_filter.addItems(
                sorted(self.df["test_rig"].dropna().unique().tolist())
            )
        self.results_filter.clear()
        self.results_filter.addItem("All")
        if "results_remarks" in self.df.columns:
            self.results_filter.addItems(
                sorted(self.df["results_remarks"].dropna().unique().tolist())
            )

    def apply_filters(self):
        if self.df.empty:
            return
        df = self.df.copy()
        if self.project_filter.currentText() != "All":
            df = df[df["project"] == self.project_filter.currentText()]
        if self.rig_filter.currentText() != "All":
            df = df[df["test_rig"] == self.rig_filter.currentText()]
        if self.results_filter.currentText() != "All":
            df = df[df["results_remarks"] == self.results_filter.currentText()]
        if self._search_text:
            q = self._search_text.lower()
            mask = pd.Series(False, index=df.index)
            for c in ("project", "test_rig", "type_of_test"):
                if c in df.columns:
                    mask |= df[c].astype(str).str.lower().str.contains(q, na=False)
            df = df[mask]
        self._populate_table(df)

    def set_filter_and_search(self, project="", test_rig="", search_text=""):
        self._search_text = (search_text or "").strip()
        self.refresh_data()
        if project and self.project_filter.findText(project) >= 0:
            self.project_filter.setCurrentText(project)
        if test_rig and self.rig_filter.findText(test_rig) >= 0:
            self.rig_filter.setCurrentText(test_rig)
        self.apply_filters()

    # Columns to show (match dataset.csv / datasheet); hide lru_category and all columns to the right
    DATASHEET_COLUMNS = [
        "lru_name", "project", "division_group", "system", "part_number",
        "serial_no", "received_data", "type_of_test", "test_rig",
        "date_of_pi", "results_remarks", "date_of_clearance",
    ]

    def _populate_table(self, df):
        drop = ["id", "created_at", "updated_at"]
        display_df = df.drop(columns=drop, errors="ignore")
        # Keep only datasheet columns (same as dataset.csv)
        keep = [c for c in self.DATASHEET_COLUMNS if c in display_df.columns]
        display_df = display_df[keep]
        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(len(display_df.columns))
        self.table.setHorizontalHeaderLabels(
            [c.replace("_", " ").title() for c in display_df.columns]
        )
        lru_idx = None
        if "lru_name" in display_df.columns:
            lru_idx = list(display_df.columns).index("lru_name")
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
