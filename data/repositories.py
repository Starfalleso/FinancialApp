from __future__ import annotations

import sqlite3
from models import Account, Budget, Goal, Transaction


class AccountRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_all(self) -> list[Account]:
        rows = self.connection.execute(
            "SELECT id, name, kind, balance FROM accounts ORDER BY kind, name"
        ).fetchall()
        return [Account(id=row["id"], name=row["name"], kind=row["kind"], balance=row["balance"]) for row in rows]

    def list_names(self) -> list[str]:
        rows = self.connection.execute("SELECT name FROM accounts ORDER BY name").fetchall()
        return [row["name"] for row in rows]

    def get_by_name(self, name: str) -> Account | None:
        row = self.connection.execute(
            "SELECT id, name, kind, balance FROM accounts WHERE name = ?",
            (name,),
        ).fetchone()
        if not row:
            return None
        return Account(id=row["id"], name=row["name"], kind=row["kind"], balance=row["balance"])

    def ensure_account(self, name: str, kind: str = "Asset") -> Account:
        existing = self.get_by_name(name)
        if existing:
            return existing

        cursor = self.connection.execute(
            "INSERT INTO accounts(name, kind, balance) VALUES(?, ?, 0)",
            (name, kind),
        )
        self.connection.commit()
        return Account(id=cursor.lastrowid, name=name, kind=kind, balance=0.0)

    def adjust_balance(self, name: str, delta: float, kind: str = "Asset") -> None:
        self.ensure_account(name, kind=kind)
        self.connection.execute(
            "UPDATE accounts SET balance = balance + ? WHERE name = ?",
            (delta, name),
        )
        self.connection.commit()

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM accounts").fetchone()
        return int(row["count"])


class TransactionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, transaction: Transaction) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO transactions(date, description, category, account, amount, type)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.date,
                transaction.description,
                transaction.category,
                transaction.account,
                transaction.amount,
                transaction.type,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def update(self, transaction_id: int, transaction: Transaction) -> None:
        self.connection.execute(
            """
            UPDATE transactions
            SET date = ?, description = ?, category = ?, account = ?, amount = ?, type = ?
            WHERE id = ?
            """,
            (
                transaction.date,
                transaction.description,
                transaction.category,
                transaction.account,
                transaction.amount,
                transaction.type,
                transaction_id,
            ),
        )
        self.connection.commit()

    def delete(self, transaction_id: int) -> None:
        self.connection.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        self.connection.commit()

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        row = self.connection.execute(
            """
            SELECT id, date, description, category, account, amount, type
            FROM transactions
            WHERE id = ?
            """,
            (transaction_id,),
        ).fetchone()
        if not row:
            return None
        return Transaction(
            id=row["id"],
            date=row["date"],
            description=row["description"],
            category=row["category"],
            account=row["account"],
            amount=row["amount"],
            type=row["type"],
        )

    def list_recent(self, limit: int = 15, month: str | None = None, search: str = "") -> list[Transaction]:
        conditions = []
        params: list[object] = []

        if month:
            conditions.append("substr(date, 1, 7) = ?")
            params.append(month)

        if search.strip():
            conditions.append("(description LIKE ? OR category LIKE ? OR account LIKE ?)")
            token = f"%{search.strip()}%"
            params.extend([token, token, token])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        rows = self.connection.execute(
            f"""
            SELECT id, date, description, category, account, amount, type
            FROM transactions
            {where_clause}
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def list_by_month(self, month: str, search: str = "") -> list[Transaction]:
        params: list[object] = [month]
        where_clause = "WHERE substr(date, 1, 7) = ?"

        if search.strip():
            token = f"%{search.strip()}%"
            where_clause += " AND (description LIKE ? OR category LIKE ? OR account LIKE ?)"
            params.extend([token, token, token])

        rows = self.connection.execute(
            f"""
            SELECT id, date, description, category, account, amount, type
            FROM transactions
            {where_clause}
            ORDER BY date DESC, id DESC
            """,
            tuple(params),
        ).fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM transactions").fetchone()
        return int(row["count"])

    def distinct_months(self) -> list[str]:
        rows = self.connection.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS month FROM transactions ORDER BY month DESC"
        ).fetchall()
        return [row["month"] for row in rows if row["month"]]

    def distinct_categories(self) -> list[str]:
        rows = self.connection.execute(
            "SELECT DISTINCT category FROM transactions ORDER BY category"
        ).fetchall()
        return [row["category"] for row in rows if row["category"]]

    def distinct_accounts(self) -> list[str]:
        rows = self.connection.execute("SELECT DISTINCT account FROM transactions ORDER BY account").fetchall()
        return [row["account"] for row in rows if row["account"]]

    def monthly_income_expense(self, month: str) -> tuple[float, float]:
        row = self.connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN ABS(amount) ELSE 0 END), 0) AS expense
            FROM transactions
            WHERE substr(date, 1, 7) = ?
            """,
            (month,),
        ).fetchone()
        return float(row["income"]), float(row["expense"])

    def monthly_net(self, month: str) -> float:
        row = self.connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS net
            FROM transactions
            WHERE substr(date, 1, 7) = ?
            """,
            (month,),
        ).fetchone()
        return float(row["net"])

    def expense_by_category(self, month: str) -> list[tuple[str, float]]:
        rows = self.connection.execute(
            """
            SELECT category, ABS(SUM(amount)) AS spent
            FROM transactions
            WHERE substr(date, 1, 7) = ?
              AND type = 'expense'
            GROUP BY category
            ORDER BY spent DESC
            """,
            (month,),
        ).fetchall()
        return [(row["category"], float(row["spent"])) for row in rows]

    def dedupe_keys(self) -> set[tuple[str, str, float, str]]:
        rows = self.connection.execute(
            "SELECT date, description, amount, account FROM transactions"
        ).fetchall()
        return {(row["date"], row["description"], round(float(row["amount"]), 2), row["account"]) for row in rows}

    @staticmethod
    def _row_to_transaction(row: sqlite3.Row) -> Transaction:
        return Transaction(
            id=row["id"],
            date=row["date"],
            description=row["description"],
            category=row["category"],
            account=row["account"],
            amount=float(row["amount"]),
            type=row["type"],
        )


class BudgetRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def upsert(self, month: str, category: str, planned: float) -> None:
        self.connection.execute(
            """
            INSERT INTO budgets(month, category, planned)
            VALUES(?, ?, ?)
            ON CONFLICT(month, category) DO UPDATE SET planned = excluded.planned
            """,
            (month, category, planned),
        )
        self.connection.commit()

    def list_by_month(self, month: str) -> list[Budget]:
        rows = self.connection.execute(
            """
            SELECT id, month, category, planned
            FROM budgets
            WHERE month = ?
            ORDER BY category
            """,
            (month,),
        ).fetchall()
        return [Budget(id=row["id"], month=row["month"], category=row["category"], planned=row["planned"]) for row in rows]

    def distinct_months(self) -> list[str]:
        rows = self.connection.execute("SELECT DISTINCT month FROM budgets ORDER BY month DESC").fetchall()
        return [row["month"] for row in rows if row["month"]]

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM budgets").fetchone()
        return int(row["count"])


class GoalRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, goal: Goal) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO goals(name, target, current, deadline)
            VALUES(?, ?, ?, ?)
            """,
            (goal.name, goal.target, goal.current, goal.deadline),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def update(self, goal_id: int, goal: Goal) -> None:
        self.connection.execute(
            """
            UPDATE goals
            SET name = ?, target = ?, current = ?, deadline = ?
            WHERE id = ?
            """,
            (goal.name, goal.target, goal.current, goal.deadline, goal_id),
        )
        self.connection.commit()

    def delete(self, goal_id: int) -> None:
        self.connection.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        self.connection.commit()

    def get_by_id(self, goal_id: int) -> Goal | None:
        row = self.connection.execute(
            "SELECT id, name, target, current, deadline FROM goals WHERE id = ?",
            (goal_id,),
        ).fetchone()
        if not row:
            return None
        return Goal(
            id=row["id"],
            name=row["name"],
            target=float(row["target"]),
            current=float(row["current"]),
            deadline=row["deadline"],
        )

    def list_all(self) -> list[Goal]:
        rows = self.connection.execute(
            "SELECT id, name, target, current, deadline FROM goals ORDER BY id DESC"
        ).fetchall()
        return [
            Goal(
                id=row["id"],
                name=row["name"],
                target=float(row["target"]),
                current=float(row["current"]),
                deadline=row["deadline"],
            )
            for row in rows
        ]

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM goals").fetchone()
        return int(row["count"])
