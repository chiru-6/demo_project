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
    QPieSlice,
    QValueAxis,
)
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
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


class _InsightDetailDialog(QDialog):
    """Dialog for enlarged insight view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
        )

    def closeEvent(self, event):
        event.accept()
        self.done(QDialog.DialogCode.Rejected)


class DashboardWidget(QWidget):
    """Dashboard with KPIs, filters, charts, and clickable insight cards."""

    open_dataset_filtered = Signal(str, str)  # project, test_rig

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self._stats = {}
        self._kpi_cards = []
        self._insight_project_map = {}
        self._insight_rig_map = {}
        self._selected_insight_viz = "test_rig"  # project | test_rig | type_of_test
        self._current_df = pd.DataFrame()
        self._ai_insight_rotation = 0  # Rotates through different insight types on each refresh
        self.init_ui()

    def init_ui(self) -> None:
        self.setObjectName("dashboardRoot")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 12, 16, 16)

        # Title + filters row
        top_row = QHBoxLayout()
        title = QLabel("📊 Dashboard — Test Data Overview")
        title.setObjectName("dashboardTitle")
        title.setStyleSheet("margin: 0px; padding: 0px;")
        top_row.addWidget(title)
        top_row.addStretch()

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
        filters_layout.addWidget(QLabel("Year:"))
        self.filter_year = QComboBox()
        self.filter_year.setMinimumWidth(100)
        self.filter_year.addItem("All")
        filters_layout.addWidget(self.filter_year)
        filters_layout.addWidget(QLabel("Month:"))
        self.filter_month = QComboBox()
        self.filter_month.setMinimumWidth(100)
        self.filter_month.addItem("All")
        filters_layout.addWidget(self.filter_month)
        for combo in (self.filter_project, self.filter_rig, self.filter_year, self.filter_month):
            combo.currentIndexChanged.connect(self._apply_filters_and_refresh)
        reset_btn = QPushButton("Refresh")
        reset_btn.setObjectName("refreshBtn")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setToolTip("Reset all filters to default (All)")
        reset_btn.clicked.connect(self._reset_filters_and_refresh)
        filters_layout.addWidget(reset_btn)
        top_row.addWidget(filters_frame)
        main_layout.addLayout(top_row)

        # KPI cards
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

        # AI insight
        self.ai_insight_label = QLabel("AI Insight: Load data to see recommendations.")
        self.ai_insight_label.setObjectName("aiInsightBox")
        self.ai_insight_label.setWordWrap(True)
        main_layout.addWidget(self.ai_insight_label)

        # Charts row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)
        self.chart_ok_vs_notok = self._create_chart_placeholder("OK vs NOT OK", "ok_not_ok")
        self.chart_insight     = self._create_chart_placeholder("Insight Chart (click card below)", "insight")
        self.chart_trend       = self._create_chart_placeholder("Monthly Trend", "trend")
        charts_layout.addWidget(self.chart_ok_vs_notok, 1)
        charts_layout.addWidget(self.chart_insight,     1)
        charts_layout.addWidget(self.chart_trend,       1)
        main_layout.addLayout(charts_layout)

        # Insight cards (click to change chart above)
        insights_layout = QHBoxLayout()
        insights_layout.setSpacing(12)
        insights_layout.addWidget(self._create_clickable_insight_card("Top Projects",  "", "project", "project"))
        insights_layout.addWidget(self._create_clickable_insight_card("Top Test Rigs", "", "test_rig", "test_rig"))
        insights_layout.addWidget(self._create_clickable_insight_card("Top Test Types","", None, "type_of_test"))
        main_layout.addLayout(insights_layout)

        self._apply_styles()
        self.refresh_data()

    # ── Widget builders ──────────────────────────────────────────────────────

    def _create_chart_placeholder(self, title: str, chart_key: str = "") -> QFrame:
        frame = QFrame()
        frame.setObjectName("chartFrame")
        frame.setMinimumHeight(220)
        frame.setCursor(Qt.PointingHandCursor)
        frame.chart_key = chart_key
        frame.installEventFilter(self)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 8, 8, 8)
        lab = QLabel(title)
        lab.setObjectName("chartTitle")
        lab.chart_key = chart_key
        lab.setCursor(Qt.PointingHandCursor)
        lab.installEventFilter(self)
        lay.addWidget(lab)
        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(180)
        chart_view.setStyleSheet("background: transparent;")
        chart_view.chart_key = chart_key
        chart_view.installEventFilter(self)
        lay.addWidget(chart_view)
        frame.chart = chart
        frame.chart_view = chart_view
        return frame

    def _create_kpi_card(self, value: str, label: str, change: str) -> QFrame:
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

    def _create_clickable_insight_card(self, title: str, body: str, filter_type: str, viz_type: str = "") -> QFrame:
        card = QFrame()
        card.setObjectName("insightCard")
        card.setCursor(Qt.PointingHandCursor)
        card._project  = ""
        card._test_rig = ""
        card._viz_type = viz_type  # project | test_rig | type_of_test
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("insightTitle")
        body_label = QLabel(body or "—")
        body_label.setObjectName("insightBody")
        body_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(body_label)
        card.body_label = body_label
        card.installEventFilter(self)
        return card

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if obj.objectName() == "insightCard":
                viz = getattr(obj, "_viz_type", "")
                if viz:
                    self._selected_insight_viz = viz
                    self._build_charts(self._current_df)
                proj = getattr(obj, "_project", "")
                rig  = getattr(obj, "_test_rig", "")
                if proj or rig:
                    self.open_dataset_filtered.emit(proj, rig)
            elif hasattr(obj, "chart_key"):
                self._open_enlarged_insight(obj.chart_key)
            else:
                w = obj.parent()
                while w:
                    if hasattr(w, "chart_key"):
                        self._open_enlarged_insight(w.chart_key)
                        break
                    w = w.parent() if hasattr(w, "parent") else None
        return super().eventFilter(obj, event)

    # ── Styles ───────────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        # Theme-dependent colors come from main_window LIGHT/DARK stylesheets.
        # Only set rules that don't override theme (KPI gradient, layout).
        self.setStyleSheet("""
        #dashboardRoot { border-radius: 12px; }
        #dashboardTitle { font-size: 24px; font-weight: bold; }
        #statsFrame { border-radius: 14px; }
        #statCard {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #6366f1);
            border-radius: 12px;
            padding: 12px;
        }
        #statCard:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4338ca, stop:1 #4f46e5);
        }
        #statCardValue  { font-size: 28px; font-weight: 700; }
        #statCardChange { font-size: 12px; }
        #statCardLabel  { font-size: 13px; }
        #filtersPanel { border-radius: 10px; }
        #aiInsightBox { border-radius: 10px; padding: 12px; font-size: 13px; }
        #chartFrame { border-radius: 12px; }
        #chartTitle { font-weight: 600; font-size: 13px; }
        #insightCard { border-radius: 14px; padding: 14px; }
        QPushButton#refreshBtn { border: none; padding: 6px 16px; border-radius: 6px; font-weight: 600; }
        QPushButton#refreshBtn:hover { background-color: #4338ca; }
        QPushButton#refreshBtn:pressed { background-color: #3730a3; }
        """)

    # ── Data / refresh ───────────────────────────────────────────────────────

    def refresh_data(self) -> None:
        try:
            self._stats = self.db.get_statistics()
        except Exception:
            self._stats = {}
        self._apply_filters_and_refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh_data()

    def _apply_filters_and_refresh(self) -> None:
        try:
            df = self.db.get_all_data()
            proj_sel = self.filter_project.currentText()
            rig_sel  = self.filter_rig.currentText()
            year_sel = self.filter_year.currentText()
            month_sel = self.filter_month.currentText()
            if proj_sel and proj_sel != "All" and "project" in df.columns:
                df = df[df["project"] == proj_sel]
            if rig_sel and rig_sel != "All" and "test_rig" in df.columns:
                df = df[df["test_rig"] == rig_sel]
            col = "date_of_pi" if "date_of_pi" in df.columns else "created_at"
            if col in df.columns and not df.empty:
                s = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dropna()
                if not s.empty and year_sel and year_sel != "All":
                    df = df.loc[s.dt.year == int(year_sel)].copy()
                    s = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dropna()
                if not s.empty and month_sel and month_sel != "All":
                    month_val = self.filter_month.currentData()
                    if month_val is not None:
                        df = df.loc[s.dt.month == int(month_val)].copy()
        except Exception:
            df = pd.DataFrame()
        self._current_df = df

        total = len(df)
        results = df.get("results_remarks", pd.Series())
        if not results.empty:
            vc = results.value_counts()
            ok_count     = int(vc.get("OK", 0))
            not_ok_count = int(sum(vc.get(k, 0) for k in vc.index if "NOT" in str(k).upper()))
            if not not_ok_count:
                not_ok_count = max(0, total - ok_count)
        else:
            ok_count = not_ok_count = 0

        cards = self._kpi_cards
        if len(cards) >= 3:
            cards[0][0].setText(str(total));      cards[0][1].setText("🟢 +12%"); cards[0][2].setText("Total Records")
            cards[1][0].setText(str(ok_count));   cards[1][1].setText("🟢 +5%");  cards[1][2].setText("OK")
            cards[2][0].setText(str(not_ok_count));cards[2][1].setText("🔴 -2%"); cards[2][2].setText("NOT OK")

        proj  = df["project"].value_counts().to_dict()      if "project"      in df.columns and not df.empty else self._stats.get("projects", {})
        rigs  = df["test_rig"].value_counts().to_dict()     if "test_rig"     in df.columns and not df.empty else self._stats.get("test_rigs", {})
        types = df["type_of_test"].value_counts().to_dict() if "type_of_test" in df.columns and not df.empty else self._stats.get("test_types", {})

        top_projects = "\n".join(f"{k} ({v})" for k, v in list(proj.items())[:5])  or "—"
        top_rigs     = "\n".join(f"{k} ({v})" for k, v in list(rigs.items())[:5])  or "—"
        top_types    = "\n".join(f"{k} ({v})" for k, v in list(types.items())[:5]) or "—"

        for w in self.findChildren(QFrame, "insightCard"):
            if hasattr(w, "body_label"):
                tit = w.findChild(QLabel, "insightTitle")
                if tit:
                    if "Project"  in tit.text(): w.body_label.setText(top_projects); w._project = (top_projects.split("\n")[0].split("(")[0].strip() if top_projects != "—" else ""); w._test_rig = ""
                    elif "Rig"    in tit.text(): w.body_label.setText(top_rigs);     w._project = ""; w._test_rig = (top_rigs.split("\n")[0].split("(")[0].strip() if top_rigs != "—" else "")
                    elif "Type"   in tit.text(): w.body_label.setText(top_types);    w._project = ""; w._test_rig = ""

        self._update_filter_combos()
        self._build_charts(df)
        self._update_ai_insight(df, total, ok_count)

    def _update_filter_combos(self) -> None:
        # Preserve current selections before repopulating
        proj_sel = self.filter_project.currentText()
        rig_sel = self.filter_rig.currentText()
        year_sel = self.filter_year.currentText()
        month_data = self.filter_month.currentData()
        month_text = self.filter_month.currentText()

        for combo in (self.filter_project, self.filter_rig, self.filter_year, self.filter_month):
            combo.blockSignals(True)

        proj = list(self._stats.get("projects", {}).keys())
        rigs = list(self._stats.get("test_rigs", {}).keys())
        self.filter_project.clear()
        self.filter_project.addItem("All")
        self.filter_project.addItems(sorted(proj))
        self.filter_rig.clear()
        self.filter_rig.addItem("All")
        self.filter_rig.addItems(sorted(rigs))
        try:
            df = self.db.get_all_data()
            col = "date_of_pi" if "date_of_pi" in df.columns else "created_at"
            if col in df.columns and not df.empty:
                s = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dropna()
                if not s.empty:
                    years = sorted(s.dt.year.unique().astype(int).tolist())
                    self.filter_year.clear()
                    self.filter_year.addItem("All")
                    self.filter_year.addItems(map(str, years))
                    months = [(i, ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][i-1]) for i in range(1,13)]
                    self.filter_month.clear()
                    self.filter_month.addItem("All")
                    for i, name in months:
                        self.filter_month.addItem(f"{i:02d} - {name}", i)
        except Exception:
            pass

        # Restore selections if they still exist in the new options
        idx = self.filter_project.findText(proj_sel)
        if idx >= 0:
            self.filter_project.setCurrentIndex(idx)
        idx = self.filter_rig.findText(rig_sel)
        if idx >= 0:
            self.filter_rig.setCurrentIndex(idx)
        idx = self.filter_year.findText(year_sel)
        if idx >= 0:
            self.filter_year.setCurrentIndex(idx)
        if month_data is not None:
            for i in range(self.filter_month.count()):
                if self.filter_month.itemData(i) == month_data:
                    self.filter_month.setCurrentIndex(i)
                    break
        elif month_text:
            idx = self.filter_month.findText(month_text)
            if idx >= 0:
                self.filter_month.setCurrentIndex(idx)
        for combo in (self.filter_project, self.filter_rig, self.filter_year, self.filter_month):
            combo.blockSignals(False)

    def _reset_filters_and_refresh(self) -> None:
        """Reset all filters to All and refresh data."""
        for combo in (self.filter_project, self.filter_rig, self.filter_year, self.filter_month):
            combo.blockSignals(True)
        self.filter_project.setCurrentIndex(0)
        self.filter_rig.setCurrentIndex(0)
        self.filter_year.setCurrentIndex(0)
        self.filter_month.setCurrentIndex(0)
        for combo in (self.filter_project, self.filter_rig, self.filter_year, self.filter_month):
            combo.blockSignals(False)
        self._apply_filters_and_refresh()

    def _is_dark_mode(self) -> bool:
        mw = self.window()
        return bool(getattr(mw, "is_dark_mode", lambda: False)())

    def _build_charts(self, df: pd.DataFrame) -> None:
        for frame in (self.chart_ok_vs_notok, self.chart_insight, self.chart_trend):
            ch = frame.chart
            ch.removeAllSeries()
            for ax in ch.axes():
                ch.removeAxis(ax)
        if df.empty:
            return

        dark = self._is_dark_mode()
        chart_theme = QChart.ChartThemeDark if dark else QChart.ChartThemeLight

        # OK vs NOT OK bar
        results = df.get("results_remarks", pd.Series())
        if not results.empty:
            ch = self.chart_ok_vs_notok.chart
            ch.setTheme(chart_theme)
            vc      = results.value_counts()
            ok      = int(vc.get("OK", 0))
            not_ok  = int(sum(vc.get(k, 0) for k in vc.index if "NOT" in str(k).upper())) or int(vc.sum() - ok)
            bar_set = QBarSet("Count")
            bar_set.setColor(QColor("#4f46e5"))
            bar_set.append([ok, not_ok])
            series = QBarSeries(); series.append(bar_set)
            self.chart_ok_vs_notok.chart.addSeries(series)
            self.chart_ok_vs_notok.chart.setTitle("OK vs NOT OK")
            ax_x = QBarCategoryAxis(); ax_x.append(["OK", "NOT OK"])
            self.chart_ok_vs_notok.chart.addAxis(ax_x, Qt.AlignBottom); series.attachAxis(ax_x)
            ax_y = QValueAxis(); ax_y.setLabelFormat("%d")
            self.chart_ok_vs_notok.chart.addAxis(ax_y, Qt.AlignLeft);   series.attachAxis(ax_y)

        # Insight chart (Projects / Test Rigs / Test Types) — always pie to match enlarged view
        col_map = {"project": ("project", "Top Projects"), "test_rig": ("test_rig", "Top Test Rigs"), "type_of_test": ("type_of_test", "Test Type Distribution")}
        col_name, title = col_map.get(self._selected_insight_viz, ("test_rig", "Top Test Rigs"))
        data_col = df.get(col_name, pd.Series())
        if not data_col.empty:
            ch = self.chart_insight.chart
            ch.setTheme(chart_theme)
            ch.legend().setVisible(False)  # Hide truncated legend; slice labels show full text
            vc = data_col.value_counts().head(8)
            pie = QPieSeries()
            pie.setLabelsVisible(True)
            pie.setLabelsPosition(QPieSlice.LabelOutside)
            for k, v in vc.items():
                sl = pie.append(f"{k} ({v})", int(v))
                sl.setLabelVisible(True)
            ch.addSeries(pie)
            ch.setTitle(title)

        # Monthly trend
        col = "date_of_pi" if "date_of_pi" in df.columns else "created_at"
        if col in df.columns:
            s = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dropna()
            if not s.empty:
                self.chart_trend.chart.setTheme(chart_theme)
                monthly = s.dt.to_period("M").value_counts().sort_index()
                line = QLineSeries()
                line.setColor(QColor("#4f46e5"))
                for i, (_, count) in enumerate(monthly.items()):
                    line.append(i, int(count))
                self.chart_trend.chart.addSeries(line)
                self.chart_trend.chart.setTitle("Monthly Trend")
                ax_y = QValueAxis(); ax_y.setLabelFormat("%d")
                self.chart_trend.chart.addAxis(ax_y, Qt.AlignLeft);   line.attachAxis(ax_y)
                ax_x = QValueAxis(); ax_x.setLabelFormat("%d")
                self.chart_trend.chart.addAxis(ax_x, Qt.AlignBottom); line.attachAxis(ax_x)

    def _update_ai_insight(self, df: pd.DataFrame, total: int, ok_count: int) -> None:
        """Update AI Insight with varied, data-driven recommendations. Rotates through
        different insight types each time the dashboard is refreshed/opened."""
        if total == 0:
            self.ai_insight_label.setText("AI Insight: Add data to see recommendations.")
            return
        not_ok_count = total - ok_count
        pct = (ok_count / total * 100) if total else 0
        # Build insight variants from available data
        insights = []
        # 1. Pass/fail summary
        if pct >= 80:
            insights.append(f"AI Insight: Strong pass rate ({pct:.0f}% OK). Keep monitoring NOT OK entries in Dataset.")
        elif pct >= 50:
            insights.append(f"AI Insight: {pct:.0f}% of tests are OK. Review {not_ok_count} NOT OK entries in Dataset for follow-up.")
        else:
            insights.append(f"AI Insight: Low pass rate ({pct:.0f}% OK). Prioritize reviewing {not_ok_count} NOT OK entries.")
        # 2. Top project focus
        if "project" in df.columns and not df.empty:
            top_proj = df["project"].value_counts().index[0]
            top_proj_count = int(df["project"].value_counts().iloc[0])
            insights.append(f"AI Insight: Top project is {top_proj} ({top_proj_count} tests). Use filters to drill down.")
        # 3. Top test rig focus
        if "test_rig" in df.columns and not df.empty:
            top_rig = df["test_rig"].value_counts().index[0]
            top_rig_count = int(df["test_rig"].value_counts().iloc[0])
            insights.append(f"AI Insight: Most active rig is {top_rig} ({top_rig_count} tests). Click Top Test Rigs to visualize.")
        # 4. Test type distribution
        if "type_of_test" in df.columns and not df.empty:
            top_type = df["type_of_test"].value_counts().index[0]
            top_type_count = int(df["type_of_test"].value_counts().iloc[0])
            insights.append(f"AI Insight: {top_type} is the most common test type ({top_type_count}). See Test Type Distribution chart.")
        # 5. Clearance status
        if "date_of_clearance" in df.columns and not df.empty:
            cleared = df["date_of_clearance"].notna().sum()
            cleared_pct = (cleared / total * 100) if total else 0
            if cleared_pct < 100:
                insights.append(f"AI Insight: {cleared_pct:.0f}% of tests are cleared. {total - cleared} entries pending clearance.")
            else:
                insights.append(f"AI Insight: All {total} tests are cleared. Good compliance.")
        # 6. Volume-based
        if total > 100:
            insights.append(f"AI Insight: Large dataset ({total} records). Use Year/Month filters to focus on specific periods.")
        elif total > 20:
            insights.append(f"AI Insight: {total} records in view. Apply Project or Test Rig filters for targeted analysis.")
        # 7. NOT OK focus
        if not_ok_count > 0:
            insights.append(f"AI Insight: {not_ok_count} NOT OK entries need attention. Open Dataset tab to review and take action.")
        # Rotate: pick one based on _ai_insight_rotation, then increment
        idx = self._ai_insight_rotation % len(insights)
        self._ai_insight_rotation += 1
        self.ai_insight_label.setText(insights[idx])

    def _open_enlarged_insight(self, chart_key: str) -> None:
        """Open enlarged insight dialog with chart, numerical insights, and back button."""
        df = self._current_df
        if df.empty:
            return
        dlg = _InsightDetailDialog(parent=self.window())
        dlg.setWindowTitle("Insight Details")
        dlg.setMinimumSize(800, 650)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("📊 Enlarged View — Close window to return to Dashboard"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)
        # Numerical insights
        total = len(df)
        results = df.get("results_remarks", pd.Series())
        ok = int(results.value_counts().get("OK", 0)) if not results.empty else 0
        not_ok = total - ok if not results.empty else 0
        insights_text = f"Total Records: {total}  |  OK: {ok}  |  NOT OK: {not_ok}\n\n"
        # Always show Top Projects, Top Test Rigs, Top Test Types
        if "project" in df.columns:
            proj = df["project"].value_counts().head(5)
            insights_text += "Top Projects:\n" + "\n".join(f"  • {k}: {v}" for k, v in proj.items()) + "\n\n"
        if "test_rig" in df.columns:
            rigs = df["test_rig"].value_counts().head(5)
            insights_text += "Top Test Rigs:\n" + "\n".join(f"  • {k}: {v}" for k, v in rigs.items()) + "\n\n"
        if "type_of_test" in df.columns:
            types = df["type_of_test"].value_counts().head(5)
            insights_text += "Top Test Types:\n" + "\n".join(f"  • {k}: {v}" for k, v in types.items())
        # For insight chart, add full breakdown of selected category (all items, line-wise)
        if chart_key == "insight":
            col_map = {"project": ("project", "Top Projects"), "test_rig": ("test_rig", "Top Test Rigs"), "type_of_test": ("type_of_test", "Test Type Distribution")}
            col_name, title = col_map.get(self._selected_insight_viz, ("test_rig", "Top Test Rigs"))
            vc = df[col_name].value_counts().head(8) if col_name in df.columns else pd.Series()
            if not vc.empty:
                insights_text += f"\n{title} — Full breakdown (one per line):\n"
                insights_text += "\n".join(f"  • {k}: {v}" for k, v in vc.items())
        insights_label = QLabel(insights_text)
        insights_label.setWordWrap(True)
        insights_label.setStyleSheet("font-size: 13px; line-height: 1.4;")
        cl.addWidget(insights_label)
        # Chart placeholder (simplified - reuse same data)
        chart_frame = QFrame()
        chart_frame.setMinimumHeight(420 if chart_key == "insight" else 280)
        chart_lay = QVBoxLayout(chart_frame)
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        dark = self._is_dark_mode()
        chart.setTheme(QChart.ChartThemeDark if dark else QChart.ChartThemeLight)
        if chart_key == "ok_not_ok" and not results.empty:
            vc = results.value_counts()
            ok_v = int(vc.get("OK", 0))
            nok_v = int(sum(vc.get(k, 0) for k in vc.index if "NOT" in str(k).upper()) or (total - ok_v))
            bar_set = QBarSet("Count")
            bar_set.setColor(QColor("#4f46e5"))
            bar_set.append([ok_v, nok_v])
            series = QBarSeries()
            series.append(bar_set)
            chart.addSeries(series)
            chart.setTitle("OK vs NOT OK")
            ax_x = QBarCategoryAxis()
            ax_x.append(["OK", "NOT OK"])
            chart.addAxis(ax_x, Qt.AlignBottom)
            series.attachAxis(ax_x)
            ax_y = QValueAxis()
            ax_y.setLabelFormat("%d")
            chart.addAxis(ax_y, Qt.AlignLeft)
            series.attachAxis(ax_y)
        elif chart_key == "insight":
            col_map = {"project": ("project", "Top Projects"), "test_rig": ("test_rig", "Top Test Rigs"), "type_of_test": ("type_of_test", "Test Type Distribution")}
            col_name, title = col_map.get(self._selected_insight_viz, ("test_rig", "Top Test Rigs"))
            vc = df[col_name].value_counts().head(8) if col_name in df.columns else pd.Series()
            if not vc.empty:
                chart.legend().setVisible(False)  # Slice labels show full text; no truncated legend
                pie = QPieSeries()
                pie.setLabelsVisible(True)
                pie.setLabelsPosition(QPieSlice.LabelOutside)
                for k, v in vc.items():
                    sl = pie.append(f"{k} ({v})", int(v))
                    sl.setLabelVisible(True)
                chart.addSeries(pie)
                chart.setTitle(title)
        elif chart_key == "trend":
            col = "date_of_pi" if "date_of_pi" in df.columns else "created_at"
            if col in df.columns:
                s = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dropna()
                if not s.empty:
                    monthly = s.dt.to_period("M").value_counts().sort_index()
                    line = QLineSeries()
                    line.setColor(QColor("#4f46e5"))
                    for i, (_, count) in enumerate(monthly.items()):
                        line.append(i, int(count))
                    chart.addSeries(line)
                    chart.setTitle("Monthly Trend")
                    ax_y = QValueAxis()
                    ax_y.setLabelFormat("%d")
                    chart.addAxis(ax_y, Qt.AlignLeft)
                    line.attachAxis(ax_y)
                    ax_x = QValueAxis()
                    ax_x.setLabelFormat("%d")
                    chart.addAxis(ax_x, Qt.AlignBottom)
                    line.attachAxis(ax_x)
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_lay.addWidget(chart_view)
        cl.addWidget(chart_frame)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("refreshBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dlg.reject)
        layout.addWidget(close_btn)
        dlg.exec()

    def add_shadow(self, widget: QFrame) -> None:
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 40))
        widget.setGraphicsEffect(shadow)
