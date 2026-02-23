"""Visualizations view: Qt Charts for test data analysis."""

import pandas as pd
from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class VisualizationsWidget(QWidget):
    """Widget for displaying data visualizations using Qt Charts."""

    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self.df = pd.DataFrame()
        self.init_ui()
        self.refresh_data()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("📈 Data Visualizations")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Select Visualization:"))
        self.viz_combo = QComboBox()
        self.viz_combo.addItems([
            "Results Distribution",
            "Test Rigs Analysis",
            "Projects Overview",
            "Division/Group Distribution",
            "Type of Test Analysis",
            "System Distribution",
            "Clearance Status",
        ])
        self.viz_combo.currentTextChanged.connect(self.update_visualization)
        controls_layout.addWidget(self.viz_combo)
        controls_layout.addWidget(QLabel("Year:"))
        self.filter_year = QComboBox()
        self.filter_year.setMinimumWidth(90)
        self.filter_year.addItem("All")
        controls_layout.addWidget(self.filter_year)
        controls_layout.addWidget(QLabel("Month:"))
        self.filter_month = QComboBox()
        self.filter_month.setMinimumWidth(100)
        self.filter_month.addItem("All")
        controls_layout.addWidget(self.filter_month)
        self.filter_year.currentTextChanged.connect(self._apply_date_filter)
        self.filter_month.currentTextChanged.connect(self._apply_date_filter)
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(refresh_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view)

    def refresh_data(self) -> None:
        try:
            self.df = self.db.get_all_data()
            self.filter_year.blockSignals(True)
            self.filter_month.blockSignals(True)
            self._populate_date_filters()
            self.filter_year.blockSignals(False)
            self.filter_month.blockSignals(False)
            self._apply_date_filter()
        except Exception as error:
            self.show_error_chart(str(error))

    def _populate_date_filters(self) -> None:
        col = "date_of_pi" if "date_of_pi" in self.df.columns else "created_at"
        self.filter_year.clear()
        self.filter_year.addItem("All")
        self.filter_month.clear()
        self.filter_month.addItem("All")
        if col in self.df.columns and not self.df.empty:
            s = pd.to_datetime(self.df[col], errors="coerce", dayfirst=True).dropna()
            if not s.empty:
                years = sorted(s.dt.year.unique().astype(int).tolist())
                self.filter_year.addItems(map(str, years))
                months = [(i, ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][i-1]) for i in range(1, 13)]
                for i, name in months:
                    self.filter_month.addItem(f"{i:02d} - {name}", i)

    def _apply_date_filter(self) -> None:
        df = self.db.get_all_data()
        year_sel = self.filter_year.currentText()
        month_sel = self.filter_month.currentText()
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
        self.df = df
        self.update_visualization()

    def _is_dark_mode(self) -> bool:
        mw = self.window()
        return bool(getattr(mw, "is_dark_mode", lambda: False)())

    def _apply_chart_theme(self, dark: bool) -> None:
        if dark:
            self.chart.setTheme(QChart.ChartThemeDark)
        else:
            self.chart.setTheme(QChart.ChartThemeLight)

    def update_visualization(self) -> None:
        if self.df.empty:
            self.show_error_chart("No data available")
            return
        viz_type = self.viz_combo.currentText()
        dark = self._is_dark_mode()
        self.chart.removeAllSeries()
        if self.chart.axisX():
            self.chart.removeAxis(self.chart.axisX())
        if self.chart.axisY():
            self.chart.removeAxis(self.chart.axisY())
        self._apply_chart_theme(dark)
        try:
            if viz_type == "Results Distribution":
                self._build_results_pie()
            elif viz_type == "Test Rigs Analysis":
                self._build_bar_from_counts("test_rig", "Test Rigs Usage")
            elif viz_type == "Projects Overview":
                self._build_bar_from_counts("project", "Projects Distribution")
            elif viz_type == "Division/Group Distribution":
                self._build_divisions_pie()
            elif viz_type == "Type of Test Analysis":
                self._build_bar_from_counts(
                    "type_of_test", "Type of Test Distribution"
                )
            elif viz_type == "System Distribution":
                self._build_bar_from_counts("system", "System Distribution")
            elif viz_type == "Clearance Status":
                self._build_clearance_bar()
        except Exception as error:
            self.show_error_chart(f"Error creating visualization: {str(error)}")

    def _build_results_pie(self) -> None:
        results_counts = self.df["results_remarks"].value_counts()
        if results_counts.empty:
            self.show_error_chart("No results_remarks data")
            return
        series = QPieSeries()
        for label, value in results_counts.items():
            slice_ = series.append(str(label), int(value))
            slice_.setLabelVisible(True)
            if str(label) in ("NOT OK", "Under Review"):
                slice_.setExploded(True)
        self.chart.addSeries(series)
        self.chart.setTitle("Test Results Distribution")

    def _build_divisions_pie(self) -> None:
        div_counts = self.df["division_group"].value_counts()
        if div_counts.empty:
            self.show_error_chart("No division/group data")
            return
        series = QPieSeries()
        for label, value in div_counts.items():
            slice_ = series.append(str(label), int(value))
            slice_.setLabelVisible(True)
        self.chart.addSeries(series)
        self.chart.setTitle("Division/Group Distribution")

    def _build_bar_from_counts(self, column: str, title: str) -> None:
        if column not in self.df.columns:
            self.show_error_chart(f"No '{column}' column")
            return
        counts = self.df[column].value_counts()
        if counts.empty:
            self.show_error_chart(f"No data in '{column}'")
            return
        categories = [str(k) for k in counts.index]
        values = [int(v) for v in counts.values]
        bar_set = QBarSet(column)
        bar_set.append(values)
        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)
        self.chart.setTitle(title)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("Count")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

    def _build_clearance_bar(self) -> None:
        cleared = self.df["date_of_clearance"].notna().sum()
        not_cleared = self.df["date_of_clearance"].isna().sum()
        bar_set = QBarSet("Clearance")
        bar_set.append([int(cleared), int(not_cleared)])
        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)
        self.chart.setTitle("Clearance Status")
        axis_x = QBarCategoryAxis()
        axis_x.append(["Cleared", "Not Cleared"])
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("Count")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

    def show_error_chart(self, message: str) -> None:
        self.chart.removeAllSeries()
        self.chart.setTitle(message)
