from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services import FinanceService


class BudgetsPage(QWidget):
    def __init__(self, service: FinanceService, on_data_changed: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.on_data_changed = on_data_changed
        self.current_month = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        self.month_value = QLabel("")
        self.month_value.setStyleSheet("font-weight: 700; color: #93c5fd;")

        self.category_input = QComboBox()
        self.category_input.setEditable(True)

        self.planned_input = QDoubleSpinBox()
        self.planned_input.setRange(0.0, 1_000_000_000.0)
        self.planned_input.setDecimals(2)
        self.planned_input.setSingleStep(25.0)

        self.save_button = QPushButton("Save Budget")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self._on_save)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.addWidget(QLabel("Selected Month:"))
        top_row.addWidget(self.month_value)
        top_row.addStretch()

        form_layout.addLayout(top_row, 0, 0, 1, 4)
        form_layout.addWidget(QLabel("Category"), 1, 0)
        form_layout.addWidget(self.category_input, 1, 1)
        form_layout.addWidget(QLabel("Planned"), 1, 2)
        form_layout.addWidget(self.planned_input, 1, 3)
        form_layout.addWidget(self.save_button, 2, 0, 1, 4)
        root.addWidget(form_card)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Category", "Planned", "Actual Spent", "Remaining", "Utilization"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        root.addWidget(self.table)

    def refresh(self, month: str, _search: str = "") -> None:
        self.current_month = month
        self.month_value.setText(month)
        self._refresh_categories()
        self._refresh_table()

    def _on_save(self) -> None:
        category = self.category_input.currentText().strip()
        planned = self.planned_input.value()
        try:
            self.service.set_budget(self.current_month, category, planned)
        except ValueError as exc:
            QMessageBox.warning(self, "Unable to Save Budget", str(exc))
            return

        self.on_data_changed()
        self._refresh_table()

    def _refresh_categories(self) -> None:
        current = self.category_input.currentText()
        categories = set(self.service.get_categories())
        categories.update(row["category"] for row in self.service.get_budget_rows(self.current_month))
        self.category_input.clear()
        self.category_input.addItems(sorted(categories))
        self.category_input.setCurrentText(current)

    def _refresh_table(self) -> None:
        rows = self.service.get_budget_rows(self.current_month)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row["category"])))

            planned_item = QTableWidgetItem(self._fmt_money(float(row["planned"])))
            planned_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 1, planned_item)

            actual_item = QTableWidgetItem(self._fmt_money(float(row["actual"])))
            actual_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 2, actual_item)

            remaining = float(row["remaining"])
            remaining_item = QTableWidgetItem(self._fmt_money(remaining))
            remaining_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            remaining_item.setForeground(QColor("#4ade80") if remaining >= 0 else QColor("#f87171"))
            self.table.setItem(row_index, 3, remaining_item)

            utilization = float(row["utilization"]) * 100
            utilization_item = QTableWidgetItem(f"{utilization:.1f}%")
            utilization_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 4, utilization_item)

    @staticmethod
    def _fmt_money(amount: float) -> str:
        sign = "-" if amount < 0 else ""
        return f"{sign}${abs(amount):,.2f}"
