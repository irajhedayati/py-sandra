"""
Schema Introspection Module

Discovers keyspaces, tables, and column metadata from Cassandra.
Provides structured information about table schemas including
partition keys, clustering keys, and column types.
"""

from dataclasses import dataclass, field
from cassandra.cluster import Session


@dataclass
class ColumnInfo:
    """Information about a single column."""
    name: str
    cql_type: str
    is_partition_key: bool = False
    is_clustering_key: bool = False
    clustering_order: str = "ASC"
    position: int = 0

    @property
    def is_primary_key(self) -> bool:
        """Check if column is part of primary key."""
        return self.is_partition_key or self.is_clustering_key


@dataclass
class TableSchema:
    """Complete schema information for a table."""
    keyspace: str
    table_name: str
    columns: list[ColumnInfo] = field(default_factory=list)

    def column(self, name: str) -> ColumnInfo | None:
        for c in self.columns:
            if c.name == name:
                return c
        return None

    @property
    def partition_keys(self) -> list[ColumnInfo]:
        """Get partition key columns in order."""
        return sorted(
            [c for c in self.columns if c.is_partition_key],
            key=lambda c: c.position
        )

    @property
    def clustering_keys(self) -> list[ColumnInfo]:
        """Get clustering key columns in order."""
        return sorted(
            [c for c in self.columns if c.is_clustering_key],
            key=lambda c: c.position
        )

    @property
    def primary_key_columns(self) -> list[ColumnInfo]:
        """Get all primary key columns (partition + clustering)."""
        return self.partition_keys + self.clustering_keys

    @property
    def regular_columns(self) -> list[ColumnInfo]:
        """Get non-primary-key columns."""
        return [c for c in self.columns if not c.is_primary_key]

    @property
    def all_columns_sorted(self) -> list[ColumnInfo]:
        """Get all columns with primary keys first."""
        return self.primary_key_columns + self.regular_columns


# noinspection SqlNoDataSourceInspection
class SchemaInspector:
    """
    Inspects Cassandra schema metadata.

    Uses system tables to discover keyspaces, tables, and column
    information dynamically. All schema information is fetched
    at runtime to handle schema changes gracefully.
    """

    def __init__(self, session: Session):
        """
        Initialize schema inspector.

        Args:
            session: Active Cassandra session.
        """
        self._session = session

    def get_keyspaces(self) -> list[str]:
        """
        Get list of all keyspaces.

        Returns:
            List of keyspace names, excluding system keyspaces.
        """
        query = """
            SELECT keyspace_name 
            FROM system_schema.keyspaces
        """
        rows = self._session.execute(query)

        # Filter out system keyspaces
        system_keyspaces = {
            'system', 'system_auth', 'system_schema',
            'system_distributed', 'system_traces', 'system_views',
            'system_virtual_schema'
        }

        return sorted([
            row['keyspace_name']
            for row in rows
            if row['keyspace_name'] not in system_keyspaces
        ])

    def get_tables(self, keyspace: str) -> list[str]:
        """
        Get list of tables in a keyspace.

        Args:
            keyspace: Name of the keyspace.

        Returns:
            List of table names.
        """
        query = """
            SELECT table_name 
            FROM system_schema.tables 
            WHERE keyspace_name = %s
        """
        rows = self._session.execute(query, (keyspace,))
        return sorted([row['table_name'] for row in rows])

    def get_table_schema(self, keyspace: str, table: str) -> TableSchema:
        """
        Get complete schema information for a table.

        This method queries system_schema.columns to get all column
        information including types, and determines partition/clustering
        keys from the column kind field.

        Args:
            keyspace: Name of the keyspace.
            table: Name of the table.

        Returns:
            TableSchema with complete column information.
        """
        # Query column information from system schema
        query = """
            SELECT column_name, type, kind, position, clustering_order
            FROM system_schema.columns
            WHERE keyspace_name = %s AND table_name = %s
        """
        rows = self._session.execute(query, (keyspace, table))

        columns = []
        for row in rows:
            # Determine column role from 'kind' field
            # kind can be: partition_key, clustering, regular, static
            is_partition = row['kind'] == 'partition_key'
            is_clustering = row['kind'] == 'clustering'

            column = ColumnInfo(
                name=row['column_name'],
                cql_type=row['type'],
                is_partition_key=is_partition,
                is_clustering_key=is_clustering,
                clustering_order=row.get('clustering_order', 'ASC') or 'ASC',
                position=row['position']
            )
            columns.append(column)

        return TableSchema(
            keyspace=keyspace,
            table_name=table,
            columns=columns
        )

    def get_row_count_estimate(self, keyspace: str, table: str) -> int:
        """
        Get estimated row count for a table.

        Note: This is an estimate and may not be accurate for large tables.

        Args:
            keyspace: Name of the keyspace.
            table: Name of the table.

        Returns:
            Estimated row count.
        """
        try:
            # This query can be slow on large tables
            query = f"SELECT COUNT(*) as count FROM {keyspace}.{table} LIMIT 10000"
            result = self._session.execute(query)
            row = result.one()
            return row['count'] if row else 0
        except Exception:
            return -1  # Unknown