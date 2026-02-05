"""
Data Grid Widget Module

Displays Cassandra table records in a paginated grid view.
Supports filtering, selection, and CRUD operations.
"""

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QSpinBox, QHeaderView, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal

from src.database.schema import TableSchema
from src.utils.type_mapping import format_value_for_display


class DataGrid(QWidget):
    """
    Paginated data grid for displaying table records.

    Features:
    - Paginated browsing
    - Column sorting (visual only)
    - Row selection for edit/delete
    - Partition key filtering
    """

    record_selected = Signal(dict)  # Emits selected record
    insert_requested = Signal()
    edit_requested = Signal(dict)  # Emits record to edit
    delete_requested = Signal(dict)  # Emits record to delete
    refresh_requested = Signal()
    filter_changed = Signal(dict)  # Emits filter parameters

    def __init__(self, parent=None):
        super().__init__(parent)
        self._schema: Optional[TableSchema] = None
        self._records: list[dict] = []
        self._page = 0
        self._page_size = 50
        self._total_records = 0

        self._setup_ui()

    def _setup_ui(self):
        """Set up the grid UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()

        # Filter controls
        filter_label = QLabel("Filter by Partition Key:")
        toolbar.addWidget(filter_label)

        self.filter_column = QComboBox()
        self.filter_column.setMinimumWidth(120)
        toolbar.addWidget(self.filter_column)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Enter value...")
        self.filter_input.setMaximumWidth(200)
        self.filter_input.returnPressed.connect(self._apply_filter)
        toolbar.addWidget(self.filter_input)

        self.filter_button = QPushButton("Filter")
        self.filter_button.setProperty("type", "secondary")
        self.filter_button.clicked.connect(self._apply_filter)
        toolbar.addWidget(self.filter_button)

        self.clear_filter_button = QPushButton("Clear")
        self.clear_filter_button.setProperty("type", "secondary")
        self.clear_filter_button.clicked.connect(self._clear_filter)
        toolbar.addWidget(self.clear_filter_button)

        toolbar.addStretch()

        # CRUD buttons
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("type", "secondary")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        toolbar.addWidget(self.refresh_button)

        self.insert_button = QPushButton("+ Insert")
        self.insert_button.clicked.connect(self.insert_requested.emit)
        toolbar.addWidget(self.insert_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.setProperty("type", "secondary")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setProperty("type", "danger")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_button)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_double_click)

        # Configure header
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        layout.addWidget(self.table)

        # Pagination
        pagination = QHBoxLayout()

        self.page_label = QLabel("Page 1")
        pagination.addWidget(self.page_label)

        self.prev_button = QPushButton("← Previous")
        self.prev_button.setProperty("type", "secondary")
        self.prev_button.clicked.connect(self._prev_page)
        pagination.addWidget(self.prev_button)

        self.next_button = QPushButton("Next →")
        self.next_button.setProperty("type", "secondary")
        self.next_button.clicked.connect(self._next_page)
        pagination.addWidget(self.next_button)

        pagination.addStretch()

        pagination.addWidget(QLabel("Page Size:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(10, 500)
        self.page_size_spin.setValue(50)
        self.page_size_spin.valueChanged.connect(self._on_page_size_changed)
        pagination.addWidget(self.page_size_spin)

        self.record_count_label = QLabel("0 records")
        pagination.addWidget(self.record_count_label)

        layout.addLayout(pagination)

    def set_schema(self, schema: TableSchema) -> None:
        """
        Set the table schema and configure columns.

        Args:
            schema: Table schema for column configuration.
        """
        self._schema = schema

        # Update filter column dropdown
        self.filter_column.clear()
        for col in schema.partition_keys:
            self.filter_column.addItem(col.name)

        # Set up table columns
        columns = schema.all_columns_sorted
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([col.name for col in columns])

    def set_data(self, records: list[dict], total_count: int = None) -> None:
        """
        Set the grid data.

        Args:
            records: List of record dictionaries.
            total_count: Total number of records (for pagination info).
        """
        self._records = records
        self._total_records = total_count or len(records)

        self._update_table()
        self._update_pagination()

    def _update_table(self) -> None:
        """Update table contents with current records."""
        if not self._schema:
            return

        columns = self._schema.all_columns_sorted
        self.table.setRowCount(len(self._records))

        for row_idx, record in enumerate(self._records):
            for col_idx, col in enumerate(columns):
                value = record.get(col.name)
                display_value = format_value_for_display(value, col.cql_type)

                item = QTableWidgetItem(display_value)
                item.setData(Qt.UserRole, value)  # Store original value

                # Visual indication for primary key columns
                if col.is_primary_key:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.table.setItem(row_idx, col_idx, item)

        self.record_count_label.setText(f"{self._total_records} records")

    def _update_pagination(self) -> None:
        """Update pagination controls."""
        total_pages = max(1, (self._total_records + self._page_size - 1) // self._page_size)
        self.page_label.setText(f"Page {self._page + 1} of {total_pages}")

        self.prev_button.setEnabled(self._page > 0)
        self.next_button.setEnabled((self._page + 1) * self._page_size < self._total_records)

    def _on_selection_changed(self) -> None:
        """Handle row selection change."""
        selected = self.table.selectedItems()
        has_selection = len(selected) > 0

        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

        if has_selection:
            row = self.table.currentRow()
            if 0 <= row < len(self._records):
                self.record_selected.emit(self._records[row])

    def _on_double_click(self, row: int, column: int) -> None:
        """Handle double-click on a row."""
        if 0 <= row < len(self._records):
            self.edit_requested.emit(self._records[row])

    def _on_edit(self) -> None:
        """Handle edit button click."""
        row = self.table.currentRow()
        if 0 <= row < len(self._records):
            self.edit_requested.emit(self._records[row])

    def _on_delete(self) -> None:
        """Handle delete button click with confirmation."""
        row = self.table.currentRow()
        if 0 <= row < len(self._records):
            record = self._records[row]

            # Build confirmation message
            pk_info = []
            if self._schema:
                for col in self._schema.primary_key_columns:
                    pk_info.append(f"{col.name}={record.get(col.name)}")

            result = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete this record?\n\n{', '.join(pk_info)}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if result == QMessageBox.Yes:
                self.delete_requested.emit(record)

    def _apply_filter(self) -> None:
        """Apply the current filter."""
        column = self.filter_column.currentText()
        value = self.filter_input.text().strip()

        if column and value:
            self._page = 0
            self.filter_changed.emit({column: value})

    def _clear_filter(self) -> None:
        """Clear the current filter."""
        self.filter_input.clear()
        self._page = 0
        self.filter_changed.emit({})

    def _prev_page(self) -> None:
        """Go to previous page."""
        if self._page > 0:
            self._page -= 1
            self.refresh_requested.emit()

    def _next_page(self) -> None:
        """Go to next page."""
        if (self._page + 1) * self._page_size < self._total_records:
            self._page += 1
            self.refresh_requested.emit()

    def _on_page_size_changed(self, value: int) -> None:
        """Handle page size change."""
        self._page_size = value
        self._page = 0
        self.refresh_requested.emit()

    @property
    def current_page(self) -> int:
        return self._page

    @property
    def page_size(self) -> int:
        return self._page_size

    def get_selected_record(self) -> Optional[dict]:
        """Get the currently selected record."""
        row = self.table.currentRow()
        if 0 <= row < len(self._records):
            return self._records[row]
        return None