from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
)

from services import FinanceService


class GoalsPage(QWidget):
    def __init__(self, service: FinanceService, on_data_changed: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.on_data_changed = on_data_changed
        self.selected_goal_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        summary_card = QFrame()
        summary_card.setObjectName("Card")
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(16)

        self.total_current_label = QLabel("$0.00")
        self.total_target_label = QLabel("$0.00")
        self.remaining_label = QLabel("$0.00")
        self.progress_label = QLabel("0.0%")
        for label in (self.total_current_label, self.total_target_label, self.remaining_label, self.progress_label):
            label.setStyleSheet("font-size: 18px; font-weight: 700;")

        summary_layout.addWidget(self._metric("Current", self.total_current_label))
        summary_layout.addWidget(self._metric("Target", self.total_target_label))
        summary_layout.addWidget(self._metric("Remaining", self.remaining_label))
        summary_layout.addWidget(self._metric("Progress", self.progress_label))
        root.addWidget(summary_card)

        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Goal name")

        self.target_input = QDoubleSpinBox()
        self.target_input.setRange(0.01, 1_000_000_000.0)
        self.target_input.setDecimals(2)
        self.target_input.setSingleStep(100.0)

        self.current_input = QDoubleSpinBox()
        self.current_input.setRange(0.0, 1_000_000_000.0)
        self.current_input.setDecimals(2)
        self.current_input.setSingleStep(50.0)

        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDisplayFormat("yyyy-MM-dd")
        self.deadline_input.setDate(QDate.currentDate().addMonths(6))

        self.no_deadline_checkbox = QCheckBox("No deadline")
        self.no_deadline_checkbox.toggled.connect(self.deadline_input.setDisabled)

        self.save_button = QPushButton("Add Goal")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self._on_save)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self._on_delete)
        self.delete_button.setEnabled(False)

        form_layout.addWidget(QLabel("Name"), 0, 0)
        form_layout.addWidget(self.name_input, 0, 1)
        form_layout.addWidget(QLabel("Target"), 0, 2)
        form_layout.addWidget(self.target_input, 0, 3)
        form_layout.addWidget(QLabel("Current"), 1, 0)
        form_layout.addWidget(self.current_input, 1, 1)
        form_layout.addWidget(QLabel("Deadline"), 1, 2)
        form_layout.addWidget(self.deadline_input, 1, 3)
        form_layout.addWidget(self.no_deadline_checkbox, 2, 0, 1, 2)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.save_button)
        actions.addWidget(self.clear_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        form_layout.addLayout(actions, 2, 2, 1, 2)
        root.addWidget(form_card)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Current", "Target", "Progress", "Remaining", "Deadline"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setColumnHidden(0, True)
        self.table.itemSelectionChanged.connect(self._load_selected_from_table)

        root.addWidget(self.table)
        self._on_clear()

    def refresh(self, _month: str = "", _search: str = "") -> None:
        self._refresh_summary()
        self._refresh_table()

    def _refresh_summary(self) -> None:
        summary = self.service.get_goals_summary()
        self.total_current_label.setText(self._fmt_money(summary["total_current"]))
        self.total_target_label.setText(self._fmt_money(summary["total_target"]))
        self.remaining_label.setText(self._fmt_money(summary["remaining"]))
        self.progress_label.setText(f"{summary['progress'] * 100:.1f}%")
        self.progress_label.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {'#4ade80' if summary['progress'] >= 1 else '#60a5fa'};"
        )

    def _refresh_table(self) -> None:
        goals = self.service.get_goals()
        self.table.setRowCount(len(goals))
        for row_index, goal in enumerate(goals):
            progress_ratio = (goal.current / goal.target) if goal.target > 0 else 0.0
            remaining = goal.target - goal.current
            deadline_text = goal.deadline or "None"

            self.table.setItem(row_index, 0, QTableWidgetItem(str(goal.id)))
            self.table.setItem(row_index, 1, QTableWidgetItem(goal.name))

            current_item = QTableWidgetItem(self._fmt_money(goal.current))
            current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 2, current_item)

            target_item = QTableWidgetItem(self._fmt_money(goal.target))
            target_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 3, target_item)

            progress_item = QTableWidgetItem(f"{progress_ratio * 100:.1f}%")
            progress_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            progress_item.setForeground(QColor("#4ade80") if progress_ratio >= 1 else QColor("#60a5fa"))
            self.table.setItem(row_index, 4, progress_item)

            remaining_item = QTableWidgetItem(self._fmt_money(remaining))
            remaining_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            remaining_item.setForeground(QColor("#4ade80") if remaining <= 0 else QColor("#f59e0b"))
            self.table.setItem(row_index, 5, remaining_item)

            self.table.setItem(row_index, 6, QTableWidgetItem(deadline_text))

    def _load_selected_from_table(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self.selected_goal_id = None
            self.save_button.setText("Add Goal")
            self.delete_button.setEnabled(False)
            return

        self.selected_goal_id = int(self.table.item(row, 0).text())
        self.save_button.setText("Update Goal")
        self.delete_button.setEnabled(True)

        self.name_input.setText(self.table.item(row, 1).text())
        self.current_input.setValue(abs(self._parse_money(self.table.item(row, 2).text())))
        self.target_input.setValue(abs(self._parse_money(self.table.item(row, 3).text())))

        deadline_text = self.table.item(row, 6).text()
        if deadline_text == "None":
            self.no_deadline_checkbox.setChecked(True)
        else:
            deadline = QDate.fromString(deadline_text, "yyyy-MM-dd")
            self.no_deadline_checkbox.setChecked(False)
            if deadline.isValid():
                self.deadline_input.setDate(deadline)

    def _on_save(self) -> None:
        payload = {
            "name": self.name_input.text(),
            "target": self.target_input.value(),
            "current": self.current_input.value(),
            "deadline": None if self.no_deadline_checkbox.isChecked() else self.deadline_input.date().toString("yyyy-MM-dd"),
        }

        try:
            if self.selected_goal_id is None:
                self.service.add_goal(**payload)
            else:
                self.service.update_goal(goal_id=self.selected_goal_id, **payload)
        except ValueError as exc:
            QMessageBox.warning(self, "Unable to Save Goal", str(exc))
            return

        self._on_clear()
        self.on_data_changed()

    def _on_delete(self) -> None:
        if self.selected_goal_id is None:
            QMessageBox.information(self, "No Selection", "Select a goal first.")
            return
        self.service.delete_goal(self.selected_goal_id)
        self._on_clear()
        self.on_data_changed()

    def _on_clear(self) -> None:
        self.selected_goal_id = None
        self.table.clearSelection()
        self.name_input.clear()
        self.target_input.setValue(10000.0)
        self.current_input.setValue(0.0)
        self.deadline_input.setDate(QDate.currentDate().addMonths(6))
        self.no_deadline_checkbox.setChecked(False)
        self.save_button.setText("Add Goal")
        self.delete_button.setEnabled(False)

    @staticmethod
    def _metric(label: str, value_label: QLabel) -> QFrame:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        caption = QLabel(label)
        caption.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(caption)
        layout.addWidget(value_label)
        return frame

    @staticmethod
    def _parse_money(raw: str) -> float:
        return float(raw.replace("$", "").replace(",", ""))

    @staticmethod
    def _fmt_money(amount: float) -> str:
        sign = "-" if amount < 0 else ""
        return f"{sign}${abs(amount):,.2f}"
