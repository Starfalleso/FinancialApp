from __future__ import annotations

import csv
import sqlite3
from datetime import date, datetime
from pathlib import Path

from data.database import DB_PATH, init_database
from data.repositories import AccountRepository, BudgetRepository, GoalRepository, TransactionRepository
from models import Goal, Transaction


class FinanceService:
    def __init__(
        self,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
        goal_repo: GoalRepository,
    ) -> None:
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.budget_repo = budget_repo
        self.goal_repo = goal_repo
        self.connection = account_repo.connection

    def get_available_months(self) -> list[str]:
        months = set(self.transaction_repo.distinct_months())
        months.update(self.budget_repo.distinct_months())
        months.update(self._last_n_months(date.today().strftime("%Y-%m"), 6))
        months.add(date.today().strftime("%Y-%m"))
        return sorted(months, reverse=True)

    def get_dashboard_metrics(self, month: str) -> dict[str, float]:
        accounts = self.account_repo.list_all()
        assets = 0.0
        debts = 0.0

        for account in accounts:
            kind = account.kind.strip().lower()
            if kind in {"debt", "liability"}:
                debts += abs(account.balance)
            else:
                assets += account.balance

        income, expense = self.transaction_repo.monthly_income_expense(month)
        cashflow = income - expense
        savings_rate = (cashflow / income) if income > 0 else 0.0

        budget_rows = self.get_budget_rows(month)
        planned_total = sum(row["planned"] for row in budget_rows)
        actual_total = sum(row["actual"] for row in budget_rows)
        budget_pct = (actual_total / planned_total) if planned_total > 0 else 0.0

        return {
            "net_worth": assets - debts,
            "monthly_cashflow": cashflow,
            "income": income,
            "expense": expense,
            "savings_rate": savings_rate,
            "budget_planned": planned_total,
            "budget_spent": actual_total,
            "budget_remaining": planned_total - actual_total,
            "budget_pct": budget_pct,
        }

    def get_cashflow_over_time(self, selected_month: str, months: int = 6) -> list[dict[str, float | str]]:
        period = self._last_n_months(selected_month, months)
        result: list[dict[str, float | str]] = []
        for month in period:
            income, expense = self.transaction_repo.monthly_income_expense(month)
            result.append(
                {
                    "month": month,
                    "income": income,
                    "expense": expense,
                    "net": income - expense,
                }
            )
        return result

    def get_expense_breakdown(self, month: str) -> list[dict[str, float | str]]:
        rows = self.transaction_repo.expense_by_category(month)
        return [{"category": category, "spent": spent} for category, spent in rows]

    def get_networth_over_time(self, selected_month: str, months: int = 6) -> list[dict[str, float | str]]:
        cashflow = self.get_cashflow_over_time(selected_month, months)
        current_networth = self.get_dashboard_metrics(selected_month)["net_worth"]
        baseline = current_networth - sum(float(row["net"]) for row in cashflow)

        points: list[dict[str, float | str]] = []
        rolling = baseline
        for row in cashflow:
            rolling += float(row["net"])
            points.append({"month": row["month"], "value": rolling})
        return points

    def get_recent_transactions(self, month: str, search: str = "", limit: int = 15):
        return self.transaction_repo.list_recent(limit=limit, month=month, search=search)

    def get_transactions(self, month: str, search: str = ""):
        return self.transaction_repo.list_by_month(month=month, search=search)

    def get_accounts(self):
        return self.account_repo.list_all()

    def get_categories(self) -> list[str]:
        return self.transaction_repo.distinct_categories()

    def get_account_names(self) -> list[str]:
        names = set(self.account_repo.list_names())
        names.update(self.transaction_repo.distinct_accounts())
        return sorted(name for name in names if name)

    def add_transaction(
        self,
        date_value: str,
        description: str,
        category: str,
        account: str,
        tx_type: str,
        amount: float,
    ) -> int:
        normalized_type = tx_type.strip().lower()
        if normalized_type not in {"income", "expense"}:
            raise ValueError("Transaction type must be 'income' or 'expense'.")

        normalized_amount = abs(amount)
        signed_amount = normalized_amount if normalized_type == "income" else -normalized_amount

        transaction = Transaction(
            id=None,
            date=date_value,
            description=description.strip() or "Untitled",
            category=category.strip() or "Uncategorized",
            account=account.strip() or "Cash",
            amount=signed_amount,
            type=normalized_type,
        )
        created_id = self.transaction_repo.add(transaction)
        self.account_repo.adjust_balance(transaction.account, transaction.amount)
        return created_id

    def update_transaction(
        self,
        transaction_id: int,
        date_value: str,
        description: str,
        category: str,
        account: str,
        tx_type: str,
        amount: float,
    ) -> None:
        old = self.transaction_repo.get_by_id(transaction_id)
        if not old:
            raise ValueError(f"Transaction {transaction_id} not found.")

        normalized_type = tx_type.strip().lower()
        if normalized_type not in {"income", "expense"}:
            raise ValueError("Transaction type must be 'income' or 'expense'.")

        signed_amount = abs(amount) if normalized_type == "income" else -abs(amount)
        updated = Transaction(
            id=transaction_id,
            date=date_value,
            description=description.strip() or "Untitled",
            category=category.strip() or "Uncategorized",
            account=account.strip() or "Cash",
            amount=signed_amount,
            type=normalized_type,
        )

        self.transaction_repo.update(transaction_id, updated)

        if old.account == updated.account:
            self.account_repo.adjust_balance(updated.account, updated.amount - old.amount)
        else:
            self.account_repo.adjust_balance(old.account, -old.amount)
            self.account_repo.adjust_balance(updated.account, updated.amount)

    def delete_transaction(self, transaction_id: int) -> None:
        existing = self.transaction_repo.get_by_id(transaction_id)
        if not existing:
            return
        self.transaction_repo.delete(transaction_id)
        self.account_repo.adjust_balance(existing.account, -existing.amount)

    def set_budget(self, month: str, category: str, planned: float) -> None:
        if planned < 0:
            raise ValueError("Budget amount cannot be negative.")
        if not category.strip():
            raise ValueError("Category is required.")
        self.budget_repo.upsert(month=month, category=category.strip(), planned=planned)

    def get_budget_rows(self, month: str) -> list[dict[str, float | str]]:
        budget_rows = self.budget_repo.list_by_month(month)
        planned = {row.category: row.planned for row in budget_rows}
        actual = {row["category"]: float(row["spent"]) for row in self.get_expense_breakdown(month)}

        categories = sorted(set(planned.keys()) | set(actual.keys()))
        rows: list[dict[str, float | str]] = []
        for category in categories:
            planned_value = float(planned.get(category, 0.0))
            actual_value = float(actual.get(category, 0.0))
            remaining = planned_value - actual_value
            utilization = (actual_value / planned_value) if planned_value > 0 else 0.0
            rows.append(
                {
                    "category": category,
                    "planned": planned_value,
                    "actual": actual_value,
                    "remaining": remaining,
                    "utilization": utilization,
                }
            )
        return rows

    def get_goals(self) -> list[Goal]:
        return self.goal_repo.list_all()

    def get_goals_summary(self) -> dict[str, float]:
        goals = self.get_goals()
        total_target = sum(goal.target for goal in goals)
        total_current = sum(goal.current for goal in goals)
        progress = (total_current / total_target) if total_target > 0 else 0.0
        return {
            "total_target": total_target,
            "total_current": total_current,
            "remaining": total_target - total_current,
            "progress": progress,
        }

    def add_goal(self, name: str, target: float, current: float, deadline: str | None) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Goal name is required.")
        if target <= 0:
            raise ValueError("Target must be greater than zero.")
        if current < 0:
            raise ValueError("Current amount cannot be negative.")

        normalized_deadline = deadline.strip() if deadline else None
        if normalized_deadline:
            datetime.strptime(normalized_deadline, "%Y-%m-%d")

        goal = Goal(
            id=None,
            name=clean_name,
            target=float(target),
            current=float(current),
            deadline=normalized_deadline or None,
        )
        return self.goal_repo.add(goal)

    def update_goal(self, goal_id: int, name: str, target: float, current: float, deadline: str | None) -> None:
        existing = self.goal_repo.get_by_id(goal_id)
        if not existing:
            raise ValueError(f"Goal {goal_id} not found.")

        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Goal name is required.")
        if target <= 0:
            raise ValueError("Target must be greater than zero.")
        if current < 0:
            raise ValueError("Current amount cannot be negative.")

        normalized_deadline = deadline.strip() if deadline else None
        if normalized_deadline:
            datetime.strptime(normalized_deadline, "%Y-%m-%d")

        updated = Goal(
            id=goal_id,
            name=clean_name,
            target=float(target),
            current=float(current),
            deadline=normalized_deadline or None,
        )
        self.goal_repo.update(goal_id, updated)

    def delete_goal(self, goal_id: int) -> None:
        self.goal_repo.delete(goal_id)

    def get_database_path(self) -> Path:
        return DB_PATH

    def export_monthly_report_csv(self, month: str, destination: str | Path, search: str = "") -> Path:
        target = Path(destination)
        if target.suffix.lower() != ".csv":
            target = target.with_suffix(".csv")
        target.parent.mkdir(parents=True, exist_ok=True)

        metrics = self.get_dashboard_metrics(month)
        accounts = self.get_accounts()
        goals = self.get_goals()
        goals_summary = self.get_goals_summary()
        budget_rows = self.get_budget_rows(month)
        expense_rows = self.get_expense_breakdown(month)
        transactions = self.get_transactions(month=month, search=search)

        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Personal Finance Dashboard Report"])
            writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["Month", month])
            writer.writerow(["Search", search or "(none)"])
            writer.writerow([])

            writer.writerow(["KPIs"])
            writer.writerow(["Net Worth", metrics["net_worth"]])
            writer.writerow(["Monthly Income", metrics["income"]])
            writer.writerow(["Monthly Expense", metrics["expense"]])
            writer.writerow(["Monthly Cashflow", metrics["monthly_cashflow"]])
            writer.writerow(["Savings Rate", metrics["savings_rate"]])
            writer.writerow(["Budget Planned", metrics["budget_planned"]])
            writer.writerow(["Budget Spent", metrics["budget_spent"]])
            writer.writerow(["Budget Remaining", metrics["budget_remaining"]])
            writer.writerow([])

            writer.writerow(["Accounts"])
            writer.writerow(["Name", "Kind", "Balance"])
            for account in accounts:
                writer.writerow([account.name, account.kind, account.balance])
            writer.writerow([])

            writer.writerow(["Budgets"])
            writer.writerow(["Category", "Planned", "Actual", "Remaining", "Utilization"])
            for row in budget_rows:
                writer.writerow(
                    [
                        row["category"],
                        row["planned"],
                        row["actual"],
                        row["remaining"],
                        row["utilization"],
                    ]
                )
            writer.writerow([])

            writer.writerow(["Expense Breakdown"])
            writer.writerow(["Category", "Spent"])
            for row in expense_rows:
                writer.writerow([row["category"], row["spent"]])
            writer.writerow([])

            writer.writerow(["Goals Summary"])
            writer.writerow(["Total Current", goals_summary["total_current"]])
            writer.writerow(["Total Target", goals_summary["total_target"]])
            writer.writerow(["Remaining", goals_summary["remaining"]])
            writer.writerow(["Progress", goals_summary["progress"]])
            writer.writerow([])

            writer.writerow(["Goals"])
            writer.writerow(["Name", "Current", "Target", "Deadline"])
            for goal in goals:
                writer.writerow([goal.name, goal.current, goal.target, goal.deadline or ""])
            writer.writerow([])

            writer.writerow(["Transactions"])
            writer.writerow(["Date", "Description", "Category", "Account", "Type", "Amount"])
            for tx in transactions:
                writer.writerow([tx.date, tx.description, tx.category, tx.account, tx.type, tx.amount])

        return target

    def backup_database(self, destination: str | Path) -> Path:
        target = Path(destination)
        if target.suffix.lower() != ".db":
            target = target.with_suffix(".db")
        target.parent.mkdir(parents=True, exist_ok=True)

        self.connection.commit()
        backup_connection = sqlite3.connect(target)
        try:
            self.connection.backup(backup_connection)
        finally:
            backup_connection.close()
        return target

    def restore_database(self, source_path: str | Path) -> None:
        source = Path(source_path)
        if not source.exists():
            raise ValueError(f"Backup file does not exist: {source}")

        source_connection = sqlite3.connect(source)
        try:
            self.connection.commit()
            source_connection.backup(self.connection)
            self.connection.commit()
            init_database(self.connection)
        finally:
            source_connection.close()

    def import_csv(self, file_path: str | Path) -> tuple[int, int]:
        required_headers = {"date", "description", "category", "account", "amount"}
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")

        imported = 0
        skipped = 0
        existing = self.transaction_repo.dedupe_keys()

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = set(reader.fieldnames or [])
            missing = required_headers - headers
            if missing:
                missing_list = ", ".join(sorted(missing))
                raise ValueError(f"CSV missing required columns: {missing_list}")

            for line_number, row in enumerate(reader, start=2):
                try:
                    date_text = (row.get("date") or "").strip()
                    datetime.strptime(date_text, "%Y-%m-%d")

                    description = (row.get("description") or "").strip()
                    category = (row.get("category") or "").strip()
                    account = (row.get("account") or "").strip()
                    amount = float((row.get("amount") or "").strip())
                except Exception as exc:  # pragma: no cover - defensive parse branch
                    raise ValueError(f"Invalid row at line {line_number}: {exc}") from exc

                if not description or not category or not account:
                    raise ValueError(f"Invalid row at line {line_number}: empty text fields are not allowed.")

                key = (date_text, description, round(amount, 2), account)
                if key in existing:
                    skipped += 1
                    continue

                tx_type = "income" if amount >= 0 else "expense"
                self.add_transaction(
                    date_value=date_text,
                    description=description,
                    category=category,
                    account=account,
                    tx_type=tx_type,
                    amount=abs(amount),
                )
                existing.add(key)
                imported += 1

        return imported, skipped

    @staticmethod
    def _last_n_months(end_month: str, count: int) -> list[str]:
        end_date = datetime.strptime(f"{end_month}-01", "%Y-%m-%d").date()
        months: list[str] = []
        for delta in range(count - 1, -1, -1):
            year = end_date.year
            month = end_date.month - delta
            while month <= 0:
                year -= 1
                month += 12
            months.append(f"{year:04d}-{month:02d}")
        return months
