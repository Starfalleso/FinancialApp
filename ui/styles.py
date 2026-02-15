from __future__ import annotations

from PySide6.QtWidgets import QApplication


DARK_STYLESHEET = """
QMainWindow, QWidget#AppRoot {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #070d18,
        stop: 0.55 #0b1220,
        stop: 1 #0d1628
    );
    color: #e5e7eb;
    font-family: "Segoe UI Variable Text", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}

QWidget#ContentShell {
    background: transparent;
}

QFrame#Sidebar {
    background-color: rgba(11, 20, 36, 0.92);
    border-right: 1px solid #1e293b;
}

QLabel#AppTitle {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #f8fafc;
    padding: 8px 12px 10px 12px;
}

QPushButton#NavButton {
    text-align: left;
    border: 1px solid rgba(148, 163, 184, 0.10);
    border-radius: 10px;
    padding: 11px 12px;
    background-color: rgba(15, 23, 42, 0.55);
    color: #cbd5e1;
    font-weight: 600;
}

QPushButton#NavButton:hover {
    background-color: rgba(37, 99, 235, 0.12);
    border-color: rgba(96, 165, 250, 0.45);
}

QPushButton#NavButton:checked {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #1d4ed8,
        stop: 1 #2563eb
    );
    color: #ffffff;
    border-color: #60a5fa;
}

QFrame#TopBar {
    background-color: rgba(17, 24, 39, 0.82);
    border: 1px solid rgba(100, 116, 139, 0.22);
    border-radius: 12px;
}

QLabel#PageTitle {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
    padding-right: 8px;
}

QLabel#MutedLabel {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

QFrame#Card, QFrame#KpiCard {
    background-color: rgba(17, 24, 39, 0.86);
    border: 1px solid rgba(100, 116, 139, 0.20);
    border-radius: 14px;
}

QFrame#Card:hover, QFrame#KpiCard:hover {
    border-color: rgba(96, 165, 250, 0.38);
}

QLabel#KpiTitle {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}

QLabel#KpiValue {
    color: #f1f5f9;
    font-size: 24px;
    font-weight: 700;
}

QLabel#KpiHint {
    color: #7dd3fc;
    font-size: 11px;
}

QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
    background-color: rgba(15, 23, 42, 0.92);
    border: 1px solid rgba(100, 116, 139, 0.38);
    border-radius: 8px;
    padding: 6px 9px;
    min-height: 29px;
    color: #e5e7eb;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
    border: 1px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    border: 1px solid #334155;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
}

QCheckBox {
    color: #cbd5e1;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #475569;
    border-radius: 3px;
    background: #0f172a;
}

QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #3b82f6;
}

QPushButton {
    border: 1px solid rgba(100, 116, 139, 0.34);
    border-radius: 8px;
    padding: 7px 12px;
    background-color: rgba(31, 41, 55, 0.82);
    color: #f9fafb;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(51, 65, 85, 0.95);
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton#PrimaryButton {
    background-color: #2563eb;
    border-color: #3b82f6;
}

QPushButton#PrimaryButton:hover {
    background-color: #1d4ed8;
}

QPushButton#ToolbarButton {
    background-color: rgba(37, 99, 235, 0.16);
    border-color: rgba(96, 165, 250, 0.48);
}

QPushButton#ToolbarButton:hover {
    background-color: rgba(37, 99, 235, 0.28);
}

QTableWidget {
    background-color: rgba(15, 23, 42, 0.82);
    alternate-background-color: rgba(17, 24, 39, 0.9);
    gridline-color: #253044;
    border: 1px solid rgba(100, 116, 139, 0.22);
    border-radius: 10px;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
    padding: 2px;
}

QHeaderView::section {
    background-color: rgba(15, 23, 42, 0.95);
    color: #d1d5db;
    border: none;
    border-right: 1px solid #253044;
    border-bottom: 1px solid #253044;
    padding: 8px;
    font-weight: 600;
}

QTableCornerButton::section {
    background-color: rgba(15, 23, 42, 0.95);
    border: 1px solid #253044;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px 2px 4px 2px;
}

QScrollBar::handle:vertical {
    background: rgba(148, 163, 184, 0.38);
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(148, 163, 184, 0.58);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px 4px 2px 4px;
}

QScrollBar::handle:horizontal {
    background: rgba(148, 163, 184, 0.38);
    min-width: 20px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(148, 163, 184, 0.58);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QToolTip {
    background-color: #0f172a;
    color: #f9fafb;
    border: 1px solid #334155;
    padding: 4px 6px;
}
"""


def apply_dark_theme(app: QApplication) -> None:
    app.setStyleSheet(DARK_STYLESHEET)
