from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services import FinanceService


class SettingsPage(QWidget):
    def __init__(self, service: FinanceService, on_data_changed: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.on_data_changed = on_data_changed

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        root.addWidget(title)

        self.path_label = QLabel("")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        db_card = QFrame()
        db_card.setObjectName("Card")
        db_layout = QVBoxLayout(db_card)
        db_layout.setContentsMargins(12, 12, 12, 12)
        db_layout.setSpacing(8)
        db_layout.addWidget(QLabel("Database File"))
        db_layout.addWidget(self.path_label)
        root.addWidget(db_card)

        backup_card = QFrame()
        backup_card.setObjectName("Card")
        backup_layout = QVBoxLayout(backup_card)
        backup_layout.setContentsMargins(12, 12, 12, 12)
        backup_layout.setSpacing(8)
        backup_layout.addWidget(QLabel("Backup and Restore"))

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.backup_button = QPushButton("Backup Database")
        self.backup_button.clicked.connect(self._on_backup)
        self.restore_button = QPushButton("Restore Database")
        self.restore_button.clicked.connect(self._on_restore)
        actions.addWidget(self.backup_button)
        actions.addWidget(self.restore_button)
        actions.addStretch()

        self.status_label = QLabel("No backup actions yet.")
        self.status_label.setStyleSheet("color: #94a3b8;")

        backup_layout.addLayout(actions)
        backup_layout.addWidget(self.status_label)
        root.addWidget(backup_card)
        root.addStretch()

        self.refresh()

    def refresh(self) -> None:
        self.path_label.setText(str(self.service.get_database_path()))

    def _on_backup(self) -> None:
        default_name = f"finance-backup-{datetime.now():%Y%m%d-%H%M%S}.db"
        selected, _ = QFileDialog.getSaveFileName(self, "Backup Database", default_name, "Database Files (*.db)")
        if not selected:
            return

        try:
            backup_path = self.service.backup_database(selected)
        except Exception as exc:  # pragma: no cover - UI error handling path
            QMessageBox.warning(self, "Backup Failed", str(exc))
            return

        self.status_label.setText(f"Backup created: {backup_path}")
        QMessageBox.information(self, "Backup Complete", f"Backup saved to:\n{backup_path}")

    def _on_restore(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "Restore Database", "", "Database Files (*.db)")
        if not selected:
            return

        answer = QMessageBox.question(
            self,
            "Confirm Restore",
            "This will replace current local data with the selected backup. Continue?",
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.service.restore_database(selected)
        except Exception as exc:  # pragma: no cover - UI error handling path
            QMessageBox.warning(self, "Restore Failed", str(exc))
            return

        self.status_label.setText(f"Database restored from: {selected}")
        self.on_data_changed()
        QMessageBox.information(self, "Restore Complete", "Database restore completed.")
