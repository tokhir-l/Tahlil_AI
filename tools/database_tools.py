"""
Database Tools for Tahlil Platform.
Provides integration with SQL databases via SQLAlchemy.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class SQLDatabaseProvider(ToolProvider):
    """
    Integration with SQL databases using SQLAlchemy.
    Supports PostgreSQL, MySQL, SQLite, and more.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._engine = None
        self._connections: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        return "sql_database"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DATABASE
    
    @property
    def description(self) -> str:
        return "SQL database connectivity for PostgreSQL, MySQL, SQLite, and more"
    
    @property
    def dependencies(self) -> List[str]:
        return ["sqlalchemy", "pandas"]
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "query_execution",
            "data_import",
            "data_export",
            "table_creation",
            "schema_inspection"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install sqlalchemy if needed
            from .dependency_manager import check_and_install
            success, _ = check_and_install('sqlalchemy', 'sqlalchemy')
            if not success:
                return False
            
            import sqlalchemy
            import pandas
            return True
        except ImportError:
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            from sqlalchemy import create_engine, inspect
            self._create_engine = create_engine
            self._inspect = inspect
            return ToolResult(success=True)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a database operation."""
        operations = {
            'connect': self._connect,
            'query': self._query,
            'execute': self._execute_sql,
            'import_csv': self._import_csv,
            'export_csv': self._export_csv,
            'list_tables': self._list_tables,
            'describe_table': self._describe_table,
            'disconnect': self._disconnect,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"Database {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _connect(self, connection_string: str, name: str = 'default', **kwargs) -> ToolResult:
        """Connect to a database."""
        try:
            engine = self._create_engine(connection_string, **kwargs)
            # Test connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            
            self._connections[name] = engine
            
            return ToolResult(
                success=True,
                data={'connection_name': name},
                metadata={'database_url': connection_string.split('@')[-1] if '@' in connection_string else connection_string}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Connection failed: {str(e)}")
    
    def _get_connection(self, name: str = 'default'):
        """Get an existing connection."""
        if name not in self._connections:
            raise ValueError(f"No connection named '{name}'. Call connect first.")
        return self._connections[name]
    
    def _query(self, sql: str, connection: str = 'default', params: Dict = None, **kwargs) -> ToolResult:
        """Execute a SELECT query and return results as DataFrame."""
        import pandas as pd
        from sqlalchemy import text
        
        engine = self._get_connection(connection)
        
        df = pd.read_sql(text(sql), engine, params=params)
        
        return ToolResult(
            success=True,
            data={
                'records': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'row_count': len(df)
            },
            metadata={'query': sql}
        )
    
    def _execute_sql(self, sql: str, connection: str = 'default', params: Dict = None, **kwargs) -> ToolResult:
        """Execute any SQL statement."""
        from sqlalchemy import text
        
        engine = self._get_connection(connection)
        
        with engine.begin() as conn:
            result = conn.execute(text(sql), params or {})
            rowcount = result.rowcount
        
        return ToolResult(
            success=True,
            data={'rows_affected': rowcount},
            metadata={'query': sql}
        )
    
    def _import_csv(self, filepath: str, table_name: str, connection: str = 'default', 
                    if_exists: str = 'replace', **kwargs) -> ToolResult:
        """Import CSV data into a database table."""
        import pandas as pd
        
        engine = self._get_connection(connection)
        
        df = pd.read_csv(filepath, **kwargs)
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        
        return ToolResult(
            success=True,
            data={
                'table_name': table_name,
                'rows_imported': len(df),
                'columns': df.columns.tolist()
            }
        )
    
    def _export_csv(self, sql: str, filepath: str, connection: str = 'default', **kwargs) -> ToolResult:
        """Export query results to CSV."""
        import pandas as pd
        from sqlalchemy import text
        
        engine = self._get_connection(connection)
        
        df = pd.read_sql(text(sql), engine)
        df.to_csv(filepath, index=False, **kwargs)
        
        return ToolResult(
            success=True,
            data={
                'filepath': filepath,
                'rows_exported': len(df)
            }
        )
    
    def _list_tables(self, connection: str = 'default', **kwargs) -> ToolResult:
        """List all tables in the database."""
        engine = self._get_connection(connection)
        inspector = self._inspect(engine)
        
        tables = inspector.get_table_names()
        views = inspector.get_view_names()
        
        return ToolResult(
            success=True,
            data={
                'tables': tables,
                'views': views
            }
        )
    
    def _describe_table(self, table_name: str, connection: str = 'default', **kwargs) -> ToolResult:
        """Get table schema information."""
        engine = self._get_connection(connection)
        inspector = self._inspect(engine)
        
        columns = inspector.get_columns(table_name)
        pk = inspector.get_pk_constraint(table_name)
        fks = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        
        return ToolResult(
            success=True,
            data={
                'table_name': table_name,
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col.get('nullable', True)
                    }
                    for col in columns
                ],
                'primary_key': pk,
                'foreign_keys': fks,
                'indexes': indexes
            }
        )
    
    def _disconnect(self, connection: str = 'default', **kwargs) -> ToolResult:
        """Disconnect from a database."""
        if connection in self._connections:
            self._connections[connection].dispose()
            del self._connections[connection]
            return ToolResult(success=True, data={'disconnected': connection})
        return ToolResult(success=False, error=f"No connection named '{connection}'")
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for database operations."""
        code_templates = {
            'connect': '''
from sqlalchemy import create_engine
import pandas as pd

# Database connection string
# PostgreSQL: postgresql://user:password@host:port/database
# MySQL: mysql+pymysql://user:password@host:port/database
# SQLite: sqlite:///path/to/database.db

connection_string = "{connection_string}"
engine = create_engine(connection_string)

# Test connection
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print("Connection successful!")
''',
            'query': '''
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("{connection_string}")

# Execute query and load into DataFrame
query = """
{sql}
"""

df = pd.read_sql(text(query), engine)
print(f"Retrieved {{len(df)}} rows")
print(df.head())
''',
            'import_csv': '''
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("{connection_string}")

# Read CSV and import to database
df = pd.read_csv("{filepath}")
df.to_sql("{table_name}", engine, if_exists="replace", index=False)

print(f"Imported {{len(df)}} rows to {table_name}")
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'connect',
                'description': 'Connect to a SQL database',
                'params': ['connection_string', 'name']
            },
            {
                'name': 'query',
                'description': 'Execute SELECT query',
                'params': ['sql', 'connection', 'params']
            },
            {
                'name': 'execute',
                'description': 'Execute any SQL statement',
                'params': ['sql', 'connection', 'params']
            },
            {
                'name': 'import_csv',
                'description': 'Import CSV into table',
                'params': ['filepath', 'table_name', 'connection']
            },
            {
                'name': 'export_csv',
                'description': 'Export query to CSV',
                'params': ['sql', 'filepath', 'connection']
            },
            {
                'name': 'list_tables',
                'description': 'List database tables',
                'params': ['connection']
            },
            {
                'name': 'describe_table',
                'description': 'Get table schema',
                'params': ['table_name', 'connection']
            },
            {
                'name': 'disconnect',
                'description': 'Close database connection',
                'params': ['connection']
            }
        ]
