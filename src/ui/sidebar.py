"""
Navigation Sidebar Widget

Displays hierarchical view of connections, keyspaces, and tables.
Handles user interaction for navigation and selection.
"""

from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QLabel, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from src.config.settings import ConnectionProfile


class NavigationSidebar(QWidget):
    """
    Sidebar widget for navigating database structure.

    Displays connections, keyspaces, and tables in a tree view.
    Emits signals when items are selected or actions are triggered.
    """

    # Signals
    connection_selected = Signal(str)  # Connection name
    connection_add_requested = Signal()
    connection_edit_requested = Signal(str)  # Connection name
    connection_delete_requested = Signal(str)  # Connection name
    keyspace_selected = Signal(str)  # Keyspace name
    table_selected = Signal(str, str)  # Keyspace, table name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Navigator")
        header_label.setProperty("type", "heading")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(28, 28)
        self.add_button.setToolTip("Add Connection")
        self.add_button.clicked.connect(self.connection_add_requested.emit)
        header_layout.addWidget(self.add_button)

        layout.addLayout(header_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

    def set_connections(self, connections: list[ConnectionProfile], active_name: str = None):
        """
        Update the list of connections in the tree.

        Args:
            connections: List of connection profiles.
            active_name: Name of the currently active connection.
        """
        # Store current expansion state
        expanded_items = set()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.isExpanded():
                expanded_items.add(item.text(0))

        self.tree.clear()

        for conn in connections:
            item = QTreeWidgetItem([conn.name])
            item.setData(0, Qt.UserRole, {"type": "connection", "name": conn.name})

            if conn.name == active_name:
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)

            self.tree.addTopLevelItem(item)

            # Restore expansion
            if conn.name in expanded_items:
                item.setExpanded(True)

    def set_keyspaces(self, connection_name: str, keyspaces: list[str]):
        """
        Update keyspaces for a connection.

        Args:
            connection_name: Name of the connection.
            keyspaces: List of keyspace names.
        """
        # Find connection item
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            data = item.data(0, Qt.UserRole)
            if data and data.get("name") == connection_name:
                # Clear existing keyspaces
                item.takeChildren()

                # Add keyspaces
                for ks in keyspaces:
                    ks_item = QTreeWidgetItem([ks])
                    ks_item.setData(0, Qt.UserRole, {
                        "type": "keyspace",
                        "connection": connection_name,
                        "name": ks
                    })
                    item.addChild(ks_item)

                item.setExpanded(True)
                break

    def set_tables(self, connection_name: str, keyspace: str, tables: list[str]):
        """
        Update tables for a keyspace.

        Args:
            connection_name: Name of the connection.
            keyspace: Keyspace name.
            tables: List of table names.
        """
        # Find keyspace item
        for i in range(self.tree.topLevelItemCount()):
            conn_item = self.tree.topLevelItem(i)
            conn_data = conn_item.data(0, Qt.UserRole)

            if conn_data and conn_data.get("name") == connection_name:
                for j in range(conn_item.childCount()):
                    ks_item = conn_item.child(j)
                    ks_data = ks_item.data(0, Qt.UserRole)

                    if ks_data and ks_data.get("name") == keyspace:
                        # Clear existing tables
                        ks_item.takeChildren()

                        # Add tables
                        for table in tables:
                            table_item = QTreeWidgetItem([table])
                            table_item.setData(0, Qt.UserRole, {
                                "type": "table",
                                "connection": connection_name,
                                "keyspace": keyspace,
                                "name": table
                            })
                            ks_item.addChild(table_item)

                        ks_item.setExpanded(True)
                        return

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle single click on tree item."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get("type")

        if item_type == "connection":
            self.connection_selected.emit(data["name"])
        elif item_type == "keyspace":
            self.keyspace_selected.emit(data["name"])
        elif item_type == "table":
            self.table_selected.emit(data["keyspace"], data["name"])

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double click on tree item."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get("type")

        if item_type == "table":
            self.table_selected.emit(data["keyspace"], data["name"])

    def _show_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        menu = QMenu(self)
        item_type = data.get("type")

        if item_type == "connection":
            edit_action = QAction("Edit Connection", self)
            edit_action.triggered.connect(
                lambda: self.connection_edit_requested.emit(data["name"])
            )
            menu.addAction(edit_action)

            delete_action = QAction("Delete Connection", self)
            delete_action.triggered.connect(
                lambda: self.connection_delete_requested.emit(data["name"])
            )
            menu.addAction(delete_action)

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(position))