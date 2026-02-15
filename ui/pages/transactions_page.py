from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
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
)

from services import FinanceService


class TransactionsPage(QWidget):
    def __init__(self, service: FinanceService, on_data_changed: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.on_data_changed = on_data_changed
        self.current_month = QDate.currentDate().toString("yyyy-MM")
        self.current_search = ""
        self.selected_transaction_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description")

        self.category_input = QComboBox()
        self.category_input.setEditable(True)

        self.account_input = QComboBox()
        self.account_input.setEditable(True)

        self.type_input = QComboBox()
        self.type_input.addItems(["income", "expense"])

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 1_000_000_000.0)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(10.0)
        self.amount_input.setValue(50.0)

        self.save_button = QPushButton("Add Transaction")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self._on_save)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self._on_delete)
        self.delete_button.setEnabled(False)

        form_layout.addWidget(QLabel("Date"), 0, 0)
        form_layout.addWidget(self.date_input, 0, 1)
        form_layout.addWidget(QLabel("Description"), 0, 2)
        form_layout.addWidget(self.description_input, 0, 3)
        form_layout.addWidget(QLabel("Category"), 1, 0)
        form_layout.addWidget(self.category_input, 1, 1)
        form_layout.addWidget(QLabel("Account"), 1, 2)
        form_layout.addWidget(self.account_input, 1, 3)
        form_layout.addWidget(QLabel("Type"), 2, 0)
        form_layout.addWidget(self.type_input, 2, 1)
        form_layout.addWidget(QLabel("Amount"), 2, 2)
        form_layout.addWidget(self.amount_input, 2, 3)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        buttons_row.addWidget(self.save_button)
        buttons_row.addWidget(self.clear_button)
        buttons_row.addWidget(self.delete_button)
        buttons_row.addStretch()
        form_layout.addLayout(buttons_row, 3, 0, 1, 4)
        root.addWidget(form_card)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Date", "Description", "Category", "Account", "Type", "Amount"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setColumnHidden(0, True)
        self.table.itemSelectionChanged.connect(self._load_selected_from_table)

        root.addWidget(self.table)

    def refresh(self, month: str, search: str = "") -> None:
        self.current_month = month
        self.current_search = search
        self._refresh_combos()
        self._refresh_table()

    def _refresh_combos(self) -> None:
        category_text = self.category_input.currentText()
        account_text = self.account_input.currentText()

        categories = self.service.get_categories()
        accounts = self.service.get_account_names()

        self.category_input.clear()
        self.category_input.addItems(categories)
        self.category_input.setCurrentText(category_text)

        self.account_input.clear()
        self.account_input.addItems(accounts)
        self.account_input.setCurrentText(account_text)

    def _refresh_table(self) -> None:
        rows = self.service.get_transactions(self.current_month, self.current_search)
        self.table.setRowCount(len(rows))

        for row_index, tx in enumerate(rows):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(tx.id)))
            self.table.setItem(row_index, 1, QTableWidgetItem(tx.date))
            self.table.setItem(row_index, 2, QTableWidgetItem(tx.description))
            self.table.setItem(row_index, 3, QTableWidgetItem(tx.category))
            self.table.setItem(row_index, 4, QTableWidgetItem(tx.account))
            self.table.setItem(row_index, 5, QTableWidgetItem(tx.type))

            amount_item = QTableWidgetItem(self._fmt_money(tx.amount))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amount_item.setData(Qt.UserRole, tx.amount)
            amount_item.setForeground(QColor("#f87171") if tx.amount < 0 else QColor("#4ade80"))
            self.table.setItem(row_index, 6, amount_item)

    def _load_selected_from_table(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self.selected_transaction_id = None
            self.save_button.setText("Add Transaction")
            self.delete_button.setEnabled(False)
            return

        tx_id_text = self.table.item(row, 0).text()
        self.selected_transaction_id = int(tx_id_text)
        self.delete_button.setEnabled(True)
        self.save_button.setText("Update Transaction")

        date_text = self.table.item(row, 1).text()
        date_value = QDate.fromString(date_text, "yyyy-MM-dd")
        if date_value.isValid():
            self.date_input.setDate(date_value)
        self.description_input.setText(self.table.item(row, 2).text())
        self.category_input.setCurrentText(self.table.item(row, 3).text())
        self.account_input.setCurrentText(self.table.item(row, 4).text())
        self.type_input.setCurrentText(self.table.item(row, 5).text())
        amount = float(self.table.item(row, 6).data(Qt.UserRole))
        self.amount_input.setValue(abs(amount))

    def _on_save(self) -> None:
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than zero.")
            return

        payload = {
            "date_value": self.date_input.date().toString("yyyy-MM-dd"),
            "description": self.description_input.text(),
            "category": self.category_input.currentText(),
            "account": self.account_input.currentText(),
            "tx_type": self.type_input.currentText(),
            "amount": self.amount_input.value(),
        }

        try:
            if self.selected_transaction_id is None:
                self.service.add_transaction(**payload)
            else:
                self.service.update_transaction(transaction_id=self.selected_transaction_id, **payload)
        except ValueError as exc:
            QMessageBox.warning(self, "Unable to Save", str(exc))
            return

        self._on_clear()
        self.on_data_changed()

    def _on_delete(self) -> None:
        if self.selected_transaction_id is None:
            QMessageBox.information(self, "No Selection", "Select a transaction first.")
            return

        self.service.delete_transaction(self.selected_transaction_id)
        self._on_clear()
        self.on_data_changed()

    def _on_clear(self) -> None:
        self.selected_transaction_id = None
        self.table.clearSelection()
        self.date_input.setDate(QDate.currentDate())
        self.description_input.clear()
        self.type_input.setCurrentText("expense")
        self.amount_input.setValue(50.0)
        self.save_button.setText("Add Transaction")
        self.delete_button.setEnabled(False)

    @staticmethod
    def _fmt_money(amount: float) -> str:
        sign = "-" if amount < 0 else ""
        return f"{sign}${abs(amount):,.2f}"
