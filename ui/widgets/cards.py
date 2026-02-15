from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KpiCard(QFrame):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("KpiCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("KpiTitle")

        self.value_label = QLabel("$0.00")
        self.value_label.setObjectName("KpiValue")

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("KpiHint")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.hint_label)

    def set_values(self, primary: str, secondary: str = "") -> None:
        self.value_label.setText(primary)
        self.hint_label.setText(secondary)
