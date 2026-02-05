"""
Dynamic Form Generation Module

Generates form widgets dynamically based on Cassandra table schema.
Handles type-specific input widgets, validation, and data conversion.
"""

from typing import Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QScrollArea,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit,
    QDateEdit, QTimeEdit, QDateTimeEdit, QPushButton, QLabel,
    QGroupBox, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime, Signal
from datetime import datetime, date, time

from src.database.schema import TableSchema, ColumnInfo
from src.utils.type_mapping import get_type_info, convert_value, format_value_for_display


class DynamicFormField(QWidget):
    """
    A single form field that adapts to Cassandra column type.

    Automatically creates the appropriate input widget based on the
    column's CQL type and provides value getting/setting methods.
    """

    value_changed = Signal()

    def __init__(self, column: ColumnInfo, parent=None):
        """
        Initialize form field for a column.

        Args:
            column: Column information from schema.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._column = column
        self._type_info = get_type_info(column.cql_type)
        self._widget = None

        self._setup_ui()

    def _setup_ui(self):
        """Create the appropriate widget for the column type."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        widget_type = self._type_info.get('widget', 'lineedit')

        if widget_type == 'spinbox':
            self._widget = QSpinBox()
            self._widget.setRange(
                self._type_info.get('min', -2147483648),
                self._type_info.get('max', 2147483647)
            )
            self._widget.valueChanged.connect(self.value_changed.emit)

        elif widget_type == 'doublespinbox':
            self._widget = QDoubleSpinBox()
            self._widget.setRange(-1e15, 1e15)
            self._widget.setDecimals(6)
            self._widget.valueChanged.connect(self.value_changed.emit)

        elif widget_type == 'checkbox':
            self._widget = QCheckBox()
            self._widget.stateChanged.connect(self.value_changed.emit)

        elif widget_type == 'textedit':
            self._widget = QTextEdit()
            self._widget.setMaximumHeight(100)
            placeholder = self._type_info.get('placeholder', '')
            if placeholder:
                self._widget.setPlaceholderText(placeholder)
            self._widget.textChanged.connect(self.value_changed.emit)

        elif widget_type == 'datetime':
            self._widget = QDateTimeEdit()
            self._widget.setCalendarPopup(True)
            self._widget.setDateTime(QDateTime.currentDateTime())
            self._widget.dateTimeChanged.connect(self.value_changed.emit)

        elif widget_type == 'date':
            self._widget = QDateEdit()
            self._widget.setCalendarPopup(True)
            self._widget.setDate(QDate.currentDate())
            self._widget.dateChanged.connect(self.value_changed.emit)

        elif widget_type == 'time':
            self._widget = QTimeEdit()
            self._widget.setTime(QTime.currentTime())
            self._widget.timeChanged.connect(self.value_changed.emit)

        else:  # Default: lineedit
            self._widget = QLineEdit()
            placeholder = self._type_info.get('placeholder', '')
            if placeholder:
                self._widget.setPlaceholderText(placeholder)
            self._widget.textChanged.connect(self.value_changed.emit)

        # Mark required fields
        if self._column.is_primary_key:
            self._widget.setProperty("required", True)

        # Set readonly if needed
        if self._type_info.get('readonly'):
            self._widget.setEnabled(False)

        layout.addWidget(self._widget)

    @property
    def column(self) -> ColumnInfo:
        """Get the column info."""
        return self._column

    def get_value(self) -> Any:
        """
        Get the current value from the widget.

        Returns:
            Value converted to appropriate Python type.
        """
        widget_type = self._type_info.get('widget', 'lineedit')

        if widget_type == 'spinbox':
            return self._widget.value()
        elif widget_type == 'doublespinbox':
            return self._widget.value()
        elif widget_type == 'checkbox':
            return self._widget.isChecked()
        elif widget_type == 'textedit':
            return self._widget.toPlainText()
        elif widget_type == 'datetime':
            return self._widget.dateTime().toPython()
        elif widget_type == 'date':
            return self._widget.date().toPython()
        elif widget_type == 'time':
            return self._widget.time().toPython()
        else:
            return self._widget.text()

    def set_value(self, value: Any) -> None:
        """
        Set the widget value.

        Args:
            value: Value to set (will be formatted appropriately).
        """
        if value is None:
            self.clear()
            return

        widget_type = self._type_info.get('widget', 'lineedit')

        try:
            if widget_type == 'spinbox':
                self._widget.setValue(int(value))
            elif widget_type == 'doublespinbox':
                self._widget.setValue(float(value))
            elif widget_type == 'checkbox':
                self._widget.setChecked(bool(value))
            elif widget_type == 'textedit':
                formatted = format_value_for_display(value, self._column.cql_type)
                self._widget.setPlainText(formatted)
            elif widget_type == 'datetime':
                if isinstance(value, datetime):
                    self._widget.setDateTime(QDateTime(value))
                else:
                    self._widget.setDateTime(QDateTime.fromString(str(value), Qt.ISODate))
            elif widget_type == 'date':
                if isinstance(value, date):
                    self._widget.setDate(QDate(value.year, value.month, value.day))
                else:
                    self._widget.setDate(QDate.fromString(str(value), Qt.ISODate))
            elif widget_type == 'time':
                if isinstance(value, time):
                    self._widget.setTime(QTime(value.hour, value.minute, value.second))
                else:
                    self._widget.setTime(QTime.fromString(str(value)))
            else:
                formatted = format_value_for_display(value, self._column.cql_type)
                self._widget.setText(formatted)
        except Exception as e:
            print(f"Warning: Could not set value for {self._column.name}: {e}")

    def clear(self) -> None:
        """Clear the widget value."""
        widget_type = self._type_info.get('widget', 'lineedit')

        if widget_type == 'spinbox':
            self._widget.setValue(0)
        elif widget_type == 'doublespinbox':
            self._widget.setValue(0.0)
        elif widget_type == 'checkbox':
            self._widget.setChecked(False)
        elif widget_type == 'textedit':
            self._widget.clear()
        elif widget_type == 'datetime':
            self._widget.setDateTime(QDateTime.currentDateTime())
        elif widget_type == 'date':
            self._widget.setDate(QDate.currentDate())
        elif widget_type == 'time':
            self._widget.setTime(QTime.currentTime())
        else:
            self._widget.clear()

    def set_readonly(self, readonly: bool) -> None:
        """Set field as readonly."""
        if hasattr(self._widget, 'setReadOnly'):
            self._widget.setReadOnly(readonly)
        else:
            self._widget.setEnabled(not readonly)


class DynamicRecordForm(QWidget):
    """
    Complete form for editing/inserting a Cassandra record.

    Dynamically generates form fields based on table schema,
    groups primary key fields separately, and handles validation.
    """

    submitted = Signal(dict)  # Emits the record data
    cancelled = Signal()

    def __init__(self, schema: TableSchema, parent=None):
        """
        Initialize the record form.

        Args:
            schema: Table schema for form generation.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._schema = schema
        self._fields: dict[str, DynamicFormField] = {}
        self._mode = "insert"  # "insert" or "update"
        self._original_record = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the form UI with all fields."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Title
        title_label = QLabel(f"Record: {self._schema.table_name}")
        title_label.setProperty("type", "heading")
        layout.addWidget(title_label)

        # Scroll area for fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # Primary key fields group
        pk_group = QGroupBox("Primary Key (Required)")
        pk_layout = QFormLayout(pk_group)
        pk_layout.setSpacing(8)

        for col in self._schema.primary_key_columns:
            field = DynamicFormField(col)
            self._fields[col.name] = field

            label_text = f"{col.name}"
            if col.is_partition_key:
                label_text += " (partition)"
            else:
                label_text += " (clustering)"

            pk_layout.addRow(f"{label_text}:", field)

        scroll_layout.addWidget(pk_group)

        # Regular columns group
        if self._schema.regular_columns:
            reg_group = QGroupBox("Columns")
            reg_layout = QFormLayout(reg_group)
            reg_layout.setSpacing(8)

            for col in self._schema.regular_columns:
                field = DynamicFormField(col)
                self._fields[col.name] = field

                label = QLabel(f"{col.name} ({col.cql_type}):")
                reg_layout.addRow(label, field)

            scroll_layout.addWidget(reg_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("type", "secondary")
        self.cancel_button.clicked.connect(self.cancelled.emit)
        button_layout.addWidget(self.cancel_button)

        self.submit_button = QPushButton("Insert Record")
        self.submit_button.clicked.connect(self._on_submit)
        button_layout.addWidget(self.submit_button)

        layout.addLayout(button_layout)

    def set_mode(self, mode: str) -> None:
        """
        Set form mode (insert or update).

        Args:
            mode: "insert" or "update"
        """
        self._mode = mode

        if mode == "update":
            self.submit_button.setText("Update Record")
            # Make primary keys readonly in update mode
            for col in self._schema.primary_key_columns:
                if col.name in self._fields:
                    self._fields[col.name].set_readonly(True)
        else:
            self.submit_button.setText("Insert Record")
            for field in self._fields.values():
                field.set_readonly(False)

    def load_record(self, record: dict) -> None:
        """
        Load a record into the form for editing.

        Args:
            record: Record data dictionary.
        """
        self._original_record = record

        for col_name, field in self._fields.items():
            if col_name in record:
                field.set_value(record[col_name])
            else:
                field.clear()

    def clear(self) -> None:
        """Clear all form fields."""
        self._original_record = None
        for field in self._fields.values():
            field.clear()

    def _validate(self) -> tuple[bool, str]:
        """
        Validate form data.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check primary key fields are filled
        for col in self._schema.primary_key_columns:
            field = self._fields.get(col.name)
            if field:
                value = field.get_value()
                if value is None or value == '':
                    # UUID fields can be auto-generated
                    if col.cql_type != 'uuid':
                        return False, f"Primary key field '{col.name}' is required."

        return True, ""

    def _on_submit(self) -> None:
        """Handle form submission."""
        is_valid, error = self._validate()

        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error)
            return

        # Collect and convert values
        record = {}
        for col_name, field in self._fields.items():
            raw_value = field.get_value()
            if raw_value is not None and raw_value != '':
                try:
                    converted = convert_value(raw_value, field.column.cql_type)
                    record[col_name] = converted
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Conversion Error",
                        f"Invalid value for '{col_name}': {e}"
                    )
                    return

        self.submitted.emit(record)

    def get_data(self) -> dict:
        """
        Get current form data.

        Returns:
            Dictionary of column names to values.
        """
        record = {}
        for col_name, field in self._fields.items():
            raw_value = field.get_value()
            if raw_value is not None and raw_value != '':
                try:
                    converted = convert_value(raw_value, field.column.cql_type)
                    record[col_name] = converted
                except:
                    record[col_name] = raw_value
        return record