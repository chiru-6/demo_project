"""Dashboard view: KPIs, filters, charts, and clickable insights."""

import pandas as pd
from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QBarSeries,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class DashboardWidget(QWidget):
    """Dashboard with KPIs, filters, charts, and clickable insight cards."""

    open_dataset_filtered = Signal(str, str)  # project, test_rig

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self._stats = {}
        self._kpi_cards = []  # list of (value_label, change_label) for refresh
        self._insight_project_map = {}  # widget -> project name for click
        self._insight_rig_map = {}
        self.init_ui()

    def init_ui(self) -> None:
        self.setObjectName("dashboardRoot")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 12, 16, 16)

        # Title row + filters (top right)
        top_row = QHBoxLayout()
        title = QLabel("📊 Dashboard — Test Data Overview")
        title.setObjectName("dashboardTitle")
        title.setStyleSheet("margin: 0px; padding: 0px;")
        top_row.addWidget(title)
        top_row.addStretch()
        # Filters panel
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersPanel")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(8)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.addWidget(QLabel("Project:"))
        self.filter_project = QComboBox()
        self.filter_project.setMinimumWidth(140)
        self.filter_project.addItem("All")
        filters_layout.addWidget(self.filter_project)
        filters_layout.addWidget(QLabel("Test Rig:"))
        self.filter_rig = QComboBox()
        self.filter_rig.setMinimumWidth(140)
        self.filter_rig.addItem("All")
        filters_layout.addWidget(self.filter_rig)
        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("refreshBtn")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_filters_and_refresh)
        filters_layout.addWidget(apply_btn)
        top_row.addWidget(filters_frame)
        main_layout.addLayout(top_row)

        # KPI cards (with change indicators)
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(16, 12, 16, 12)
        self._kpi_cards = []
        for _ in ("total", "ok", "not_ok"):
            card = self._create_kpi_card("—", "Label", "🟢 —")
            stats_layout.addWidget(card)
        main_layout.addWidget(stats_frame)

        # AI insight box
        self.ai_insight_label = QLabel(
            'AI Insight: Load data to see recommendations.'
        )
        self.ai_insight_label.setObjectName("aiInsightBox")
        self.ai_insight_label.setWordWrap(True)
        main_layout.addWidget(self.ai_insight_label)

        # Charts section (3 charts in a row or stacked)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)
        self.chart_ok_vs_notok = self._create_chart_placeholder("OK vs NOT OK")
        self.chart_test_type = self._create_chart_placeholder("Test Type Distribution")
        self.chart_trend = self._create_chart_placeholder("Monthly Trend")
        charts_layout.addWidget(self.chart_ok_vs_notok, 1)
        charts_layout.addWidget(self.chart_test_type, 1)
        charts_layout.addWidget(self.chart_trend, 1)
        main_layout.addLayout(charts_layout)

        # Insight cards (clickable)
        insights_layout = QHBoxLayout()
        insights_layout.setSpacing(12)
        insights_layout.addWidget(
            self._create_clickable_insight_card(
                "Top Projects", "", "project"
            )
        )
        insights_layout.addWidget(
            self._create_clickable_insight_card(
                "Top Test Rigs", "", "test_rig"
            )
        )
        insights_layout.addWidget(
            self._create_clickable_insight_card(
                "Top Test Types", "", None
            )
        )
        main_layout.addLayout(insights_layout)

        self._apply_styles()
        self.refresh_data()

    def _create_chart_placeholder(self, title: str) -> QFrame:
        """Create a frame that will hold a QChartView; chart built in refresh_data."""
        frame = QFrame()
        frame.setObjectName("chartFrame")
        frame.setMinimumHeight(220)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 8, 8, 8)
        lab = QLabel(title)
        lab.setObjectName("chartTitle")
        lay.addWidget(lab)
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(180)
        lay.addWidget(chart_view)
        frame.chart = chart
        frame.chart_view = chart_view
        return frame

    def _create_kpi_card(
        self, value: str, label: str, change: str
    ) -> QFrame:
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        value_label = QLabel(value)
        value_label.setObjectName("statCardValue")
        value_label.setAlignment(Qt.AlignCenter)
        change_label = QLabel(change)
        change_label.setObjectName("statCardChange")
        change_label.setAlignment(Qt.AlignCenter)
        label_label = QLabel(label)
        label_label.setObjectName("statCardLabel")
        label_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)
        card_layout.addWidget(change_label)
        card_layout.addWidget(label_label)
        container_layout.addWidget(card)
        self.add_shadow(card)
        self._kpi_cards.append((value_label, change_label, label_label))
        return container

    def _create_clickable_insight_card(
        self, title: str, body: str, filter_type: str
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("insightCard")
        card.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("insightTitle")
        body_label = QLabel(body or "—")
        body_label.setObjectName("insightBody")
        body_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(body_label)
        self.add_shadow(card)
        if filter_type == "project":
            card.menu_type = "project"
            card.menu_value = None
        elif filter_type == "test_rig":
            card.menu_type = "test_rig"
            card.menu_value = None
        else:
            card.menu_type = None
            card.menu_value = None
        card.body_label = body_label
        card._project = ""
        card._test_rig = ""
        card.installEventFilter(self)
        return card

    def eventFilter(self, obj, event) -> None:
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            if obj.objectName() == "insightCard" and hasattr(obj, "_project"):
                self.open_dataset_filtered.emit(
                    getattr(obj, "_project", "") or "",
                    getattr(obj, "_test_rig", "") or "",
                )
                return True
        return super().eventFilter(obj, event)

    def _apply_filters_and_refresh(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        try:
            self._stats = self.db.get_statistics()
        except Exception:
            self._stats = {}
        try:
            df = self.db.get_all_data()
            proj_sel = self.filter_project.currentText()
            rig_sel = self.filter_rig.currentText()
            if proj_sel and proj_sel != "All" and "project" in df.columns:
                df = df[df["project"] == proj_sel]
            if rig_sel and rig_sel != "All" and "test_rig" in df.columns:
                df = df[df["test_rig"] == rig_sel]
        except Exception:
            df = pd.DataFrame()
        total = len(df)
        results = df.get("results_remarks", pd.Series())
        if not results.empty:
            vc = results.value_counts()
            ok_count = int(vc.get("OK", 0))
            not_ok_count = int(sum(vc.get(k, 0) for k in vc.index if "NOT" in str(k).upper()))
            if not not_ok_count:
                not_ok_count = max(0, total - ok_count)
        else:
            ok_count = not_ok_count = 0
        change_total = "+12%"
        change_ok = "+5%" if ok_count else "—"
        change_not_ok = "-2%" if not_ok_count else "—"
        cards = self._kpi_cards
        if len(cards) >= 3:
            cards[0][0].setText(str(total))
            cards[0][1].setText(f"🟢 {change_total}")
            cards[0][2].setText("Total Records")
            cards[1][0].setText(str(ok_count))
            cards[1][1].setText(f"🟢 {change_ok}")
            cards[1][2].setText("OK")
            cards[2][0].setText(str(not_ok_count))
            cards[2][1].setText(f"🔴 {change_not_ok}")
            cards[2][2].setText("NOT OK")
        proj = df["project"].value_counts().to_dict() if "project" in df.columns and not df.empty else self._stats.get("projects", {})
        rigs = df["test_rig"].value_counts().to_dict() if "test_rig" in df.columns and not df.empty else self._stats.get("test_rigs", {})
        types = df["type_of_test"].value_counts().to_dict() if "type_of_test" in df.columns and not df.empty else self._stats.get("test_types", {})
        top_projects = "\n".join(
            f"{k} ({v})" for k, v in list(proj.items())[:5]
        ) or "—"
        top_rigs = "\n".join(
            f"{k} ({v})" for k, v in list(rigs.items())[:5]
        ) or "—"
        top_types = "\n".join(
            f"{k} ({v})" for k, v in list(types.items())[:5]
        ) or "—"
        insight_cards = self.findChildren(QFrame, "insightCard")
        for w in insight_cards:
            if hasattr(w, "body_label"):
                tit = w.findChild(QLabel, "insightTitle")
                if tit:
                    if "Project" in tit.text():
                        w.body_label.setText(top_projects)
                        first = (top_projects.split("\n")[0].split("(")[0].strip()
                                 if top_projects and top_projects != "—" else "")
                        w._project = first
                        w._test_rig = ""
                    elif "Test Rig" in tit.text():
                        w.body_label.setText(top_rigs)
                        first = (top_rigs.split("\n")[0].split("(")[0].strip()
                                 if top_rigs and top_rigs != "—" else "")
                        w._project = ""
                        w._test_rig = first
                    elif "Test Type" in tit.text():
                        w.body_label.setText(top_types)
                        w._project = ""
                        w._test_rig = ""
        self._update_filter_combos()
        self._build_charts(df)
        self._update_ai_insight(df, total, ok_count)
    def _update_filter_combos(self) -> None:
        proj = list(self._stats.get("projects", {}).keys())
        rigs = list(self._stats.get("test_rigs", {}).keys())
        self.filter_project.clear()
        self.filter_project.addItem("All")
        self.filter_project.addItems(sorted(proj))
        self.filter_rig.clear()
        self.filter_rig.addItem("All")
        self.filter_rig.addItems(sorted(rigs))

    def _build_charts(self, df: pd.DataFrame) -> None:
        for frame in (
            self.chart_ok_vs_notok,
            self.chart_test_type,
            self.chart_trend,
        ):
            ch = frame.chart
            ch.removeAllSeries()
            if ch.axisX():
                ch.removeAxis(ch.axisX())
            if ch.axisY():
                ch.removeAxis(ch.axisY())
        if df.empty:
            return
        # OK vs NOT OK bar
        results = df.get("results_remarks", pd.Series())
        if not results.empty:
            vc = results.value_counts()
            ok = int(vc.get("OK", 0))
            not_ok = int(sum(vc.get(k, 0) for k in vc.index if "NOT" in str(k)))
            if not not_ok:
                not_ok = int(vc.sum() - ok)
            bar_set = QBarSet("Count")
            bar_set.append([ok, not_ok])
            series = QBarSeries()
            series.append(bar_set)
            self.chart_ok_vs_notok.chart.addSeries(series)
            self.chart_ok_vs_notok.chart.setTitle("OK vs NOT OK")
            ax_x = QBarCategoryAxis()
            ax_x.append(["OK", "NOT OK"])
            self.chart_ok_vs_notok.chart.addAxis(ax_x, Qt.AlignBottom)
            series.attachAxis(ax_x)
            ax_y = QValueAxis()
            ax_y.setLabelFormat("%d")
            self.chart_ok_vs_notok.chart.addAxis(ax_y, Qt.AlignLeft)
            series.attachAxis(ax_y)
        # Test type pie
        tt = df.get("type_of_test", pd.Series())
        if not tt.empty:
            vc = tt.value_counts().head(6)
            pie = QPieSeries()
            for k, v in vc.items():
                pie.append(str(k), int(v))
            self.chart_test_type.chart.addSeries(pie)
            self.chart_test_type.chart.setTitle("Test Type Distribution")
        # Monthly trend (by date_of_pi or created_at)
        col = "date_of_pi" if "date_of_pi" in df.columns else "created_at"
        if col in df.columns and not df[col].empty:
            s = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dropna()
            if not s.empty:
                monthly = s.dt.to_period("M").value_counts().sort_index()
                line = QLineSeries()
                for i, (period, count) in enumerate(monthly.items()):
                    line.append(i, int(count))
                self.chart_trend.chart.addSeries(line)
                self.chart_trend.chart.setTitle("Monthly Trend")
                ax_y = QValueAxis()
                ax_y.setLabelFormat("%d")
                self.chart_trend.chart.addAxis(ax_y, Qt.AlignLeft)
                line.attachAxis(ax_y)
                ax_x = QValueAxis()
                ax_x.setLabelFormat("%d")
                self.chart_trend.chart.addAxis(ax_x, Qt.AlignBottom)
                line.attachAxis(ax_x)

    def _update_ai_insight(
        self, df: pd.DataFrame, total: int, ok_count: int
    ) -> None:
        if total == 0:
            self.ai_insight_label.setText(
                "AI Insight: Add data to see recommendations."
            )
            return
        pct = (ok_count / total * 100) if total else 0
        self.ai_insight_label.setText(
            f'AI Insight: {pct:.0f}% of tests are OK. '
            'Review NOT OK entries in Dataset for follow-up.'
        )

    def add_shadow(self, widget: QFrame) -> None:
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
        #dashboardRoot { background-color: #f8fafc; }
        #dashboardTitle { font-size: 24px; font-weight: bold; color: #1f2937; }
        #statsFrame { background: white; border-radius: 14px; border: 1px solid #e5e7eb; }
        #statCard {
            background-color: #e0e7ff; border-radius: 12px; padding: 12px;
            font-weight: bold; color: #4f46e5;
        }
        #statCard:hover { background-color: #c7d2fe; }
        #statCardValue { font-size: 28px; font-weight: 700; color: #1f2937; }
        #statCardChange { font-size: 12px; color: #059669; }
        #statCardLabel { font-size: 13px; color: #6b7280; }
        #filtersPanel { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; }
        #aiInsightBox {
            background: #e0e7ff; color: #3730a3; border-radius: 10px;
            padding: 12px; font-size: 13px; border: 1px solid #c7d2fe;
        }
        #chartFrame { background: white; border-radius: 12px; border: 1px solid #e5e7eb; }
        #chartTitle { font-weight: 600; color: #374151; }
        #insightCard {
            background: white; border-radius: 14px; padding: 14px;
            border: 1px solid #e5e7eb;
        }
        #insightCard:hover { background-color: #f9fafb; }
        #insightTitle { font-weight: bold; font-size: 14px; color: #374151; }
        #insightBody { font-size: 13px; color: #1f2937; }
        """)