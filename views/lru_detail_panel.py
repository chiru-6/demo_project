"""LRU Detail Panel: Right-side expandable panel showing LRU details with tabs."""

import os
import platform
import subprocess

import pandas as pd
from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QValueAxis,
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QPainter, QPixmap, QColor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyledItemDelegate,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


# ── Delegate: keeps font consistent in view AND edit mode ───────────────────
class _FontDelegate(QStyledItemDelegate):
    """Ensures inline editor uses the same readable font as the display item."""

    POINT_SIZE = 11

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            f = QFont()
            f.setPointSize(self.POINT_SIZE)
            editor.setFont(f)
            editor.setStyleSheet(
                "QLineEdit {"
                "  border: 2px solid #4f46e5;"
                "  border-radius: 3px;"
                "  padding: 4px 6px;"
                "  background: palette(base);"
                "  color: palette(text);"
                "}"
            )
        return editor

    def sizeHint(self, option, index):
        sh = super().sizeHint(option, index)
        return QSize(sh.width(), max(sh.height(), 34))


# ── Shared table stylesheet (theme colors from main_window) ──────────────────
def _table_stylesheet() -> str:
    return """
        QTableWidget { font-size: 13px; border-radius: 6px; }
        QTableWidget::item { padding: 6px 8px; }
        QTableWidget::item:selected { background: #4f46e5; color: white; }
        QHeaderView::section { font-size: 13px; font-weight: bold; padding: 8px; border: none; }
        QScrollBar:vertical { width: 8px; background: transparent; }
        QScrollBar::handle:vertical { border-radius: 4px; min-height: 20px; }
    """


class LRUDetailPanel(QWidget):
    """Right-side detail panel with tabs. Fully palette-aware (light + dark)."""

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self.current_lru = None
        self.setObjectName("lruDetailPanel")
        self._init_ui()
        self._apply_panel_style()

    # ── Construction ────────────────────────────────────────────────────────

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title = QLabel("LRU Details")
        title.setObjectName("lruPanelTitle")
        header.addWidget(title)
        header.addStretch()

        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setObjectName("lruPanelMinBtn")
        self.minimize_btn.setFixedSize(26, 26)
        self.minimize_btn.setToolTip("Minimize panel")
        self.minimize_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("lruPanelCloseBtn")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setToolTip("Close panel")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        # Thin divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setObjectName("lruDivider")
        layout.addWidget(div)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("lruTabs")
        self.tabs.addTab(self._create_summary_tab(),     "📋  Summary")
        self.tabs.addTab(self._create_test_data_tab(),   "🧪  Test Data")
        self.tabs.addTab(self._create_attachments_tab(), "📎  Files")
        layout.addWidget(self.tabs)

    def _create_summary_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("lruTabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        self.summary_table = QTableWidget()
        self.summary_table.setObjectName("lruSummaryTable")
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.verticalHeader().setDefaultSectionSize(36)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.summary_table.setStyleSheet(_table_stylesheet())
        # ← The key fix: attach delegate so edit font matches display font
        self._summary_delegate = _FontDelegate(self.summary_table)
        self.summary_table.setItemDelegateForColumn(1, self._summary_delegate)
        layout.addWidget(self.summary_table)

        hdr = QLabel("Test Statistics")
        hdr.setObjectName("lruSectionHeader")
        layout.addWidget(hdr)

        self.stats_chart = QChartView()
        self.stats_chart.setObjectName("lruChartView")
        self.stats_chart.setMinimumHeight(200)
        self.stats_chart.setMaximumHeight(240)
        self.stats_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.stats_chart)
        layout.addStretch()
        return tab

    def _create_test_data_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("lruTabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        self.test_data_table = QTableWidget()
        self.test_data_table.setObjectName("lruTestDataTable")
        self.test_data_table.setAlternatingRowColors(True)
        self.test_data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.test_data_table.verticalHeader().setDefaultSectionSize(36)
        self.test_data_table.setStyleSheet(_table_stylesheet())
        self._test_delegate = _FontDelegate(self.test_data_table)
        self.test_data_table.setItemDelegate(self._test_delegate)
        layout.addWidget(self.test_data_table)
        return tab

    def _create_attachments_tab(self) -> QWidget:
        tab = QWidget()
        tab.setObjectName("lruTabPage")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(8)

        attach_hdr = QLabel("Attachments (drag & drop files here)")
        attach_hdr.setObjectName("lruSectionHeader")
        layout.addWidget(attach_hdr)

        drop_frame = QFrame()
        drop_frame.setObjectName("lruDropZone")
        drop_frame.setStyleSheet("#lruDropZone { border: 2px dashed #94a3b8; border-radius: 8px; padding: 4px; }")
        drop_layout = QVBoxLayout(drop_frame)
        drop_layout.setContentsMargins(4, 4, 4, 4)
        drop_frame.setAcceptDrops(True)

        self.attachments_list = QListWidget()
        self.attachments_list.setObjectName("lruAttachmentList")
        self.attachments_list.setMaximumHeight(160)
        # Theme colors from main_window LIGHT/DARK stylesheets
        self.attachments_list.setStyleSheet("""
            QListWidget { border-radius: 6px; font-size: 13px; padding: 4px; }
            QListWidget::item { padding: 7px 10px; border-radius: 4px; }
            QListWidget::item:selected { background: #4f46e5; color: white; }
        """)
        self.attachments_list.itemClicked.connect(self._on_attachment_selected)
        self.attachments_list.itemDoubleClicked.connect(self._open_attachment)
        drop_layout.addWidget(self.attachments_list)
        layout.addWidget(drop_frame)

        def _drag_enter(e):
            if e.mimeData().hasUrls():
                e.acceptProposedAction()
        def _drop(e):
            urls = e.mimeData().urls()
            paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
            for p in paths:
                self._add_attachment_path(p)
            e.acceptProposedAction()
        drop_frame.dragEnterEvent = _drag_enter
        drop_frame.dropEvent = _drop

        preview_hdr = QLabel("Preview")
        preview_hdr.setObjectName("lruSectionHeader")
        layout.addWidget(preview_hdr)

        self.preview_label = QLabel("Select an attachment to preview")
        self.preview_label.setObjectName("lruPreviewLabel")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(140)
        self.preview_label.setWordWrap(True)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.preview_label)

        self.add_attach_btn = QPushButton("＋  Add Attachment")
        self.add_attach_btn.setObjectName("lruAddAttachBtn")
        self.add_attach_btn.setCursor(Qt.PointingHandCursor)
        self.add_attach_btn.setFixedHeight(36)
        self.add_attach_btn.clicked.connect(self._add_attachment)
        layout.addWidget(self.add_attach_btn)
        return tab

    # ── Styling ─────────────────────────────────────────────────────────────

    def _apply_panel_style(self) -> None:
        # Theme-dependent colors come from main_window LIGHT/DARK stylesheets.
        # Only set layout/size rules and indigo accent (works in both themes).
        self.setStyleSheet("""
            #lruDetailPanel { }
            #lruPanelTitle { font-size: 17px; font-weight: 700; }
            #lruDivider { margin: 0 0 4px 0; }
            #lruTabs QTabBar::tab {
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom: none;
                margin-right: 2px;
            }
            #lruTabs QTabBar::tab:selected { background: #4f46e5; color: white; border-color: #4f46e5; }
            #lruTabs QTabWidget::pane { border-radius: 0 6px 6px 6px; }
            #lruSectionHeader { font-size: 13px; font-weight: 700; padding: 2px 0; }
            #lruPreviewLabel { border-radius: 6px; font-size: 12px; padding: 12px; }
            #lruAddAttachBtn {
                background-color: #4f46e5;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 16px;
            }
            #lruAddAttachBtn:hover { background-color: #4338ca; }
            #lruAddAttachBtn:pressed { background-color: #3730a3; }
            #lruPanelMinBtn, #lruPanelCloseBtn { border-radius: 4px; font-size: 14px; font-weight: bold; }
            #lruPanelMinBtn:hover { background: #fbbf24; color: #1f2937; border-color: #f59e0b; }
            #lruPanelCloseBtn:hover { background: #ef4444; color: white; border-color: #dc2626; }
        """)

    # ── Data loading ────────────────────────────────────────────────────────

    def show_lru(self, lru_name: str) -> None:
        self.current_lru = lru_name
        self._load_summary(lru_name)
        self._load_test_data(lru_name)
        self._load_attachments(lru_name)

    def _load_summary(self, lru_name: str) -> None:
        df = self.db.get_lru_data(lru_name)
        if df.empty:
            self.summary_table.setRowCount(0)
            return

        row = df.iloc[0]
        all_fields = [
            ("LRU Name",          row.get("lru_name", "")),
            ("Project",           row.get("project", "")),
            ("Division / Group",  row.get("division_group", "")),
            ("System",            row.get("system", "")),
            ("Part Number",       row.get("part_number", "")),
            ("Serial No",         row.get("serial_no", "")),
            ("Received Data",     row.get("received_data", "")),
            ("Type of Test",      row.get("type_of_test", "")),
            ("Test Rig",          row.get("test_rig", "")),
            ("Date of PI",        row.get("date_of_pi", "")),
            ("Results & Remarks", row.get("results_remarks", "")),
            ("Date of Clearance", row.get("date_of_clearance", "")),
        ]
        fields = [(f, v) for f, v in all_fields if v and str(v).strip() and pd.notna(v)]

        field_font = QFont(); field_font.setBold(True); field_font.setPointSize(11)
        value_font = QFont(); value_font.setPointSize(11)

        self.summary_table.setRowCount(len(fields))
        for i, (field, value) in enumerate(fields):
            fi = QTableWidgetItem(str(field))
            fi.setFlags(fi.flags() & ~Qt.ItemIsEditable)
            fi.setFont(field_font)
            self.summary_table.setItem(i, 0, fi)

            vi = QTableWidgetItem(str(value) if pd.notna(value) else "")
            vi.setFlags(vi.flags() | Qt.ItemIsEditable)
            vi.setFont(value_font)
            self.summary_table.setItem(i, 1, vi)

        self.summary_table.resizeColumnToContents(0)
        self._build_chart(
            df["results_remarks"].value_counts()
            if "results_remarks" in df.columns
            else pd.Series()
        )

    def _build_chart(self, results: pd.Series) -> None:
        chart = QChart()
        chart.setTitle("Test Results Distribution")
        chart.setBackgroundVisible(False)
        chart.legend().setVisible(True)

        if not results.empty:
            bar_set = QBarSet("Count")
            bar_set.setColor(QColor("#4f46e5"))
            for val in results.values:
                bar_set.append(int(val))
            series = QBarSeries()
            series.append(bar_set)
            chart.addSeries(series)
            ax_x = QBarCategoryAxis()
            ax_x.append([str(k) for k in results.index])
            chart.addAxis(ax_x, Qt.AlignBottom)
            series.attachAxis(ax_x)
            ax_y = QValueAxis()
            ax_y.setRange(0, max(results.values) * 1.15)
            chart.addAxis(ax_y, Qt.AlignLeft)
            series.attachAxis(ax_y)

        self.stats_chart.setChart(chart)

    def _load_test_data(self, lru_name: str) -> None:
        csv_df = self.db.get_lru_test_data_csv(lru_name)
        if not csv_df.empty:
            self._fill_table(self.test_data_table, csv_df)
            return

        df = self.db.get_lru_data(lru_name)
        if df.empty:
            self.test_data_table.setRowCount(0)
            return

        cols = ["date_of_pi", "type_of_test", "test_rig", "results_remarks",
                "test_standard", "test_lab", "approval_status"]
        self._fill_table(self.test_data_table, df[[c for c in cols if c in df.columns]])

    def _fill_table(self, table: QTableWidget, df: pd.DataFrame) -> None:
        font = QFont(); font.setPointSize(11)
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in df.columns])
        for i, row in enumerate(df.itertuples(index=False)):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setFont(font)
                table.setItem(i, j, item)
        table.resizeColumnsToContents()

    def _load_attachments(self, lru_name: str) -> None:
        df = self.db.get_lru_attachments(lru_name)
        self.attachments_list.clear()
        self.preview_label.setText("Select an attachment to preview")
        self.preview_label.setPixmap(QPixmap())

        for _, row in df.iterrows():
            file_name = row["file_name"]
            file_path = row["file_path"]
            file_type = (row.get("file_type", "").upper()
                         if pd.notna(row.get("file_type")) else "")
            icon = ("🖼️" if file_type in {"PNG", "JPG", "JPEG", "GIF", "BMP"}
                    else ("📄" if file_type == "PDF" else "📎"))
            item = QListWidgetItem(f"{icon}  {file_name}")
            item.setData(Qt.UserRole,     file_path)
            item.setData(Qt.UserRole + 1, file_type)
            self.attachments_list.addItem(item)

    # ── Attachment interactions ──────────────────────────────────────────────

    def _on_attachment_selected(self, item: QListWidgetItem) -> None:
        file_path = item.data(Qt.UserRole)
        file_type = item.data(Qt.UserRole + 1) or ""
        if not file_path:
            return

        if not os.path.exists(file_path):
            self.preview_label.setText(f"⚠ File not found:\n{os.path.basename(file_path)}")
            self.preview_label.setPixmap(QPixmap())
            return

        ext = os.path.splitext(file_path)[1].lower()
        if file_type in {"PNG", "JPG", "JPEG", "GIF", "BMP"} or ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
            px = QPixmap(file_path)
            if not px.isNull():
                self.preview_label.setPixmap(px.scaled(400, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.preview_label.setText("")
            else:
                self.preview_label.setText("Unable to load image.")
                self.preview_label.setPixmap(QPixmap())
        elif file_type == "PDF" or ext == ".pdf":
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(f"📄 PDF\n\n{os.path.basename(file_path)}\n\nDouble-click to open.")
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(f"📎 {os.path.basename(file_path)}\n\nDouble-click to open.")

    def _open_attachment(self, item: QListWidgetItem) -> None:
        file_path = item.data(Qt.UserRole)
        if not file_path:
            return
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not open file:\n{exc}")

    def _add_attachment_path(self, file_path: str) -> bool:
        """Add a single file as attachment. Returns True if successful."""
        if not self.current_lru:
            QMessageBox.information(self, "No LRU", "Please select an LRU first.")
            return False
        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_name)[1][1:].upper() or "FILE"
        success, msg = self.db.add_attachment(self.current_lru, file_name, file_path, file_type)
        if success:
            self._load_attachments(self.current_lru)
        else:
            QMessageBox.warning(self, "Error", f"Could not add attachment:\n{msg}")
        return success

    def _add_attachment(self) -> None:
        if not self.current_lru:
            QMessageBox.information(self, "No LRU", "Please select an LRU first.")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Attachment", "", "All Files (*.*)")
        if file_path:
            self._add_attachment_path(file_path)
