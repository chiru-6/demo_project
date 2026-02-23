"""Home view: landing page with quick stats, activity, status, and navigation."""

from datetime import datetime
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HomeWidget(QWidget):
    """Action-oriented home page with stats, recent activity, system status, and search."""

    go_dashboard      = Signal()
    go_dataset        = Signal()
    go_visualizations = Signal()
    go_chatbot        = Signal()
    search_requested  = Signal(str)

    def __init__(self, db=None) -> None:
        super().__init__()
        self.db = db
        self._recent_activity: List[str] = []
        self._init_ui()
        self._refresh_stats()

    # ── Public API ───────────────────────────────────────────────────────────

    def add_recent_activity(self, message: str) -> None:
        self._recent_activity.insert(0, message)
        while len(self._recent_activity) > 10:
            self._recent_activity.pop()
        self._update_activity_list()

    # ── Internal helpers ────────────────────────────────────────────────────

    def _update_activity_list(self) -> None:
        self.activity_list.clear()
        for msg in self._recent_activity:
            self.activity_list.addItem(QListWidgetItem(msg))

    def _refresh_stats(self) -> None:
        if not self.db:
            self._set_placeholder_stats()
            return
        try:
            stats    = self.db.get_statistics()
            total    = stats.get("total_records", 0)
            results  = stats.get("results", {})
            ok_count = sum(v for k, v in results.items() if str(k).upper() == "OK")
            ok_pct   = (ok_count / total * 100) if total else 0
            num_proj = len(stats.get("projects", {}))
            self.total_value.setText(str(total))
            self.ok_pct_value.setText(f"{ok_pct:.0f}%")
            self.projects_value.setText(str(num_proj))
            self.last_updated_value.setText(datetime.now().strftime("%d %b %H:%M"))
            self.status_db.setText("Database: Connected 🟢")
            self.status_records.setText(f"Records: {total} Loaded")
        except Exception:
            self._set_placeholder_stats()

    def _set_placeholder_stats(self) -> None:
        self.total_value.setText("—")
        self.ok_pct_value.setText("—")
        self.projects_value.setText("—")
        self.last_updated_value.setText("—")
        self.status_db.setText("Database: —")
        self.status_records.setText("Records: —")

    def _on_search(self) -> None:
        text = self.search_edit.text().strip()
        if text:
            self.search_requested.emit(text)

    def _create_card(self, title: str, description: str, button_text: str, signal) -> QFrame:
        card = QFrame()
        card.setObjectName("homeCard")
        card.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("homeCardTitle")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        desc_label = QLabel(description)
        desc_label.setObjectName("homeCardDesc")
        desc_label.setWordWrap(True)

        btn = QPushButton(button_text)
        btn.setObjectName("homeCardButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(signal.emit)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(btn, alignment=Qt.AlignRight)
        return card

    # ── UI construction ──────────────────────────────────────────────────────

    def _init_ui(self) -> None:
        self.setObjectName("homeRoot")
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(20)

        # ── Top row: title + search ──
        top_row = QHBoxLayout()
        header = QLabel("Project Test Data Manager")
        header.setObjectName("homeHeader")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_row.addWidget(header)
        top_row.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("homeSearch")
        self.search_edit.setPlaceholderText("Search projects, rigs, test types...")
        self.search_edit.setMinimumWidth(280)
        self.search_edit.returnPressed.connect(self._on_search)
        top_row.addWidget(self.search_edit)
        root_layout.addLayout(top_row)

        # ── Quick stats bar ──
        stats_bar = QFrame()
        stats_bar.setObjectName("quickStatsBar")
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(20, 14, 20, 14)
        stats_layout.setSpacing(0)

        def _add_stat(label_text: str, value_label: QLabel, trend: str = ""):
            f = QFrame()
            f.setObjectName("quickStatItem")
            lay = QVBoxLayout(f)
            lay.setSpacing(3)
            lay.setContentsMargins(16, 8, 16, 8)
            value_label.setObjectName("quickStatValue")
            lay.addWidget(value_label, alignment=Qt.AlignCenter)
            lab = QLabel(label_text)
            lab.setObjectName("quickStatLabel")
            lay.addWidget(lab, alignment=Qt.AlignCenter)
            if trend:
                t = QLabel(trend)
                t.setObjectName("quickStatTrend")
                lay.addWidget(t, alignment=Qt.AlignCenter)
            stats_layout.addWidget(f)

        self.total_value        = QLabel("—")
        self.ok_pct_value       = QLabel("—")
        self.projects_value     = QLabel("—")
        self.last_updated_value = QLabel("—")

        _add_stat("Total Tests",      self.total_value,        "🟢 live")
        _add_stat("OK %",             self.ok_pct_value,       "🟢 live")
        _add_stat("Active Projects",  self.projects_value)
        _add_stat("Last Updated",     self.last_updated_value)
        stats_layout.addStretch()
        root_layout.addWidget(stats_bar)

        # ── Content: nav cards (left) + activity/status (right) ──
        content = QHBoxLayout()
        content.setSpacing(24)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.addWidget(self._create_card("📊 Dashboard",       "Overview of all test data with filters and summary statistics.", "Open dashboard",      self.go_dashboard),      0, 0)
        grid.addWidget(self._create_card("🗂 Dataset Manager", "View and edit the underlying dataset, import new CSV files.",    "Open dataset manager",self.go_dataset),        0, 1)
        grid.addWidget(self._create_card("📈 Visualizations",  "Interactive charts for projects, test rigs, results and more.", "View charts",         self.go_visualizations), 1, 0)
        grid.addWidget(self._create_card("🤖 AI Chatbot",      "Ask natural-language questions about your test data.",          "Chat with AI",        self.go_chatbot),        1, 1)
        content.addLayout(grid, stretch=3)

        # Right panel
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        activity_label = QLabel("Recent Activity")
        activity_label.setObjectName("homePanelTitle")
        right_panel.addWidget(activity_label)

        self.activity_list = QListWidget()
        self.activity_list.setObjectName("recentActivityList")
        self.activity_list.setMaximumHeight(140)
        for msg in ["✔ New test added", "⚠ Dataset updated", "📊 Visualization exported"]:
            self._recent_activity.append(msg)
        self._update_activity_list()
        right_panel.addWidget(self.activity_list)

        status_label = QLabel("System Status")
        status_label.setObjectName("homePanelTitle")
        right_panel.addWidget(status_label)

        status_frame = QFrame()
        status_frame.setObjectName("systemStatusFrame")
        status_inner = QVBoxLayout(status_frame)
        status_inner.setSpacing(8)
        status_inner.setContentsMargins(14, 12, 14, 12)

        self.status_db      = QLabel("Database: Connected 🟢")
        self.status_ai      = QLabel("AI Service: Online 🟢")
        self.status_records = QLabel("Records: — Loaded")
        for lbl in (self.status_db, self.status_ai, self.status_records):
            lbl.setObjectName("statusLine")
            status_inner.addWidget(lbl)

        right_panel.addWidget(status_frame)
        right_panel.addStretch()
        content.addLayout(right_panel, stretch=1)
        root_layout.addLayout(content)

        self._apply_styles()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._refresh_stats()

    # ── Styles ───────────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        # Theme-dependent colors come from main_window LIGHT/DARK stylesheets.
        # Only set layout/size rules that don't affect light/dark appearance.
        self.setStyleSheet("""
        #homeRoot { }
        #homeHeader { font-size: 24px; font-weight: 700; }
        #homeSearch { border-radius: 8px; padding: 8px 12px; font-size: 13px; }
        #homeSearch:focus { border-color: #4f46e5; }
        #quickStatsBar { border-radius: 14px; }
        #quickStatItem { }
        #quickStatValue { font-size: 28px; font-weight: 700; }
        #quickStatLabel { font-size: 12px; }
        #quickStatTrend { font-size: 11px; }
        #homeCard { border-radius: 14px; }
        #homeCard:hover { border-color: #4f46e5; }
        #homeCardTitle { font-size: 17px; font-weight: 600; }
        #homeCardDesc { font-size: 13px; }
        QPushButton#homeCardButton { border: none; padding: 7px 16px; border-radius: 7px; font-size: 13px; font-weight: 600; }
        QPushButton#homeCardButton:hover { background-color: #4338ca; }
        QPushButton#homeCardButton:pressed { background-color: #3730a3; }
        #homePanelTitle { font-size: 14px; font-weight: 600; }
        #recentActivityList { border-radius: 10px; font-size: 13px; padding: 6px; }
        #recentActivityList::item { padding: 5px 8px; border-radius: 4px; }
        #systemStatusFrame { border-radius: 10px; }
        #statusLine { font-size: 13px; }
        """)
