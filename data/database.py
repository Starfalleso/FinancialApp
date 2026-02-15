from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path


APP_DATA_DIR_NAME = "PersonalFinanceDashboard"
DATA_DIR_ENV_VAR = "FINANCEAPP_DATA_DIR"
LEGACY_DB_PATH = Path(__file__).resolve().parent.parent / "finance.db"


def resolve_data_dir() -> Path:
    configured = os.getenv(DATA_DIR_ENV_VAR)
    if configured:
        data_dir = Path(configured).expanduser()
    elif sys.platform.startswith("win"):
        base = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        data_dir = base / APP_DATA_DIR_NAME
    elif sys.platform == "darwin":
        data_dir = Path.home() / "Library" / "Application Support" / APP_DATA_DIR_NAME
    else:
        base = Path(os.getenv("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
        data_dir = base / APP_DATA_DIR_NAME

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


DATA_DIR = resolve_data_dir()
DB_PATH = DATA_DIR / "finance.db"


def _migrate_legacy_database() -> None:
    if DB_PATH.exists():
        return
    if not LEGACY_DB_PATH.exists():
        return
    if LEGACY_DB_PATH == DB_PATH:
        return
    shutil.copy2(LEGACY_DB_PATH, DB_PATH)


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_database()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            account TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense'))
        );

        CREATE TABLE IF NOT EXISTS budgets(
            id INTEGER PRIMARY KEY,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            planned REAL NOT NULL,
            UNIQUE(month, category)
        );

        CREATE TABLE IF NOT EXISTS goals(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            target REAL NOT NULL,
            current REAL NOT NULL,
            deadline TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
        CREATE INDEX IF NOT EXISTS idx_transactions_month ON transactions(substr(date, 1, 7));
        CREATE INDEX IF NOT EXISTS idx_transactions_search ON transactions(description, category, account);
        """
    )
    connection.commit()


def _shift_month(base: date, delta: int) -> date:
    month_index = (base.month - 1) + delta
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def seed_demo_data(connection: sqlite3.Connection) -> None:
    tx_count = connection.execute("SELECT COUNT(*) AS count FROM transactions").fetchone()["count"]
    goal_count = connection.execute("SELECT COUNT(*) AS count FROM goals").fetchone()["count"]
    if tx_count:
        return

    connection.executemany(
        "INSERT OR IGNORE INTO accounts(name, kind, balance) VALUES(?, ?, ?)",
        [
            ("Checking", "Asset", 5300.00),
            ("Savings", "Asset", 15000.00),
            ("Brokerage", "Asset", 9200.00),
            ("Credit Card", "Debt", 2200.00),
        ],
    )

    now = date.today()
    current = _shift_month(now, 0)
    previous = _shift_month(now, -1)

    seed_transactions = [
        (previous.replace(day=1).isoformat(), "Salary", "Income", "Checking", 4200.0, "income"),
        (previous.replace(day=3).isoformat(), "Freelance Project", "Income", "Checking", 600.0, "income"),
        (previous.replace(day=4).isoformat(), "Monthly Rent", "Housing", "Checking", -1450.0, "expense"),
        (previous.replace(day=6).isoformat(), "Supermarket", "Groceries", "Checking", -320.0, "expense"),
        (previous.replace(day=9).isoformat(), "Electric + Internet", "Utilities", "Checking", -180.0, "expense"),
        (previous.replace(day=11).isoformat(), "Dinner with Friends", "Dining", "Checking", -140.0, "expense"),
        (previous.replace(day=14).isoformat(), "Gas", "Transport", "Checking", -90.0, "expense"),
        (previous.replace(day=17).isoformat(), "Gym Membership", "Health", "Checking", -55.0, "expense"),
        (previous.replace(day=21).isoformat(), "Streaming + Games", "Entertainment", "Checking", -120.0, "expense"),
        (previous.replace(day=24).isoformat(), "Index ETF Buy", "Investments", "Brokerage", -500.0, "expense"),
        (current.replace(day=1).isoformat(), "Salary", "Income", "Checking", 4200.0, "income"),
        (current.replace(day=2).isoformat(), "Quarterly Bonus", "Income", "Checking", 300.0, "income"),
        (current.replace(day=4).isoformat(), "Monthly Rent", "Housing", "Checking", -1450.0, "expense"),
        (current.replace(day=5).isoformat(), "Supermarket", "Groceries", "Checking", -340.0, "expense"),
        (current.replace(day=7).isoformat(), "Electric + Internet", "Utilities", "Checking", -170.0, "expense"),
        (current.replace(day=10).isoformat(), "Coffee + Lunch", "Dining", "Checking", -155.0, "expense"),
        (current.replace(day=13).isoformat(), "Fuel + Parking", "Transport", "Checking", -95.0, "expense"),
        (current.replace(day=16).isoformat(), "Subscriptions", "Entertainment", "Checking", -42.0, "expense"),
        (current.replace(day=19).isoformat(), "Pharmacy", "Health", "Checking", -110.0, "expense"),
        (current.replace(day=23).isoformat(), "Weekend Trip", "Travel", "Checking", -260.0, "expense"),
    ]

    connection.executemany(
        """
        INSERT INTO transactions(date, description, category, account, amount, type)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
        seed_transactions,
    )

    connection.executemany(
        "INSERT OR IGNORE INTO budgets(month, category, planned) VALUES(?, ?, ?)",
        [
            (current.strftime("%Y-%m"), "Housing", 1500.0),
            (current.strftime("%Y-%m"), "Groceries", 450.0),
            (current.strftime("%Y-%m"), "Utilities", 250.0),
            (current.strftime("%Y-%m"), "Dining", 220.0),
            (current.strftime("%Y-%m"), "Transport", 180.0),
            (current.strftime("%Y-%m"), "Entertainment", 160.0),
            (previous.strftime("%Y-%m"), "Housing", 1500.0),
            (previous.strftime("%Y-%m"), "Groceries", 420.0),
            (previous.strftime("%Y-%m"), "Utilities", 240.0),
            (previous.strftime("%Y-%m"), "Dining", 210.0),
            (previous.strftime("%Y-%m"), "Transport", 170.0),
            (previous.strftime("%Y-%m"), "Entertainment", 150.0),
        ],
    )

    if not goal_count:
        connection.execute(
            """
            INSERT INTO goals(name, target, current, deadline)
            VALUES(?, ?, ?, ?)
            """,
            ("Emergency Fund", 20000.0, 15000.0, f"{now.year + 1}-12-31"),
        )

    connection.commit()
