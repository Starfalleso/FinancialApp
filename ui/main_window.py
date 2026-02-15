from __future__ import annotations

from datetime import date

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from services import FinanceService
from ui.pages import BudgetsPage, DashboardPage, GoalsPage, SettingsPage, TransactionsPage


class MainWindow(QMainWindow):
    def __init__(self, service: FinanceService, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.nav_labels = ["Dashboard", "Transactions", "Budgets", "Goals", "Settings"]
        self._page_fade_animation: QPropertyAnimation | None = None
        self.setWindowTitle("Personal Finance Dashboard")
        self.resize(1400, 900)

        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar)

        content = QWidget()
        content.setObjectName("ContentShell")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(12)
        root_layout.addWidget(content, 1)

        self.topbar = self._build_topbar()
        content_layout.addWidget(self.topbar)

        self.stacked = QStackedWidget()
        content_layout.addWidget(self.stacked, 1)

        self.dashboard_page = DashboardPage(self.service)
        self.transactions_page = TransactionsPage(self.service, on_data_changed=self._handle_data_changed)
        self.budgets_page = BudgetsPage(self.service, on_data_changed=self._handle_data_changed)
        self.goals_page = GoalsPage(self.service, on_data_changed=self._handle_data_changed)
        self.settings_page = SettingsPage(self.service, on_data_changed=self._handle_data_changed)

        self.stacked.addWidget(self.dashboard_page)
        self.stacked.addWidget(self.transactions_page)
        self.stacked.addWidget(self.budgets_page)
        self.stacked.addWidget(self.goals_page)
        self.stacked.addWidget(self.settings_page)

        first_button = self.nav_group.button(0)
        if first_button:
            first_button.setChecked(True)

        self._reload_months()
        self._on_nav_changed(0)
        self._refresh_pages()

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Sidebar")
        frame.setFixedWidth(220)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        title = QLabel("Finance")
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_group.idClicked.connect(self._on_nav_changed)

        for index, label in enumerate(self.nav_labels):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            self.nav_group.addButton(button, index)
            layout.addWidget(button)

        layout.addStretch()
        return frame

    def _build_topbar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("TopBar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("PageTitle")
        layout.addWidget(self.page_title)

        layout.addStretch(1)

        month_label = QLabel("Month")
        month_label.setObjectName("MutedLabel")
        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(120)
        self.month_combo.currentTextChanged.connect(self._refresh_pages)

        search_label = QLabel("Search")
        search_label.setObjectName("MutedLabel")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter transactions...")
        self.search_input.textChanged.connect(self._refresh_pages)

        self.report_button = QPushButton("Export Report")
        self.report_button.setObjectName("ToolbarButton")
        self.report_button.clicked.connect(self._export_report)

        self.import_button = QPushButton("Import CSV")
        self.import_button.setObjectName("ToolbarButton")
        self.import_button.clicked.connect(self._import_csv)

        layout.addWidget(month_label)
        layout.addWidget(self.month_combo)
        layout.addWidget(search_label)
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.report_button)
        layout.addWidget(self.import_button)
        return frame

    def _on_nav_changed(self, page_index: int) -> None:
        self.stacked.setCurrentIndex(page_index)
        self.page_title.setText(self.nav_labels[page_index])
        self._animate_current_page()

    def _animate_current_page(self) -> None:
        current_widget = self.stacked.currentWidget()
        if current_widget is None:
            return

        if self._page_fade_animation is not None:
            self._page_fade_animation.stop()
            self._page_fade_animation = None

        effect = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(220)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def clear_effect() -> None:
            current_widget.setGraphicsEffect(None)
            effect.deleteLater()

        animation.finished.connect(clear_effect)
        self._page_fade_animation = animation
        animation.start()

    def _reload_months(self, preferred_month: str | None = None) -> None:
        available = self.service.get_available_months()
        if not available:
            available = [date.today().strftime("%Y-%m")]

        fallback = preferred_month or self.month_combo.currentText() or available[0]
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        self.month_combo.addItems(available)

        if fallback in available:
            self.month_combo.setCurrentText(fallback)
        else:
            self.month_combo.setCurrentIndex(0)
        self.month_combo.blockSignals(False)

    def _refresh_pages(self) -> None:
        month = self.month_combo.currentText()
        if not month:
            return
        search = self.search_input.text().strip()
        self.dashboard_page.refresh(month=month, search=search)
        self.transactions_page.refresh(month=month, search=search)
        self.budgets_page.refresh(month=month, _search=search)
        self.goals_page.refresh(_month=month, _search=search)
        self.settings_page.refresh()

    def _handle_data_changed(self) -> None:
        current = self.month_combo.currentText()
        self._reload_months(preferred_month=current)
        self._refresh_pages()

    def _import_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Transactions CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            imported, skipped = self.service.import_csv(file_path)
        except ValueError as exc:
            QMessageBox.warning(self, "Import Failed", str(exc))
            return

        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported: {imported}\nSkipped duplicates: {skipped}",
        )
        self._handle_data_changed()

    def _export_report(self) -> None:
        month = self.month_combo.currentText()
        if not month:
            QMessageBox.information(self, "No Month", "Select a month first.")
            return

        suggested_name = f"finance-report-{month}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Monthly Report", suggested_name, "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            report_path = self.service.export_monthly_report_csv(
                month=month,
                destination=file_path,
                search=self.search_input.text().strip(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Export Failed", str(exc))
            return

        QMessageBox.information(self, "Report Exported", f"Saved report to:\n{report_path}")
