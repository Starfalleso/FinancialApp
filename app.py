from __future__ import annotations

import sqlite3
import sys

from PySide6.QtWidgets import QApplication

from data.database import get_connection, init_database, seed_demo_data
from data.repositories import AccountRepository, BudgetRepository, GoalRepository, TransactionRepository
from services.finance_service import FinanceService
from ui.main_window import MainWindow
from ui.styles import apply_dark_theme


def build_service() -> tuple[FinanceService, sqlite3.Connection]:
    connection = get_connection()
    init_database(connection)
    seed_demo_data(connection)

    service = FinanceService(
        account_repo=AccountRepository(connection),
        transaction_repo=TransactionRepository(connection),
        budget_repo=BudgetRepository(connection),
        goal_repo=GoalRepository(connection),
    )
    return service, connection


def main() -> int:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    service, connection = build_service()
    window = MainWindow(service)
    window.show()

    exit_code = app.exec()
    connection.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
