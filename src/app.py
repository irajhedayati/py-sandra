"""
Main Application Logic

Coordinates all components of the Cassandra GUI client:
- Connection management
- Schema navigation
- Data browsing and CRUD operations
"""

from typing import Dict, Any, List
import re

import pandas as pd
import streamlit as st

from src.config.settings import ConfigManager, ConnectionProfile
from src.database.connection import CassandraConnectionManager
from src.database.schema import SchemaInspector, TableSchema


# noinspection SqlNoDataSourceInspection
class CassandraGUIApp:
    """
    Main application controller for Cassandra GUI Client.
    """

    def __init__(self):
        # Initialize session state
        if 'config_manager' not in st.session_state:
            st.session_state.config_manager = ConfigManager()
        if 'connection_manager' not in st.session_state:
            st.session_state.connection_manager = CassandraConnectionManager()
        if 'schema_inspector' not in st.session_state:
            st.session_state.schema_inspector = None
        
        self._config = st.session_state.config_manager
        self._connection = st.session_state.connection_manager
        
        # Load settings
        if 'settings' not in st.session_state:
            st.session_state.settings = self._config.load()

    def run(self):
        """Run the main application loop."""
        self._render_sidebar()
        self._render_main_content()
        self._render_delete_confirmation()
        self._render_map_schema_editor()

    def _render_sidebar(self):
        """Render the sidebar for navigation and connection management."""
        with st.sidebar:
            st.title("Cassandra GUI")
            
            # Connection Management
            st.header("Connections")
            
            connections = self._config.get_all_connections()
            connection_names = [c.name for c in connections]
            
            selected_conn = st.selectbox(
                "Select Connection",
                ["Select..."] + connection_names,
                key="selected_connection"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Connect", disabled=selected_conn == "Select..."):
                    self._connect_to_profile(selected_conn)
            with col2:
                if st.button("Disconnect", disabled=not self._connection.is_connected):
                    self._disconnect()

            # Add/Edit Connection
            with st.expander("Manage Connections"):
                self._render_connection_form()

            # Schema Navigation
            if self._connection.is_connected and st.session_state.schema_inspector:
                st.divider()
                st.header("Schema")
                
                keyspaces = st.session_state.schema_inspector.get_keyspaces()
                selected_ks = st.selectbox("Keyspace", keyspaces, key="selected_keyspace")
                
                if selected_ks:
                    tables = st.session_state.schema_inspector.get_tables(selected_ks)
                    selected_table = st.selectbox("Table", tables, key="selected_table")
                    
                    if selected_table:
                        # Reset pagination when table changes
                        if 'current_table_name' not in st.session_state or st.session_state.current_table_name != selected_table:
                            st.session_state.current_table_name = selected_table
                            st.session_state.paging_state = None
                            st.session_state.page_history = []
                        
                        st.session_state.current_table_schema = st.session_state.schema_inspector.get_table_schema(selected_ks, selected_table)

    def _render_main_content(self):
        """Render the main content area."""
        if not self._connection.is_connected:
            st.info("Please select a connection and click 'Connect' to start.")
            return

        if 'current_table_schema' in st.session_state and st.session_state.current_table_schema:
            schema = st.session_state.current_table_schema
            st.header(f"Table: {schema.keyspace}.{schema.table_name}")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Data Browser", "Insert Record", "Table Info", "CQL Editor"])
            
            with tab1:
                self._render_data_grid(schema)
            
            with tab2:
                self._render_insert_form(schema)
                
            with tab3:
                self._render_table_info(schema)
                
            with tab4:
                self._render_cql_editor()
        else:
            st.info("Select a keyspace and table from the sidebar to view data.")

    def _render_connection_form(self):
        """Render form for adding/editing connections."""
        with st.form("connection_form"):
            name = st.text_input("Name")
            hosts = st.text_input("Hosts (comma-separated)", "127.0.0.1")
            port = st.number_input("Port", value=9042)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Save Connection"):
                profile = ConnectionProfile(
                    name=name,
                    hosts=[h.strip() for h in hosts.split(",")],
                    port=port,
                    username=username if username else None,
                    password=password if password else None
                )
                self._config.add_connection(profile)
                st.success(f"Saved connection '{name}'")
                st.rerun()

    def _connect_to_profile(self, name: str):
        """Connect to the selected profile."""
        profile = self._config.get_connection(name)
        if profile:
            with st.spinner(f"Connecting to {name}..."):
                result = self._connection.connect(profile)
                if result.success:
                    st.session_state.schema_inspector = SchemaInspector(self._connection.session)
                    st.success(f"Connected to {name}")
                    st.rerun()
                else:
                    st.error(f"Connection failed: {result.message}")

    def _disconnect(self):
        """Disconnect from the current cluster."""
        self._connection.disconnect()
        st.session_state.schema_inspector = None
        if 'current_table_schema' in st.session_state:
            del st.session_state.current_table_schema
        st.rerun()

    def _render_data_grid(self, schema: TableSchema):
        """Render the data grid and filters."""
        # Determine visible columns
        visible_columns = []
        for col in schema.columns:
            meta = self._config.get_column_metadata(schema.keyspace, schema.table_name, col.name)
            if not meta.get("hide", False):
                visible_columns.append(col)

        # Filters
        with st.expander("Filters"):
            cols = st.columns(3)
            filter_params = {}
            for i, col in enumerate(schema.columns):
                # Simple filter implementation
                val = cols[i % 3].text_input(f"Filter {col.name}")
                if val:
                    filter_params[col.name] = val

        # Pagination Controls
        col1, col2, col3 = st.columns([1, 1, 4])
        page_size = col1.selectbox("Rows per page", [10, 25, 50], index=0, key="page_size_selector")
        
        # Initialize pagination state if needed
        if 'paging_state' not in st.session_state:
            st.session_state.paging_state = None
        if 'page_history' not in st.session_state:
            st.session_state.page_history = []

        # Query Data
        query = f"SELECT * FROM {schema.keyspace}.{schema.table_name}"
        
        # Reset pagination if filters change (simple detection)
        current_filter_hash = str(filter_params)
        if 'last_filter_hash' not in st.session_state or st.session_state.last_filter_hash != current_filter_hash:
            st.session_state.last_filter_hash = current_filter_hash
            st.session_state.paging_state = None
            st.session_state.page_history = []

        if filter_params:
            where_clauses = [f"{k} = %s" for k in filter_params.keys()]
            query += " WHERE " + " AND ".join(where_clauses) + " ALLOW FILTERING"
            # Note: In a real app, handle type conversion for params
            rows = self._connection.execute(
                query, 
                tuple(filter_params.values()), 
                page_size=page_size, 
                paging_state=st.session_state.paging_state
            )
        else:
            rows = self._connection.execute(
                query, 
                page_size=page_size, 
                paging_state=st.session_state.paging_state
            )

        # Display Data
        data = list(rows)
        
        # Pagination Buttons
        prev_col, next_col = col2.columns(2)
        
        # Previous Button
        if st.session_state.page_history:
            if prev_col.button("Previous"):
                # Pop current state (which we just used) and the previous one to go back
                st.session_state.paging_state = st.session_state.page_history.pop()
                st.rerun()
        else:
            prev_col.button("Previous", disabled=True)

        # Next Button
        if rows.has_more_pages:
            if next_col.button("Next"):
                st.session_state.page_history.append(st.session_state.paging_state)
                st.session_state.paging_state = rows.paging_state
                st.rerun()
        else:
            next_col.button("Next", disabled=True)

        if data:
            # Custom grid rendering to support row actions
            st.write("### Data")
            
            # Calculate column widths: 1 for actions, 2 for each visible data column
            col_spec = [0.5] + [1] * len(visible_columns)
            cols = st.columns(col_spec)
            
            # Header
            cols[0].markdown("**Actions**")
            for i, col in enumerate(visible_columns):
                if i + 1 < len(cols):
                    cols[i+1].markdown(f"**{col.name}**")
            
            # Rows
            for i, row in enumerate(data):
                cols = st.columns(col_spec)
                
                # Delete Action
                if cols[0].button("🗑️", key=f"del_{i}", help="Delete Row"):
                    self._confirm_delete(schema, row)
                
                # Data
                for j, col in enumerate(visible_columns):
                    if j + 1 < len(cols):
                        # row is a dict because of dict_factory in connection.py
                        val = row.get(col.name)
                        cols[j+1].write(str(val))
                        
        else:
            st.info("No data found.")

    def _confirm_delete(self, schema: TableSchema, row: Any):
        """Show confirmation dialog for deletion."""
        st.session_state.delete_target = {
            'schema': schema,
            'row': row
        }
        st.rerun()

    def _render_delete_confirmation(self):
        """Render delete confirmation dialog if needed."""
        if 'delete_target' in st.session_state:
            target = st.session_state.delete_target
            schema = target['schema']
            row = target['row']
            
            # Use a container at the top or a modal-like expander
            with st.container():
                st.warning("⚠️ Are you sure you want to delete this record?")
                st.json(row)  # Display the row data clearly
                
                col1, col2 = st.columns([1, 5])
                if col1.button("Yes, Delete", type="primary"):
                    self._delete_record(schema, row)
                    del st.session_state.delete_target
                    st.rerun()
                
                if col2.button("Cancel"):
                    del st.session_state.delete_target
                    st.rerun()

    def _delete_record(self, schema: TableSchema, row: Any):
        """Delete a record."""
        keyspace = schema.keyspace
        table = schema.table_name
        
        # Build WHERE clause using primary key
        where_parts = []
        where_values = []
        for col in schema.primary_key_columns:
            # row is a dict
            val = row.get(col.name)
            where_parts.append(f"{col.name} = %s")
            where_values.append(val)
            
        query = f"DELETE FROM {keyspace}.{table} WHERE {' AND '.join(where_parts)}"
        
        try:
            self._connection.execute(query, tuple(where_values))
            st.success("Record deleted successfully")
        except Exception as e:
            st.error(f"Delete failed: {str(e)}")

    def _render_insert_form(self, schema: TableSchema):
        """Render form for inserting new records."""
        with st.form("insert_form"):
            st.subheader("New Record")
            form_data = {}
            
            cols = st.columns(2)
            for i, col in enumerate(schema.columns):
                # Basic input field generation based on type could be improved
                form_data[col.name] = cols[i % 2].text_input(f"{col.name} ({col.cql_type})")
            
            if st.form_submit_button("Insert"):
                # Filter out empty strings
                data = {k: v for k, v in form_data.items() if v}
                if data:
                    self._insert_record(schema, data)

    def _render_table_info(self, schema: TableSchema):
        """Render table schema information."""
        st.subheader("Table Schema")
        
        # Header
        cols = st.columns([2, 2, 2, 2, 2])
        cols[0].markdown("**Column Name**")
        cols[1].markdown("**Type**")
        cols[2].markdown("**Key Type**")
        cols[3].markdown("**Hide in Data Browser**", help="Check to hide this column in the Data Browser tab. Useful for large columns like maps or lists.")
        cols[4].markdown("**Map Schema**", help="Define fixed schema for MAP columns.")

        for col in schema.all_columns_sorted:
            key_type = ""
            if col.is_partition_key:
                key_type = "Partition Key"
            elif col.is_clustering_key:
                key_type = f"Clustering Key ({col.clustering_order})"
            
            # Get current metadata state
            meta = self._config.get_column_metadata(schema.keyspace, schema.table_name, col.name)
            is_hidden = meta.get("hide", False)

            cols = st.columns([2, 2, 2, 2, 2])
            cols[0].write(col.name)
            cols[1].write(col.cql_type)
            cols[2].write(key_type)
            
            # Checkbox for hiding column
            new_hidden = cols[3].checkbox(
                "Hide", 
                value=is_hidden, 
                key=f"hide_{schema.keyspace}_{schema.table_name}_{col.name}",
                label_visibility="hidden"
            )
            
            # Update config if changed
            if new_hidden != is_hidden:
                self._config.set_column_metadata(
                    schema.keyspace, 
                    schema.table_name, 
                    col.name, 
                    "hide", 
                    new_hidden
                )
                st.rerun()

            # Map Schema Editor Button
            if col.cql_type.startswith("map<"):
                if cols[4].button("Edit Schema", key=f"edit_map_{col.name}"):
                    st.session_state.map_editor_target = {
                        'keyspace': schema.keyspace,
                        'table': schema.table_name,
                        'column': col.name,
                        'current_schema': meta.get("map_schema", [])
                    }
                    st.rerun()
            else:
                cols[4].write("-")

    def _render_map_schema_editor(self):
        """Render editor for Map column schema."""
        if 'map_editor_target' in st.session_state:
            target = st.session_state.map_editor_target
            keyspace = target['keyspace']
            table = target['table']
            column = target['column']
            current_schema = target['current_schema']
            
            # Use a modal-like container
            with st.container():
                st.markdown("---")
                st.subheader(f"Edit Map Schema for `{column}`")
                st.info("Define the fixed keys and their types for this MAP column. This helps in validating and displaying map data.")
                
                # Initialize working copy in session state if not present
                if 'map_schema_working_copy' not in st.session_state:
                    st.session_state.map_schema_working_copy = list(current_schema)

                working_copy = st.session_state.map_schema_working_copy
                
                # Display existing keys
                if working_copy:
                    st.write("Defined Keys:")
                    for i, item in enumerate(working_copy):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        c1.text_input("Key", value=item['key'], key=f"map_key_{i}", disabled=True)
                        c2.text_input("Type", value=item['type'], key=f"map_type_{i}", disabled=True)
                        if c3.button("Remove", key=f"remove_map_key_{i}"):
                            working_copy.pop(i)
                            st.rerun()
                else:
                    st.write("No keys defined yet.")

                st.markdown("#### Add New Key")
                with st.form("add_map_key_form"):
                    c1, c2 = st.columns([3, 2])
                    new_key = c1.text_input("Key Name")
                    new_type = c2.selectbox("Value Type", [
                        "text", "int", "bigint", "boolean", "float", "double", "timestamp", "uuid"
                    ])
                    
                    if st.form_submit_button("Add Key"):
                        if new_key:
                            # Check for duplicates
                            if any(k['key'] == new_key for k in working_copy):
                                st.error(f"Key '{new_key}' already exists.")
                            else:
                                working_copy.append({"key": new_key, "type": new_type})
                                st.rerun()
                        else:
                            st.error("Key name cannot be empty.")

                # Save/Cancel Actions
                st.markdown("---")
                c1, c2 = st.columns([1, 5])
                
                if c1.button("Save Schema", type="primary"):
                    self._config.set_column_metadata(
                        keyspace, 
                        table, 
                        column, 
                        "map_schema", 
                        working_copy
                    )
                    del st.session_state.map_editor_target
                    if 'map_schema_working_copy' in st.session_state:
                        del st.session_state.map_schema_working_copy
                    st.success("Map schema saved!")
                    st.rerun()
                
                if c2.button("Cancel", key="cancel_map_edit"):
                    del st.session_state.map_editor_target
                    if 'map_schema_working_copy' in st.session_state:
                        del st.session_state.map_schema_working_copy
                    st.rerun()

    def _insert_record(self, schema: TableSchema, data: Dict[str, Any]):
        """Execute insert query."""
        keyspace = schema.keyspace
        table = schema.table_name
        
        columns = list(data.keys())
        placeholders = ', '.join(['%s' for _ in columns])
        col_names = ', '.join(columns)
        
        query = f"INSERT INTO {keyspace}.{table} ({col_names}) VALUES ({placeholders})"
        
        try:
            # Note: Type conversion should be handled here
            self._connection.execute(query, tuple(data.values()))
            st.success("Record inserted successfully")
            st.rerun()
        except Exception as e:
            st.error(f"Insert failed: {str(e)}")

    def _render_cql_editor(self):
        """Render CQL Editor tab."""
        st.subheader("CQL Editor")
        
        # Query Input
        query = st.text_area("Enter CQL Query", height=150, help="Type your CQL query here.")
        
        # Options
        col1, col2 = st.columns([1, 3])
        extended_mode = col1.checkbox("Extended Mode", help="Show results in extended format (stacked columns). Limits results to 10.")
        
        if st.button("Execute", type="primary"):
            if not query.strip():
                st.warning("Please enter a query.")
                return
                
            # Handle Extended Mode Limit
            final_query = query
            if extended_mode:
                # Check for existing LIMIT
                limit_match = re.search(r'\bLIMIT\s+(\d+)', final_query, re.IGNORECASE)
                if limit_match:
                    st.warning(f"Extended mode overrides LIMIT {limit_match.group(1)} with LIMIT 10.")
                    final_query = re.sub(r'\bLIMIT\s+\d+', 'LIMIT 10', final_query, flags=re.IGNORECASE)
                else:
                    final_query += " LIMIT 10"
            
            try:
                # Execute Query
                # Note: We don't use pagination here as per typical editor behavior, 
                # but we could add it if needed. For extended mode, it's limited to 10 anyway.
                rows = self._connection.execute(final_query)
                data = list(rows)
                
                if not data:
                    st.info("Query executed successfully. No results returned.")
                else:
                    st.success(f"Query executed successfully. Returned {len(data)} rows.")
                    
                    if extended_mode:
                        # Extended Mode Rendering
                        for i, row in enumerate(data):
                            with st.container():
                                st.markdown(f"**Row {i+1}**")
                                # Create a DataFrame for the single row to display as key-value pairs
                                row_data = [{"Column": k, "Value": str(v)} for k, v in row.items()]
                                st.table(row_data)
                                st.markdown("---")
                    else:
                        # Standard Mode Rendering
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                        
            except Exception as e:
                st.error(f"Error executing query: {str(e)}")
