from __future__ import annotations

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QCategoryAxis,
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
)
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services import FinanceService
from ui.widgets import KpiCard


class DashboardPage(QWidget):
    INCOME_COLOR = QColor("#34d399")
    EXPENSE_COLOR = QColor("#fb7185")
    NET_COLOR = QColor("#60a5fa")
    NETWORTH_COLOR = QColor("#22d3ee")
    AXIS_LABEL_COLOR = QColor("#d1d5db")
    GRID_COLOR = QColor("#334155")
    MINOR_GRID_COLOR = QColor("#243041")
    AXIS_LINE_COLOR = QColor("#64748b")
    PLOT_BG = QColor(15, 23, 42, 160)

    def __init__(self, service: FinanceService, parent=None) -> None:
        super().__init__(parent)
        self.service = service

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(12)
        self.net_worth_card = KpiCard("Net Worth")
        self.cashflow_card = KpiCard("Monthly Cashflow")
        self.savings_card = KpiCard("Savings Rate")
        self.budget_card = KpiCard("Budget Status")

        kpi_layout.addWidget(self.net_worth_card, 0, 0)
        kpi_layout.addWidget(self.cashflow_card, 0, 1)
        kpi_layout.addWidget(self.savings_card, 0, 2)
        kpi_layout.addWidget(self.budget_card, 0, 3)
        root.addLayout(kpi_layout)

        self.cashflow_chart = QChartView()
        self.expense_chart = QChartView()
        self.networth_chart = QChartView()
        for chart_view in (self.cashflow_chart, self.expense_chart, self.networth_chart):
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(250)
            chart_view.setStyleSheet("background: transparent; border: none;")

        charts_grid = QGridLayout()
        charts_grid.setSpacing(12)
        charts_grid.addWidget(self._card_with_widget("Cashflow Over Time (6 Months)", self.cashflow_chart), 0, 0)
        charts_grid.addWidget(self._card_with_widget("Expense Breakdown (Selected Month)", self.expense_chart), 0, 1)
        charts_grid.addWidget(self._card_with_widget("Net Worth Over Time (6 Months)", self.networth_chart), 1, 0, 1, 2)
        root.addLayout(charts_grid)

        self.recent_table = QTableWidget(0, 5)
        self.recent_table.setHorizontalHeaderLabels(["Date", "Description", "Category", "Account", "Amount"])
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setSelectionMode(QTableWidget.NoSelection)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.accounts_table = QTableWidget(0, 3)
        self.accounts_table.setHorizontalHeaderLabels(["Name", "Kind", "Balance"])
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.accounts_table.setSelectionMode(QTableWidget.NoSelection)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.accounts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        tables_row = QHBoxLayout()
        tables_row.setSpacing(12)
        tables_row.addWidget(self._card_with_widget("Recent Transactions", self.recent_table))
        tables_row.addWidget(self._card_with_widget("Accounts", self.accounts_table))
        root.addLayout(tables_row)

    def refresh(self, month: str, search: str = "") -> None:
        metrics = self.service.get_dashboard_metrics(month)

        self.net_worth_card.set_values(
            self._fmt_money(metrics["net_worth"]),
            f"Assets - Debts",
        )
        self.cashflow_card.set_values(
            self._fmt_money(metrics["monthly_cashflow"]),
            f"Income {self._fmt_money(metrics['income'])} | Expense {self._fmt_money(metrics['expense'])}",
        )
        self.savings_card.set_values(
            f"{metrics['savings_rate'] * 100:.1f}%",
            "Cashflow / Income",
        )
        self.budget_card.set_values(
            f"{metrics['budget_pct'] * 100:.1f}% used",
            f"Remaining {self._fmt_money(metrics['budget_remaining'])}",
        )

        cashflow_data = self.service.get_cashflow_over_time(month, months=6)
        expense_data = self.service.get_expense_breakdown(month)
        networth_data = self.service.get_networth_over_time(month, months=6)

        self.cashflow_chart.setChart(self._build_cashflow_chart(cashflow_data))
        self.expense_chart.setChart(self._build_expense_chart(expense_data))
        self.networth_chart.setChart(self._build_networth_chart(networth_data))

        self._fill_recent_table(month, search)
        self._fill_accounts_table()

    def _fill_recent_table(self, month: str, search: str) -> None:
        rows = self.service.get_recent_transactions(month=month, search=search, limit=15)
        self.recent_table.setRowCount(len(rows))
        for row_index, tx in enumerate(rows):
            self.recent_table.setItem(row_index, 0, QTableWidgetItem(tx.date))
            self.recent_table.setItem(row_index, 1, QTableWidgetItem(tx.description))
            self.recent_table.setItem(row_index, 2, QTableWidgetItem(tx.category))
            self.recent_table.setItem(row_index, 3, QTableWidgetItem(tx.account))

            amount_item = QTableWidgetItem(self._fmt_money(tx.amount))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amount_item.setForeground(QColor("#f87171") if tx.amount < 0 else QColor("#4ade80"))
            self.recent_table.setItem(row_index, 4, amount_item)

    def _fill_accounts_table(self) -> None:
        rows = self.service.get_accounts()
        self.accounts_table.setRowCount(len(rows))
        for row_index, account in enumerate(rows):
            self.accounts_table.setItem(row_index, 0, QTableWidgetItem(account.name))
            self.accounts_table.setItem(row_index, 1, QTableWidgetItem(account.kind))
            balance_item = QTableWidgetItem(self._fmt_money(account.balance))
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if account.kind.strip().lower() in {"debt", "liability"}:
                balance_item.setForeground(QColor("#f87171"))
            else:
                balance_item.setForeground(QColor("#60a5fa"))
            self.accounts_table.setItem(row_index, 2, balance_item)

    def _build_cashflow_chart(self, rows: list[dict[str, float | str]]) -> QChart:
        chart = self._base_chart("Cashflow")
        categories = [self._month_label(str(row["month"])) for row in rows]

        specs = [
            ("Income", "income", self.INCOME_COLOR),
            ("Expense", "expense", self.EXPENSE_COLOR),
            ("Net", "net", self.NET_COLOR),
        ]
        for label, key, color in specs:
            series = QLineSeries()
            series.setName(label)
            self._style_line_series(series, color, width=3)
            for index, row in enumerate(rows):
                series.append(float(index) + 0.5, float(row[key]))
            chart.addSeries(series)

        axis_x = self._line_axis(categories)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("$%.0f")
        axis_y.applyNiceNumbers()
        self._style_axis(axis_x)
        self._style_axis(axis_y)

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        for series in chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        return chart

    def _build_expense_chart(self, rows: list[dict[str, float | str]]) -> QChart:
        chart = self._base_chart("Expense Breakdown")

        categories = [str(row["category"]) for row in rows] or ["No Data"]
        values = [float(row["spent"]) for row in rows] or [0.0]

        bar_set = QBarSet("Spent")
        for value in values:
            bar_set.append(value)
        bar_set.setColor(self.EXPENSE_COLOR)
        bar_set.setBorderColor(QColor("#fecdd3"))

        series = QBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.62)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsAngle(-25)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("$%.0f")
        axis_y.applyNiceNumbers()
        self._style_axis(axis_x)
        self._style_axis(axis_y)

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        return chart

    def _build_networth_chart(self, rows: list[dict[str, float | str]]) -> QChart:
        chart = self._base_chart("Net Worth")
        categories = [self._month_label(str(row["month"])) for row in rows]

        series = QLineSeries()
        series.setName("Net Worth")
        self._style_line_series(series, self.NETWORTH_COLOR, width=3)
        for index, row in enumerate(rows):
            series.append(float(index) + 0.5, float(row["value"]))
        chart.addSeries(series)

        axis_x = self._line_axis(categories)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("$%.0f")
        axis_y.applyNiceNumbers()
        self._style_axis(axis_x)
        self._style_axis(axis_y)

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        return chart

    def _base_chart(self, _title: str) -> QChart:
        chart = QChart()
        chart.setTheme(QChart.ChartThemeDark)
        chart.setTitle("")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(450)
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(6, 6, 6, 6))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setPlotAreaBackgroundBrush(self.PLOT_BG)
        chart.setPlotAreaBackgroundPen(QColor(0, 0, 0, 0))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)
        chart.legend().setLabelColor(QColor("#e5e7eb"))
        chart.legend().setBackgroundVisible(False)
        return chart

    def _style_axis(self, axis) -> None:
        axis.setLabelsColor(self.AXIS_LABEL_COLOR)
        axis.setGridLineColor(self.GRID_COLOR)
        axis.setLinePenColor(self.AXIS_LINE_COLOR)
        if isinstance(axis, QValueAxis):
            axis.setMinorTickCount(1)
            axis.setMinorGridLineVisible(True)
            axis.setMinorGridLineColor(self.MINOR_GRID_COLOR)

    @staticmethod
    def _line_axis(categories: list[str]) -> QCategoryAxis:
        labels = categories if categories else ["No Data"]
        axis = QCategoryAxis()
        for index, label in enumerate(labels, start=1):
            axis.append(label, float(index))
        axis.setStartValue(0.0)
        axis.setRange(0.0, float(max(len(labels), 1)))
        axis.setLabelsAngle(-18)
        return axis

    @staticmethod
    def _style_line_series(series: QLineSeries, color: QColor, width: int) -> None:
        pen = QPen(color)
        pen.setWidth(width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        series.setPen(pen)

    def _card_with_widget(self, title: str, inner: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setStyleSheet("font-weight: 600; color: #e2e8f0;")

        layout.addWidget(label)
        layout.addWidget(inner)
        return card

    @staticmethod
    def _month_label(month_key: str) -> str:
        year, month = month_key.split("-")
        return f"{month}/{year[2:]}"

    @staticmethod
    def _fmt_money(amount: float) -> str:
        sign = "-" if amount < 0 else ""
        return f"{sign}${abs(amount):,.2f}"
