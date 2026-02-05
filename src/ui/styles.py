"""
Qt Stylesheet Definitions

Provides consistent, modern styling for the application using Qt stylesheets.
"""

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
}

/* Sidebar styling */
QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 4px;
}

QTreeWidget::item {
    padding: 8px 4px;
    border-radius: 4px;
}

QTreeWidget::item:hover {
    background-color: #f0f0f0;
}

QTreeWidget::item:selected {
    background-color: #e3f2fd;
    color: #1976d2;
}

/* Button styling */
QPushButton {
    background-color: #1976d2;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1565c0;
}

QPushButton:pressed {
    background-color: #0d47a1;
}

QPushButton:disabled {
    background-color: #bdbdbd;
    color: #757575;
}

QPushButton[type="secondary"] {
    background-color: #ffffff;
    color: #424242;
    border: 1px solid #e0e0e0;
}

QPushButton[type="secondary"]:hover {
    background-color: #f5f5f5;
}

QPushButton[type="danger"] {
    background-color: #d32f2f;
}

QPushButton[type="danger"]:hover {
    background-color: #c62828;
}

/* Table styling */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    gridline-color: #f0f0f0;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #e3f2fd;
    color: #1976d2;
}

QHeaderView::section {
    background-color: #fafafa;
    border: none;
    border-bottom: 2px solid #e0e0e0;
    padding: 10px;
    font-weight: 600;
    color: #424242;
}

/* Input styling */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #1976d2;
    outline: none;
}

QTextEdit {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px;
    background-color: #ffffff;
}

QTextEdit:focus {
    border-color: #1976d2;
}

/* ComboBox dropdown */
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

/* Checkbox styling */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #bdbdbd;
    border-radius: 4px;
}

QCheckBox::indicator:checked {
    background-color: #1976d2;
    border-color: #1976d2;
}

/* Group box styling */
QGroupBox {
    font-weight: 600;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #424242;
}

/* Splitter styling */
QSplitter::handle {
    background-color: #e0e0e0;
}

QSplitter::handle:horizontal {
    width: 1px;
}

/* Tab styling */
QTabWidget::pane {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    background-color: #ffffff;
}

QTabBar::tab {
    padding: 10px 20px;
    margin-right: 4px;
    border: 1px solid transparent;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-color: #e0e0e0;
}

QTabBar::tab:!selected {
    background-color: #f5f5f5;
}

/* Scrollbar styling */
QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #bdbdbd;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9e9e9e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Status bar */
QStatusBar {
    background-color: #fafafa;
    border-top: 1px solid #e0e0e0;
}

/* Labels */
QLabel[type="heading"] {
    font-size: 18px;
    font-weight: 600;
    color: #212121;
}

QLabel[type="subheading"] {
    font-size: 14px;
    color: #757575;
}

/* Dialog styling */
QDialog {
    background-color: #ffffff;
}

/* Message box */
QMessageBox {
    background-color: #ffffff;
}
"""