"""Dataset Relations Panel: relational explorer with filters, animated stats, full cross-breakdown, and detail modal."""

import pandas as pd
from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# ── Column name resolution (CSV vs DB) ───────────────────────────────────────
_COL = {
    "lru":          ("LRU Name",         "lru_name"),
    "project":      ("Project",          "project"),
    "division":     ("Division / Group", "division_group"),
    "system":       ("System",           "system"),
    "part":         ("Part Number",      "part_number"),
    "serial":       ("Serial No",        "serial_no"),
    "received":     ("Received Data",    "received_data"),
    "test_type":    ("Type of Test",     "type_of_test"),
    "test_rig":     ("Test Rig",         "test_rig"),
    "date_pi":      ("Date of PI",       "date_of_pi"),
    "results":      ("Results & Remarks","results_remarks"),
    "date_clearance":("Date of Clearance","date_of_clearance"),
}

FILTER_KEYS = [
    ("LRU Name", _COL["lru"]),
    ("Project",  _COL["project"]),
    ("Division", _COL["division"]),
    ("System",   _COL["system"]),
    ("Test Type",_COL["test_type"]),
    ("Test Rig", _COL["test_rig"]),
    ("Result",   _COL["results"]),
]

# Cross-breakdown dimensions always shown (except active filter)
CROSS_DIMS = [
    ("Division",  _COL["division"]),
    ("System",    _COL["system"]),
    ("Test Type", _COL["test_type"]),
    ("Project",   _COL["project"]),
    ("Test Rig",  _COL["test_rig"]),
]

RESULT_COLORS = {
    "OK":           "#10b981",
    "NOT OK":       "#ef4444",
    "Pending":      "#f59e0b",
    "Under Review": "#3b82f6",
}

CROSS_COLORS = ["#6366f1", "#06b6d4", "#8b5cf6", "#ec4899", "#14b8a6"]

# Theme colors (light mode matches app; dark mode for night)
THEME_LIGHT = {
    "bg": "#f8fafc",
    "panel_bg": "#ffffff",
    "panel_border": "#e5e7eb",
    "text": "#1f2937",
    "muted": "#6b7280",
    "accent": "#4f46e5",
    "hover": "#e5e7eb",
    "bar_bg": "#e2e8f0",
    "alt_row": "#f8fafc",
    "header_bg": "#f1f5f9",
}
THEME_DARK = {
    "bg": "#0f172a",
    "panel_bg": "#1e293b",
    "panel_border": "#334155",
    "text": "#e2e8f0",
    "muted": "#64748b",
    "accent": "#6366f1",
    "hover": "#334155",
    "bar_bg": "#0f172a",
    "alt_row": "#1e293b50",
    "header_bg": "#0f172a",
}


def _col(df: pd.DataFrame, key: str) -> str | None:
    for c in _COL[key]:
        if c in df.columns:
            return c
    return None


# ── Animated Progress Bar ─────────────────────────────────────────────────────
class AnimatedBar(QWidget):
    """A mini labeled bar that animates its fill smoothly when value changes."""

    def __init__(self, label: str, value: int, max_val: int, color: str, theme: dict, parent=None):
        super().__init__(parent)
        self._color = color
        self._theme = theme
        self._max = max_val if max_val > 0 else 1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self.lbl = QLabel(label)
        self.lbl.setFixedWidth(90)
        layout.addWidget(self.lbl)

        self.bar = QProgressBar()
        self.bar.setMinimum(0)
        self.bar.setMaximum(1000)       # use 0-1000 for smooth stepping
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        layout.addWidget(self.bar, 1)

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setFixedWidth(28)
        self.val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.val_lbl)

        self._apply_theme()

        # Animate on creation
        self._anim = QPropertyAnimation(self.bar, b"value")
        self._anim.setDuration(500)
        self._anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutCubic))
        self._anim.setStartValue(0)
        target_scaled = int((value / self._max) * 1000)
        self._anim.setEndValue(target_scaled)
        QTimer.singleShot(30, self._anim.start)

    def _apply_theme(self) -> None:
        t = self._theme
        self.lbl.setStyleSheet(f"color: {t['muted']}; font-size: 11px;")
        self.val_lbl.setStyleSheet(f"color: {t['text']}; font-size: 11px; font-weight: bold;")
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background: {t['bar_bg']}; border-radius: 3px; border: none; }}
            QProgressBar::chunk {{ background: {self._color}; border-radius: 3px; }}
        """)

    def update_theme(self, theme: dict) -> None:
        self._theme = theme
        self._apply_theme()

    def update_value(self, value: int, max_val: int) -> None:
        """Smoothly animate to new value."""
        self._max = max_val if max_val > 0 else 1
        self.val_lbl.setText(str(value))
        current_scaled = self.bar.value()
        target_scaled  = int((value / self._max) * 1000)
        self._anim.stop()
        self._anim.setStartValue(current_scaled)
        self._anim.setEndValue(target_scaled)
        self._anim.start()


# ── Collapsible cross-breakdown card ─────────────────────────────────────────
class CrossCard(QFrame):
    """A single cross-breakdown dimension card with animated bars."""

    def __init__(self, title: str, color: str, theme: dict, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self._theme = theme
        self._bars: dict[str, AnimatedBar] = {}

        self.setFrameShape(QFrame.StyledPanel)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(6)

        # Title row with accent dot
        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 8px; margin-right: 4px;")
        header.addWidget(dot)
        self.title_lbl = QLabel(title)
        header.addWidget(self.title_lbl)
        header.addStretch()
        self.count_lbl = QLabel("")
        header.addWidget(self.count_lbl)
        outer.addLayout(header)

        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.Shape.HLine)
        self.sep.setFixedHeight(1)
        outer.addWidget(self.sep)

        self.bars_widget = QWidget()
        self.bars_layout = QVBoxLayout(self.bars_widget)
        self.bars_layout.setContentsMargins(0, 0, 0, 0)
        self.bars_layout.setSpacing(2)
        outer.addWidget(self.bars_widget)

        self.empty_lbl = QLabel("Select a value to see breakdown")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.empty_lbl)

        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self._theme
        self.setStyleSheet(f"""
            CrossCard {{
                background: {t['panel_bg']};
                border: 1px solid {t['panel_border']};
                border-radius: 10px;
            }}
        """)
        self.title_lbl.setStyleSheet(
            f"color: {t['text']}; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;"
        )
        self.count_lbl.setStyleSheet(f"color: {t['muted']}; font-size: 10px;")
        self.sep.setStyleSheet(f"border: none; border-top: 1px solid {t['panel_border']};")
        self.empty_lbl.setStyleSheet(f"color: {t['muted']}; font-size: 10px; padding: 4px 0;")
        for bar in self._bars.values():
            bar.update_theme(t)

    def update_theme(self, theme: dict) -> None:
        self._theme = theme
        self._apply_theme()

    def refresh(self, counts: dict[str, int], total: int) -> None:
        """Animate bars to new data. Adds/removes bars as needed."""
        self.empty_lbl.setVisible(not counts)
        self.count_lbl.setText(f"{total} records" if counts else "")

        existing  = set(self._bars.keys())
        new_keys  = set(counts.keys())

        # Remove stale bars
        for k in existing - new_keys:
            bar = self._bars.pop(k)
            self.bars_layout.removeWidget(bar)
            bar.deleteLater()

        # Update or create bars
        for k, v in counts.items():
            if k in self._bars:
                self._bars[k].update_value(v, total)
            else:
                bar = AnimatedBar(str(k)[:26], v, total, self.color, self._theme)
                self._bars[k] = bar
                self.bars_layout.addWidget(bar)

    def clear(self) -> None:
        for bar in self._bars.values():
            self.bars_layout.removeWidget(bar)
            bar.deleteLater()
        self._bars.clear()
        self.count_lbl.setText("")
        self.empty_lbl.setVisible(True)


# ── Result stats card ─────────────────────────────────────────────────────────
class ResultStatsCard(QFrame):
    """Animated result-distribution bars."""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._bars: dict[str, AnimatedBar] = {}

        self.setFrameShape(QFrame.StyledPanel)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(6)

        header = QHBoxLayout()
        self.title_lbl = QLabel("RESULT DISTRIBUTION")
        header.addWidget(self.title_lbl)
        header.addStretch()
        self.rec_lbl = QLabel("")
        header.addWidget(self.rec_lbl)
        outer.addLayout(header)

        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.Shape.HLine)
        self.sep.setFixedHeight(1)
        outer.addWidget(self.sep)

        self.bars_widget = QWidget()
        self.bars_layout = QVBoxLayout(self.bars_widget)
        self.bars_layout.setContentsMargins(0, 0, 0, 0)
        self.bars_layout.setSpacing(2)
        outer.addWidget(self.bars_widget)

        # Pre-create bars for all result types in fixed order
        for k in ["OK", "NOT OK", "Pending", "Under Review"]:
            bar = AnimatedBar(k, 0, 1, RESULT_COLORS[k], self._theme)
            self._bars[k] = bar
            self.bars_layout.addWidget(bar)

        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self._theme
        self.setStyleSheet(f"""
            ResultStatsCard {{
                background: {t['panel_bg']};
                border: 1px solid {t['panel_border']};
                border-radius: 10px;
            }}
        """)
        self.title_lbl.setStyleSheet(
            f"color: {t['muted']}; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        self.rec_lbl.setStyleSheet(f"color: {t['accent']}; font-size: 11px; font-weight: bold;")
        self.sep.setStyleSheet(f"border: none; border-top: 1px solid {t['panel_border']};")
        for bar in self._bars.values():
            bar.update_theme(t)

    def update_theme(self, theme: dict) -> None:
        self._theme = theme
        self._apply_theme()

    def refresh(self, counts: dict, total: int) -> None:
        self.rec_lbl.setText(f"{total}")
        for k in ["OK", "NOT OK", "Pending", "Under Review"]:
            v = int(counts.get(k, 0))
            self._bars[k].update_value(v, total)


# ── Detail dialog ─────────────────────────────────────────────────────────────
class _DetailDialog(QDialog):
    def __init__(self, row_data: dict, related_counts: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Details")
        self.setMinimumWidth(460)
        t = theme
        self.setStyleSheet(f"""
            QDialog {{ background: {t['bg']}; color: {t['text']}; }}
            QLabel  {{ color: {t['text']}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel(str(row_data.get("LRU Name", row_data.get("lru_name", ""))))
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        hdr.addWidget(title)
        hdr.addStretch()
        result = str(row_data.get("Results & Remarks", row_data.get("results_remarks", "")))
        if result and result != "nan":
            res_lbl = QLabel(result)
            color = RESULT_COLORS.get(result, "#64748b")
            res_lbl.setStyleSheet(
                f"background: {color}30; color: {color}; border: 1px solid {color}60; "
                "padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 11px;"
            )
            hdr.addWidget(res_lbl)
        layout.addLayout(hdr)

        serial = str(row_data.get("Serial No", row_data.get("serial_no", "")))
        if serial and serial != "nan":
            s = QLabel(serial)
            s.setStyleSheet(f"color: {t['muted']}; font-size: 11px;")
            layout.addWidget(s)

        # Fields grid
        skip = {"LRU Name", "Serial No", "Results & Remarks", "lru_name", "serial_no", "results_remarks"}
        grid = QGridLayout()
        grid.setSpacing(8)
        cols = [c for c in row_data if c not in skip and str(row_data.get(c, "")) not in ("", "nan")]
        for i, k in enumerate(cols):
            r, c = i // 2, (i % 2) * 2
            key_lbl = QLabel(f"{k}:")
            key_lbl.setStyleSheet(f"color: {t['muted']}; font-size: 11px;")
            val_lbl = QLabel(str(row_data.get(k, "")))
            val_lbl.setStyleSheet(f"color: {t['text']}; font-size: 11px;")
            val_lbl.setWordWrap(True)
            grid.addWidget(key_lbl, r, c)
            grid.addWidget(val_lbl, r, c + 1)
        layout.addLayout(grid)

        # Related summary
        if related_counts:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"border: none; border-top: 1px solid {t['panel_border']};")
            layout.addWidget(sep)
            lbl = QLabel("Other records with same LRU:")
            lbl.setStyleSheet(f"color: {t['muted']}; font-size: 11px;")
            layout.addWidget(lbl)
            badges = QHBoxLayout()
            for k, v in related_counts.items():
                if v > 0:
                    color = RESULT_COLORS.get(k, "#64748b")
                    b = QLabel(f"{v}× {k}")
                    b.setStyleSheet(
                        f"background: {color}25; color: {color}; border: 1px solid {color}50; "
                        "padding: 3px 8px; border-radius: 4px; font-size: 11px;"
                    )
                    badges.addWidget(b)
            badges.addStretch()
            layout.addLayout(badges)

        ok_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t['accent']}; color: white; border: none;
                padding: 6px 20px; border-radius: 6px; font-weight: bold;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        ok_btn.accepted.connect(self.accept)
        layout.addWidget(ok_btn)


# ── Main panel ────────────────────────────────────────────────────────────────
class DatasetRelationsPanel(QWidget):
    """
    Full relational explorer with:
      • Left filter panel (filter key + value list)
      • Result distribution card (animated)
      • Cross-breakdown cards for Division, System, Test Type (animated)
      • Sortable, paginated record table
      • Double-click detail modal
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df               = pd.DataFrame()
        self._sort_col        = None
        self._sort_asc        = True
        self._page            = 0
        self._page_size       = 15
        self._selected_value  = None
        self._table_df        = pd.DataFrame()
        self._table_cols: list[str] = []
        self._theme           = THEME_LIGHT.copy()
        self._theme_connected = False
        self._init_ui()

    def _get_theme(self) -> dict:
        """Return current theme based on main window dark/light mode."""
        mw = self.window()
        if hasattr(mw, "is_dark_mode") and mw.is_dark_mode():
            return THEME_DARK.copy()
        return THEME_LIGHT.copy()

    def _apply_theme(self) -> None:
        """Apply theme-aware styling to the panel and children."""
        self._theme = self._get_theme()
        t = self._theme
        self.setStyleSheet(f"""
            QWidget {{ background: {t['bg']}; color: {t['text']}; font-family: 'Segoe UI', sans-serif; }}
            QGroupBox {{ border: none; color: {t['muted']}; font-size: 10px; font-weight: bold; letter-spacing: 1px; }}
            QScrollBar:vertical {{ background: {t['panel_bg']}; width: 6px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background: {t['panel_border']}; border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        if hasattr(self, "filter_panel"):
            self.filter_panel.setStyleSheet(f"""
                #filterByPanel {{
                    background: {t['panel_bg']};
                    border: 1px solid {t['panel_border']};
                    border-radius: 12px;
                }}
            """)
        if hasattr(self, "values_panel"):
            self.values_panel.setStyleSheet(f"""
                #valuesPanel {{
                    background: {t['panel_bg']};
                    border: 1px solid {t['panel_border']};
                    border-radius: 12px;
                }}
            """)
        if hasattr(self, "filter_label"):
            self.filter_label.setStyleSheet(
                f"color: {t['muted']}; font-size: 10px; font-weight: bold; letter-spacing: 1.5px; padding-bottom: 2px;"
            )
        if hasattr(self, "values_label"):
            self.values_label.setStyleSheet(
                f"color: {t['muted']}; font-size: 10px; font-weight: bold; letter-spacing: 1.5px; padding-bottom: 2px;"
            )
        if hasattr(self, "filter_btns"):
            for _, btn in self.filter_btns:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left; padding: 7px 12px; border-radius: 7px;
                        background: transparent; color: {t['muted']}; border: none; font-size: 12px;
                    }}
                    QPushButton:hover {{ background: {t['hover']}; color: {t['text']}; }}
                    QPushButton:checked {{ background: {t['accent']}; color: white; font-weight: bold; }}
                """)
        if hasattr(self, "values_list"):
            self.values_list.setStyleSheet(f"""
                #valuesList {{
                    background: transparent; border: none; padding: 2px;
                }}
                #valuesList::item {{ padding: 6px 10px; border-radius: 6px; color: {t['text']}; font-size: 11px; }}
                #valuesList::item:hover {{ background: {t['hover']}; }}
                #valuesList::item:selected {{ background: {t['accent']}40; color: {t['text']}; border: 1px solid {t['accent']}60; }}
                #valuesList QScrollBar:vertical {{
                    background: {t['panel_bg']}; width: 10px; border-radius: 5px; margin: 2px 0;
                }}
                #valuesList QScrollBar::handle:vertical {{
                    background: {t['panel_border']}; border-radius: 5px; min-height: 24px;
                }}
                #valuesList QScrollBar::handle:vertical:hover {{ background: {t['accent']}; }}
                #valuesList QScrollBar::add-line:vertical, #valuesList QScrollBar::sub-line:vertical {{ height: 0; }}
            """)
        if hasattr(self, "result_card"):
            self.result_card.update_theme(t)
        for card in getattr(self, "cross_cards", {}).values():
            card.update_theme(t)
        if hasattr(self, "table_frame"):
            self.table_frame.setStyleSheet(f"""
                QFrame {{ background: {t['panel_bg']}; border: 1px solid {t['panel_border']}; border-radius: 10px; }}
            """)
        if hasattr(self, "table_title_lbl"):
            self.table_title_lbl.setStyleSheet(
                f"color: {t['muted']}; font-size: 10px; font-weight: bold; letter-spacing: 1.5px;"
            )
        if hasattr(self, "pag_label"):
            self.pag_label.setStyleSheet(f"color: {t['muted']}; font-size: 11px;")
        if hasattr(self, "pag_prev"):
            for btn in (self.pag_prev, self.pag_next):
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {t['panel_border']}; color: {t['text']};
                        border: none; border-radius: 5px; font-size: 14px;
                    }}
                    QPushButton:hover {{ background: {t['accent']}; }}
                    QPushButton:disabled {{ background: {t['panel_bg']}; color: {t['muted']}; }}
                """)
        if hasattr(self, "sub_table"):
            self.sub_table.setStyleSheet(f"""
                QTableWidget {{
                    background: transparent; alternate-background-color: {t['alt_row']};
                    border: none; font-size: 12px; selection-background-color: {t['accent']}30;
                }}
                QTableWidget::item {{ padding: 6px 8px; border-bottom: 1px solid {t['panel_border']}30; color: {t['text']}; }}
                QHeaderView::section {{
                    background: {t['header_bg']}; color: {t['muted']};
                    font-size: 10px; font-weight: bold; letter-spacing: 0.8px;
                    padding: 6px 8px; border: none; border-bottom: 1px solid {t['panel_border']};
                }}
                QHeaderView::section:hover {{ background: {t['panel_bg']}; color: {t['text']}; }}
            """)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._theme_connected:
            mw = self.window()
            if hasattr(mw, "themeChanged"):
                mw.themeChanged.connect(self._apply_theme)
                self._theme_connected = True
        self._apply_theme()

    # ── UI construction ───────────────────────────────────────────────────────
    def _init_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(14)

        # ── Left side: two separate containers ─────────────────────────────
        left_side = QWidget()
        left_side.setFixedWidth(196)
        left_side_layout = QVBoxLayout(left_side)
        left_side_layout.setContentsMargins(0, 0, 0, 0)
        left_side_layout.setSpacing(12)

        # Container 1: FILTER BY
        self.filter_panel = QFrame()
        self.filter_panel.setObjectName("filterByPanel")
        filter_layout = QVBoxLayout(self.filter_panel)
        filter_layout.setContentsMargins(10, 12, 10, 12)
        filter_layout.setSpacing(8)

        self.filter_label = QLabel("FILTER BY")
        filter_layout.addWidget(self.filter_label)

        self.filter_btns: list[tuple[str, QPushButton]] = []
        for i, (label, _) in enumerate(FILTER_KEYS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, l=label: self._on_filter_clicked(l))
            if i == 0:
                btn.setChecked(True)
            self.filter_btns.append((label, btn))
            filter_layout.addWidget(btn)

        left_side_layout.addWidget(self.filter_panel)

        # Container 2: Dynamic label (LRU Name, Project, etc.) + values list
        self.values_panel = QFrame()
        self.values_panel.setObjectName("valuesPanel")
        values_panel_layout = QVBoxLayout(self.values_panel)
        values_panel_layout.setContentsMargins(10, 12, 10, 12)
        values_panel_layout.setSpacing(8)

        self.values_label = QLabel("LRU Name")  # Dynamic: matches selected filter
        values_panel_layout.addWidget(self.values_label)

        self.values_list = QListWidget()
        self.values_list.setObjectName("valuesList")
        self.values_list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.values_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.values_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.values_list.setMinimumHeight(120)
        self.values_list.itemClicked.connect(self._on_value_clicked)
        values_panel_layout.addWidget(self.values_list, 1)

        left_side_layout.addWidget(self.values_panel, 1)

        root.addWidget(left_side)

        # ── Right content area ────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)

        # ── Stats cards: 2-row layout matching screenshot ──────────────────
        # Row 1: Result distribution + Project
        # Row 2: Division, System, Test Type, Test Rig
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)
        stats_grid.setContentsMargins(0, 0, 0, 0)

        self.result_card = ResultStatsCard(self._theme)
        self.result_card.setFixedWidth(260)
        stats_grid.addWidget(self.result_card, 0, 0)

        self.cross_cards: dict[str, CrossCard] = {}
        # Order for layout: Project first (row 0), then Division, System, Test Type, Test Rig (row 1)
        layout_order = [("Project", 0, 1), ("Division", 1, 0), ("System", 1, 1), ("Test Type", 1, 2), ("Test Rig", 1, 3)]
        for dim_label, row, col in layout_order:
            i = next(j for j, (d, _) in enumerate(CROSS_DIMS) if d == dim_label)
            color = CROSS_COLORS[i % len(CROSS_COLORS)]
            card = CrossCard(dim_label, color, self._theme)
            card.setMinimumWidth(160)
            self.cross_cards[dim_label] = card
            stats_grid.addWidget(card, row, col, 1, 1)

        right.addLayout(stats_grid)

        # ── Table ─────────────────────────────────────────────────────────
        self.table_frame = QFrame()
        table_outer = QVBoxLayout(self.table_frame)
        table_outer.setContentsMargins(0, 0, 0, 0)
        table_outer.setSpacing(0)

        # Table header row
        tbl_hdr = QHBoxLayout()
        tbl_hdr.setContentsMargins(12, 10, 12, 0)
        self.table_title_lbl = QLabel("RECORDS")
        tbl_hdr.addWidget(self.table_title_lbl)
        tbl_hdr.addStretch()
        self.pag_label = QLabel("")
        tbl_hdr.addWidget(self.pag_label)
        self.pag_prev = QPushButton("‹")
        self.pag_next = QPushButton("›")
        for btn in (self.pag_prev, self.pag_next):
            btn.setFixedSize(28, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pag_prev.clicked.connect(lambda: self._set_page(self._page - 1))
        self.pag_next.clicked.connect(lambda: self._set_page(self._page + 1))
        tbl_hdr.addWidget(self.pag_prev)
        tbl_hdr.addWidget(self.pag_next)
        table_outer.addLayout(tbl_hdr)

        self.sub_table = QTableWidget()
        self.sub_table.setAlternatingRowColors(True)
        self.sub_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sub_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sub_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sub_table.setShowGrid(False)
        self.sub_table.setFrameShape(QFrame.Shape.NoFrame)
        self.sub_table.verticalHeader().setVisible(False)
        self.sub_table.horizontalHeader().setStretchLastSection(True)
        self.sub_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.sub_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self.sub_table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        table_outer.addWidget(self.sub_table)

        right.addWidget(self.table_frame, 1)

        right_w = QWidget()
        right_w.setLayout(right)
        root.addWidget(right_w, 1)

        self._apply_theme()

    # ── Filter helpers ────────────────────────────────────────────────────────
    def _get_active_filter(self) -> str | None:
        for label, btn in self.filter_btns:
            if btn.isChecked():
                return label
        return None

    def _get_filter_col(self, label: str) -> str | None:
        for l, choices in FILTER_KEYS:
            if l == label:
                for c in choices:
                    if c in self.df.columns:
                        return c
        return None

    def _get_cross_col(self, label: str) -> str | None:
        for l, choices in CROSS_DIMS:
            if l == label:
                for c in choices:
                    if c in self.df.columns:
                        return c
        return None

    # ── Event handlers ────────────────────────────────────────────────────────
    def _on_filter_clicked(self, label: str) -> None:
        for l, btn in self.filter_btns:
            btn.setChecked(l == label)
        self._selected_value = None
        self._page = 0
        self._refresh_values_list()
        self._refresh_all()

    def _on_value_clicked(self, item: QListWidgetItem) -> None:
        val = item.data(Qt.ItemDataRole.UserRole)
        if self._selected_value == val:
            self._selected_value = None
            self.values_list.clearSelection()
        else:
            self._selected_value = val
        self._page = 0
        self._refresh_all()

    def _on_header_clicked(self, idx: int) -> None:
        if idx >= len(self._table_cols):
            return
        col = self._table_cols[idx]
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._refresh_sub_table()

    def _on_cell_double_clicked(self, row: int, _col: int) -> None:
        if self._table_df.empty:
            return
        actual = self._page * self._page_size + row
        if actual >= len(self._table_df):
            return
        row_series = self._table_df.iloc[actual]
        row_data   = dict(row_series)
        col_lru    = _col(self.df, "lru")
        col_res    = _col(self.df, "results")
        lru        = str(row_series.get(col_lru, "")) if col_lru else ""
        related_counts: dict[str, int] = {}
        if lru and col_lru and col_res:
            related = self.df[self.df[col_lru].astype(str) == lru]
            for k, v in related[col_res].value_counts().items():
                related_counts[str(k)] = int(v)
        _DetailDialog(row_data, related_counts, self._theme, self).exec()

    # ── Data helpers ──────────────────────────────────────────────────────────
    def _get_filtered_df(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame()
        active = self._get_active_filter()
        col    = self._get_filter_col(active) if active else None
        if not col or not self._selected_value:
            return self.df.copy()
        return self.df[self.df[col].astype(str) == self._selected_value].copy()

    # ── Refresh routines ──────────────────────────────────────────────────────
    def _refresh_values_list(self) -> None:
        self.values_list.clear()
        active = self._get_active_filter()
        # Update values panel header to match selected filter (e.g. "LRU Name", "Project", "Test Rig")
        self.values_label.setText(active or "VALUES")
        col = self._get_filter_col(active) if active else None
        if not col or self.df.empty:
            return
        counts = self.df[col].value_counts()
        for val, cnt in counts.items():
            item = QListWidgetItem(f"{val}  ({cnt})")
            item.setData(Qt.ItemDataRole.UserRole,     str(val))
            item.setData(Qt.ItemDataRole.UserRole + 1, int(cnt))
            # Colour result values
            if active == "Result":
                item.setForeground(QColor(RESULT_COLORS.get(str(val), TEXT_MUTED)))
            self.values_list.addItem(item)

    def _refresh_all(self) -> None:
        df = self._get_filtered_df()
        n  = len(df)

        # ── Result distribution card ──────────────────────────────────────
        col_res = _col(df, "results") if not df.empty else None
        counts  = {}
        if col_res and not df.empty:
            counts = {k: int(v) for k, v in df[col_res].value_counts().items()}
        self.result_card.refresh(counts, n)

        # Update header label
        if self._selected_value:
            self.table_title_lbl.setText(
                f"RECORDS  ·  {self._selected_value}  ·  {n} rows"
            )
        else:
            self.table_title_lbl.setText(f"RECORDS  ·  all {n} rows")

        # ── Cross-breakdown cards ─────────────────────────────────────────
        active_filter = self._get_active_filter()
        for dim_label, card in self.cross_cards.items():
            # Always show card; grey out if it matches active filter
            if dim_label == active_filter:
                card.clear()
                continue
            col = self._get_cross_col(dim_label)
            if not col or df.empty or col not in df.columns:
                card.clear()
                continue
            top_counts = {
                str(k): int(v)
                for k, v in df[col].value_counts().head(6).items()
            }
            card.refresh(top_counts, n)

        # ── Table ─────────────────────────────────────────────────────────
        self._refresh_sub_table()

    def _refresh_sub_table(self) -> None:
        df = self._get_filtered_df()
        if df.empty:
            self.sub_table.setRowCount(0)
            self.sub_table.setColumnCount(0)
            self._update_pagination(0)
            return

        if self._sort_col and self._sort_col in df.columns:
            df = df.sort_values(by=self._sort_col, ascending=self._sort_asc, na_position="last")

        self._table_df   = df.reset_index(drop=True)
        self._table_cols = list(df.columns)

        total = len(df)
        start = self._page * self._page_size
        end   = min(start + self._page_size, total)
        page_df = df.iloc[start:end]

        col_res = _col(df, "results")

        self.sub_table.setRowCount(len(page_df))
        self.sub_table.setColumnCount(len(self._table_cols))
        self.sub_table.setHorizontalHeaderLabels(self._table_cols)

        for i, (_, row) in enumerate(page_df.iterrows()):
            for j, c in enumerate(self._table_cols):
                val  = row.get(c)
                text = str(val) if pd.notna(val) else ""
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c == col_res and text in RESULT_COLORS:
                    item.setForeground(QColor(RESULT_COLORS[text]))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.sub_table.setItem(i, j, item)

        self.sub_table.resizeColumnsToContents()
        self._update_pagination(total)

    def _update_pagination(self, total: int) -> None:
        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        self._page  = max(0, min(self._page, total_pages - 1))
        start = self._page * self._page_size + 1
        end   = min((self._page + 1) * self._page_size, total)
        self.pag_label.setText(f"{start}–{end} / {total}")
        self.pag_prev.setEnabled(self._page > 0)
        self.pag_next.setEnabled(self._page < total_pages - 1)

    def _set_page(self, p: int) -> None:
        self._page = max(0, p)
        self._refresh_sub_table()

    # ── Public API ────────────────────────────────────────────────────────────
    def set_data(self, df: pd.DataFrame) -> None:
        """Load a new DataFrame into the panel."""
        self.df = df.copy() if not df.empty else pd.DataFrame()
        if self.filter_btns:
            self.filter_btns[0][1].setChecked(True)
            for _, btn in self.filter_btns[1:]:
                btn.setChecked(False)
        self._selected_value = None
        self._sort_col       = None
        self._sort_asc       = True
        self._page           = 0
        self._refresh_values_list()
        self._refresh_all()

    def set_filter(self, entity: str, value: str) -> None:
        """Programmatically select a filter key and value."""
        for label, btn in self.filter_btns:
            btn.setChecked(label == entity)
        self._selected_value = value
        self._page = 0
        self._refresh_values_list()
        for i in range(self.values_list.count()):
            item = self.values_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == value:
                self.values_list.setCurrentItem(item)
                break
        self._refresh_all()
