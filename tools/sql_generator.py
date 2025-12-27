"""
SQL Generator Module for Tahlil Platform

Converts pandas DataFrames to executable SQL scripts with support for:
- PostgreSQL, MySQL, SQLite, SQL Server, Oracle
- Smart type inference
- Batch INSERT statements
- Index and constraint generation
- ADVANCED: Foreign key detection, CHECK constraints, automatic indexes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ForeignKeyDetection:
    """Detected foreign key relationship."""
    column: str
    referenced_table: str
    referenced_column: str
    confidence: float  # 0.0 to 1.0
    reason: str


@dataclass
class CheckConstraint:
    """Detected CHECK constraint."""
    column: str
    constraint_sql: str
    constraint_type: str  # 'positive', 'email', 'range', 'enum', 'length'
    reason: str


@dataclass
class IndexSuggestion:
    """Suggested index based on data analysis."""
    columns: List[str]
    index_type: str  # 'btree', 'hash', 'unique'
    priority: str  # 'high', 'medium', 'low'
    reason: str
    cardinality_ratio: float


@dataclass
class ValidationRule:
    """Data validation rule."""
    column: str
    rule_type: str
    rule_sql: str
    description: str


class DataAnalyzer:
    """
    Analyzes DataFrame to detect patterns and suggest constraints.
    """
    
    # Common foreign key patterns
    FK_PATTERNS = [
        (r'(.+)_id$', 'id'),           # customer_id -> customers.id
        (r'^fk_(.+)$', 'id'),           # fk_customer -> customers.id
        (r'(.+)Id$', 'id'),             # customerId -> customers.id
        (r'^id_(.+)$', 'id'),           # id_customer -> customers.id
        (r'(.+)_fk$', 'id'),            # customer_fk -> customers.id
    ]
    
    # Email patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Phone patterns
    PHONE_PATTERN = re.compile(r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$')
    
    # URL patterns
    URL_PATTERN = re.compile(r'^https?://[^\s]+$')
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.column_stats = self._compute_column_stats()
    
    def _compute_column_stats(self) -> Dict[str, Dict]:
        """Compute statistics for each column."""
        stats = {}
        for col in self.df.columns:
            series = self.df[col]
            stats[col] = {
                'dtype': str(series.dtype),
                'null_count': series.isnull().sum(),
                'null_ratio': series.isnull().mean(),
                'unique_count': series.nunique(),
                'unique_ratio': series.nunique() / len(series) if len(series) > 0 else 0,
                'min': series.min() if pd.api.types.is_numeric_dtype(series) else None,
                'max': series.max() if pd.api.types.is_numeric_dtype(series) else None,
                'is_numeric': pd.api.types.is_numeric_dtype(series),
                'is_datetime': pd.api.types.is_datetime64_any_dtype(series),
            }
        return stats
    
    def detect_foreign_keys(self) -> List[ForeignKeyDetection]:
        """
        Detect potential foreign key relationships based on column naming patterns.
        """
        detected_fks = []
        
        for col in self.df.columns:
            col_lower = col.lower()
            
            for pattern, ref_col in self.FK_PATTERNS:
                match = re.match(pattern, col_lower)
                if match:
                    # Extract referenced table name
                    ref_table = match.group(1)
                    
                    # Pluralize table name (simple heuristic)
                    if not ref_table.endswith('s'):
                        ref_table_plural = ref_table + 's'
                    else:
                        ref_table_plural = ref_table
                    
                    # Check if column contains integer-like values (typical for FKs)
                    series = self.df[col].dropna()
                    is_integer_like = False
                    if len(series) > 0:
                        if pd.api.types.is_integer_dtype(series):
                            is_integer_like = True
                        elif pd.api.types.is_float_dtype(series):
                            # Check if all values are whole numbers
                            is_integer_like = (series == series.astype(int)).all()
                    
                    confidence = 0.7 if is_integer_like else 0.5
                    
                    # Higher confidence if column name is very standard
                    if col_lower.endswith('_id'):
                        confidence += 0.2
                    
                    detected_fks.append(ForeignKeyDetection(
                        column=col,
                        referenced_table=ref_table_plural,
                        referenced_column=ref_col,
                        confidence=min(confidence, 1.0),
                        reason=f"Column '{col}' matches FK pattern '{pattern}'"
                    ))
                    break  # Only match first pattern
        
        return detected_fks
    
    def detect_check_constraints(self) -> List[CheckConstraint]:
        """
        Detect potential CHECK constraints based on data patterns.
        """
        constraints = []
        
        for col in self.df.columns:
            series = self.df[col].dropna()
            col_lower = col.lower()
            stats = self.column_stats[col]
            
            # 1. Positive number constraints
            if stats['is_numeric'] and stats['min'] is not None:
                if stats['min'] >= 0:
                    # Check for typical positive-only columns
                    positive_keywords = ['age', 'price', 'amount', 'quantity', 'qty', 
                                        'count', 'salary', 'cost', 'total', 'balance',
                                        'weight', 'height', 'size', 'rating', 'score']
                    
                    if any(kw in col_lower for kw in positive_keywords) or stats['min'] >= 0:
                        constraints.append(CheckConstraint(
                            column=col,
                            constraint_sql=f"{col} >= 0",
                            constraint_type='positive',
                            reason=f"All values in '{col}' are non-negative (min: {stats['min']})"
                        ))
            
            # 2. Email validation
            if 'email' in col_lower or 'e_mail' in col_lower:
                if len(series) > 0:
                    sample_valid = series.head(100).apply(
                        lambda x: bool(self.EMAIL_PATTERN.match(str(x))) if pd.notna(x) else True
                    ).mean()
                    
                    if sample_valid > 0.8:
                        constraints.append(CheckConstraint(
                            column=col,
                            constraint_sql=f"{col} LIKE '%@%.%'",
                            constraint_type='email',
                            reason=f"Column '{col}' contains email addresses ({sample_valid*100:.0f}% valid)"
                        ))
            
            # 3. Phone number validation
            if any(kw in col_lower for kw in ['phone', 'tel', 'mobile', 'cell']):
                constraints.append(CheckConstraint(
                    column=col,
                    constraint_sql=f"LENGTH({col}) >= 7 AND LENGTH({col}) <= 20",
                    constraint_type='length',
                    reason=f"Column '{col}' appears to contain phone numbers"
                ))
            
            # 4. Age range constraints
            if col_lower in ['age', 'user_age', 'customer_age', 'person_age']:
                if stats['is_numeric']:
                    constraints.append(CheckConstraint(
                        column=col,
                        constraint_sql=f"{col} >= 0 AND {col} <= 150",
                        constraint_type='range',
                        reason=f"Column '{col}' appears to be age (valid range: 0-150)"
                    ))
            
            # 5. Percentage constraints
            if any(kw in col_lower for kw in ['percent', 'pct', 'rate', 'ratio']):
                if stats['is_numeric'] and stats['min'] is not None and stats['max'] is not None:
                    if stats['min'] >= 0 and stats['max'] <= 100:
                        constraints.append(CheckConstraint(
                            column=col,
                            constraint_sql=f"{col} >= 0 AND {col} <= 100",
                            constraint_type='range',
                            reason=f"Column '{col}' appears to be a percentage (0-100)"
                        ))
                    elif stats['min'] >= 0 and stats['max'] <= 1:
                        constraints.append(CheckConstraint(
                            column=col,
                            constraint_sql=f"{col} >= 0 AND {col} <= 1",
                            constraint_type='range',
                            reason=f"Column '{col}' appears to be a ratio (0-1)"
                        ))
            
            # 6. Enum-like constraints (few unique values)
            if stats['unique_count'] <= 10 and stats['unique_count'] > 1:
                unique_vals = series.unique()
                # Only for string or small integer enums
                if series.dtype == 'object' or (stats['is_numeric'] and stats['unique_count'] <= 5):
                    if len(unique_vals) <= 10:
                        # Format values for SQL IN clause
                        if series.dtype == 'object':
                            values_str = ", ".join([f"'{v}'" for v in unique_vals if pd.notna(v)])
                        else:
                            values_str = ", ".join([str(int(v)) for v in unique_vals if pd.notna(v)])
                        
                        constraints.append(CheckConstraint(
                            column=col,
                            constraint_sql=f"{col} IN ({values_str})",
                            constraint_type='enum',
                            reason=f"Column '{col}' has only {stats['unique_count']} unique values"
                        ))
            
            # 7. URL validation
            if any(kw in col_lower for kw in ['url', 'link', 'website', 'href']):
                constraints.append(CheckConstraint(
                    column=col,
                    constraint_sql=f"{col} LIKE 'http%'",
                    constraint_type='length',
                    reason=f"Column '{col}' appears to contain URLs"
                ))
        
        return constraints
    
    def suggest_indexes(self) -> List[IndexSuggestion]:
        """
        Suggest indexes based on data characteristics.
        """
        suggestions = []
        
        for col in self.df.columns:
            stats = self.column_stats[col]
            col_lower = col.lower()
            
            # 1. High cardinality columns (good for filtering)
            if stats['unique_ratio'] > 0.7 and stats['unique_ratio'] < 1.0:
                suggestions.append(IndexSuggestion(
                    columns=[col],
                    index_type='btree',
                    priority='high',
                    reason=f"High cardinality ({stats['unique_ratio']*100:.1f}% unique) - efficient for filtering",
                    cardinality_ratio=stats['unique_ratio']
                ))
            
            # 2. Unique columns (candidate for unique index)
            if stats['unique_ratio'] == 1.0 and stats['null_ratio'] == 0:
                suggestions.append(IndexSuggestion(
                    columns=[col],
                    index_type='unique',
                    priority='high',
                    reason=f"100% unique values with no nulls - candidate for UNIQUE constraint",
                    cardinality_ratio=1.0
                ))
            
            # 3. Date/timestamp columns (commonly queried)
            if stats['is_datetime'] or any(kw in col_lower for kw in ['date', 'time', 'created', 'updated', 'timestamp']):
                suggestions.append(IndexSuggestion(
                    columns=[col],
                    index_type='btree',
                    priority='high',
                    reason=f"Date/time column - commonly used in range queries and sorting",
                    cardinality_ratio=stats['unique_ratio']
                ))
            
            # 4. Foreign key columns (frequently joined)
            if col_lower.endswith('_id') or col_lower.startswith('fk_'):
                suggestions.append(IndexSuggestion(
                    columns=[col],
                    index_type='btree',
                    priority='high',
                    reason=f"Foreign key column - frequently used in JOINs",
                    cardinality_ratio=stats['unique_ratio']
                ))
            
            # 5. Status/type columns (enum-like, good for partial indexes)
            if stats['unique_count'] <= 20 and stats['unique_count'] > 1:
                if any(kw in col_lower for kw in ['status', 'type', 'category', 'state', 'flag']):
                    suggestions.append(IndexSuggestion(
                        columns=[col],
                        index_type='btree',
                        priority='medium',
                        reason=f"Status/category column with {stats['unique_count']} values - good for filtered queries",
                        cardinality_ratio=stats['unique_ratio']
                    ))
            
            # 6. Email columns (often queried for lookup)
            if 'email' in col_lower:
                suggestions.append(IndexSuggestion(
                    columns=[col],
                    index_type='btree',
                    priority='high',
                    reason=f"Email column - commonly used for user lookup",
                    cardinality_ratio=stats['unique_ratio']
                ))
            
            # 7. Name columns (for search)
            if any(kw in col_lower for kw in ['name', 'title', 'username']):
                suggestions.append(IndexSuggestion(
                    columns=[col],
                    index_type='btree',
                    priority='medium',
                    reason=f"Name/title column - commonly used for search",
                    cardinality_ratio=stats['unique_ratio']
                ))
        
        # Remove duplicates and sort by priority
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            key = (tuple(s.columns), s.index_type)
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(s)
        
        # Sort: high priority first
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        unique_suggestions.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return unique_suggestions
    
    def generate_validation_rules(self) -> List[ValidationRule]:
        """
        Generate data validation rules and ALTER TABLE statements.
        """
        rules = []
        
        for col in self.df.columns:
            stats = self.column_stats[col]
            col_lower = col.lower()
            
            # 1. NOT NULL constraint suggestion
            if stats['null_ratio'] == 0:
                rules.append(ValidationRule(
                    column=col,
                    rule_type='not_null',
                    rule_sql=f"ALTER TABLE {{table}} ALTER COLUMN {col} SET NOT NULL;",
                    description=f"Column '{col}' has no null values - add NOT NULL constraint"
                ))
            
            # 2. UNIQUE constraint for high uniqueness
            if stats['unique_ratio'] > 0.99 and stats['null_ratio'] == 0:
                rules.append(ValidationRule(
                    column=col,
                    rule_type='unique',
                    rule_sql=f"ALTER TABLE {{table}} ADD CONSTRAINT uq_{col} UNIQUE ({col});",
                    description=f"Column '{col}' is {stats['unique_ratio']*100:.1f}% unique - add UNIQUE constraint"
                ))
            
            # 3. Default value suggestions
            if stats['null_ratio'] > 0 and stats['null_ratio'] < 0.5:
                # Suggest most common value as default
                if not stats['is_numeric']:
                    mode_val = self.df[col].mode()
                    if len(mode_val) > 0:
                        default_val = mode_val.iloc[0]
                        if pd.notna(default_val):
                            rules.append(ValidationRule(
                                column=col,
                                rule_type='default',
                                rule_sql=f"ALTER TABLE {{table}} ALTER COLUMN {col} SET DEFAULT '{default_val}';",
                                description=f"Suggest default value '{default_val}' (most common value)"
                            ))
                else:
                    # For numeric, suggest 0 or average
                    rules.append(ValidationRule(
                        column=col,
                        rule_type='default',
                        rule_sql=f"ALTER TABLE {{table}} ALTER COLUMN {col} SET DEFAULT 0;",
                        description=f"Suggest default value 0 for numeric column"
                    ))
            
            # 4. Length constraint for strings
            if not stats['is_numeric'] and not stats['is_datetime']:
                series = self.df[col].dropna().astype(str)
                if len(series) > 0:
                    max_len = series.str.len().max()
                    if max_len < 255:
                        rules.append(ValidationRule(
                            column=col,
                            rule_type='length',
                            rule_sql=f"-- Max observed length: {max_len}. Consider VARCHAR({int(max_len * 1.5)})",
                            description=f"Maximum string length is {max_len} characters"
                        ))
        
        return rules


class SQLGenerator:
    """
    Generate SQL scripts from pandas DataFrames.
    Supports: PostgreSQL, MySQL, SQLite, SQL Server, Oracle
    """
    
    # SQL type mapping by dialect
    TYPE_MAPPINGS = {
        'postgresql': {
            'int64': 'BIGINT',
            'int32': 'INTEGER',
            'int16': 'SMALLINT',
            'float64': 'DOUBLE PRECISION',
            'float32': 'REAL',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP',
            'object': 'TEXT',
            'category': 'VARCHAR(255)',
        },
        'mysql': {
            'int64': 'BIGINT',
            'int32': 'INT',
            'int16': 'SMALLINT',
            'float64': 'DOUBLE',
            'float32': 'FLOAT',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'DATETIME',
            'object': 'TEXT',
            'category': 'VARCHAR(255)',
        },
        'sqlite': {
            'int64': 'INTEGER',
            'int32': 'INTEGER',
            'int16': 'INTEGER',
            'float64': 'REAL',
            'float32': 'REAL',
            'bool': 'INTEGER',
            'datetime64[ns]': 'TEXT',
            'object': 'TEXT',
            'category': 'TEXT',
        },
        'sqlserver': {
            'int64': 'BIGINT',
            'int32': 'INT',
            'int16': 'SMALLINT',
            'float64': 'FLOAT',
            'float32': 'REAL',
            'bool': 'BIT',
            'datetime64[ns]': 'DATETIME2',
            'object': 'NVARCHAR(MAX)',
            'category': 'NVARCHAR(255)',
        },
        'oracle': {
            'int64': 'NUMBER(19)',
            'int32': 'NUMBER(10)',
            'int16': 'NUMBER(5)',
            'float64': 'BINARY_DOUBLE',
            'float32': 'BINARY_FLOAT',
            'bool': 'NUMBER(1)',
            'datetime64[ns]': 'TIMESTAMP',
            'object': 'CLOB',
            'category': 'VARCHAR2(255)',
        }
    }
    
    def __init__(self, dialect: str = 'postgresql'):
        """
        Initialize SQL generator.
        
        Args:
            dialect: 'postgresql', 'mysql', 'sqlite', 'sqlserver', 'oracle'
        """
        if dialect not in self.TYPE_MAPPINGS:
            raise ValueError(f"Unsupported SQL dialect: {dialect}")
        
        self.dialect = dialect
        self.type_mapping = self.TYPE_MAPPINGS[dialect]
    
    def sanitize_identifier(self, name: str) -> str:
        """
        Sanitize table/column names for SQL.
        Removes special characters, handles spaces.
        """
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        # Remove special characters except underscore
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = '_' + name
        # Lowercase for consistency
        name = name.lower()
        return name or 'column'
    
    def infer_sql_type(self, series: pd.Series, column_name: str) -> str:
        """
        Infer SQL type from pandas Series with smart detection.
        """
        dtype_str = str(series.dtype)
        
        if dtype_str == 'object':
            non_null = series.dropna()
            if len(non_null) > 0:
                sample = non_null.iloc[0]
                
                if isinstance(sample, str):
                    try:
                        pd.to_datetime(sample)
                        if self.dialect == 'postgresql':
                            return 'TIMESTAMP'
                        elif self.dialect == 'mysql':
                            return 'DATETIME'
                        elif self.dialect == 'sqlite':
                            return 'TEXT'
                        elif self.dialect == 'sqlserver':
                            return 'DATETIME2'
                        elif self.dialect == 'oracle':
                            return 'TIMESTAMP'
                    except:
                        pass
                
                max_len = series.astype(str).str.len().max()
                if max_len <= 50:
                    if self.dialect in ['postgresql', 'mysql', 'oracle']:
                        return f'VARCHAR({max(int(max_len), 50)})'
                    elif self.dialect == 'sqlserver':
                        return f'NVARCHAR({max(int(max_len), 50)})'
                elif max_len <= 255:
                    if self.dialect in ['postgresql', 'mysql']:
                        return 'VARCHAR(255)'
                    elif self.dialect == 'sqlserver':
                        return 'NVARCHAR(255)'
                    elif self.dialect == 'oracle':
                        return 'VARCHAR2(255)'
        
        if dtype_str in self.type_mapping:
            return self.type_mapping[dtype_str]
        
        if self.dialect == 'postgresql':
            return 'TEXT'
        elif self.dialect == 'mysql':
            return 'TEXT'
        elif self.dialect == 'sqlite':
            return 'TEXT'
        elif self.dialect == 'sqlserver':
            return 'NVARCHAR(MAX)'
        elif self.dialect == 'oracle':
            return 'CLOB'
    
    def generate_create_database(self, database_name: str) -> str:
        """Generate CREATE DATABASE statement."""
        db_name = self.sanitize_identifier(database_name)
        
        if self.dialect == 'postgresql':
            return f"CREATE DATABASE {db_name};\n"
        elif self.dialect == 'mysql':
            return f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
        elif self.dialect == 'sqlite':
            return f"-- SQLite database will be created when saving to file: {db_name}.db\n"
        elif self.dialect == 'sqlserver':
            return f"CREATE DATABASE [{db_name}];\nGO\n"
        elif self.dialect == 'oracle':
            return f"-- Oracle database creation requires DBA privileges\n-- CREATE DATABASE {db_name};\n"
    
    def generate_create_schema(self, schema_name: str) -> str:
        """Generate CREATE SCHEMA statement (if supported)."""
        schema = self.sanitize_identifier(schema_name)
        
        if self.dialect == 'postgresql':
            return f"CREATE SCHEMA IF NOT EXISTS {schema};\n"
        elif self.dialect == 'mysql':
            return ""
        elif self.dialect == 'sqlite':
            return ""
        elif self.dialect == 'sqlserver':
            return f"CREATE SCHEMA [{schema}];\nGO\n"
        elif self.dialect == 'oracle':
            return f"-- CREATE SCHEMA AUTHORIZATION {schema};\n"
    
    def generate_check_constraints_sql(self, constraints: List[CheckConstraint], table_name: str) -> str:
        """Generate CHECK constraint statements."""
        if not constraints:
            return ""
        
        table = self.sanitize_identifier(table_name)
        lines = ["\n-- CHECK Constraints (auto-detected)"]
        
        for i, c in enumerate(constraints):
            col = self.sanitize_identifier(c.column)
            constraint_name = f"chk_{table}_{col}_{i}"
            
            if self.dialect in ['postgresql', 'mysql', 'oracle']:
                lines.append(f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} CHECK ({c.constraint_sql});")
                lines.append(f"-- Reason: {c.reason}")
            elif self.dialect == 'sqlserver':
                lines.append(f"ALTER TABLE [{table}] ADD CONSTRAINT {constraint_name} CHECK ({c.constraint_sql});")
                lines.append(f"-- Reason: {c.reason}")
            elif self.dialect == 'sqlite':
                lines.append(f"-- SQLite CHECK: {c.constraint_sql}")
                lines.append(f"-- Reason: {c.reason}")
        
        return "\n".join(lines) + "\n"
    
    def generate_foreign_keys_sql(self, foreign_keys: List[ForeignKeyDetection], table_name: str) -> str:
        """Generate FOREIGN KEY constraint statements."""
        if not foreign_keys:
            return ""
        
        table = self.sanitize_identifier(table_name)
        lines = ["\n-- Foreign Key Constraints (auto-detected)"]
        lines.append("-- NOTE: Uncomment after creating referenced tables")
        
        for fk in foreign_keys:
            col = self.sanitize_identifier(fk.column)
            ref_table = self.sanitize_identifier(fk.referenced_table)
            ref_col = fk.referenced_column
            fk_name = f"fk_{table}_{col}"
            
            if self.dialect in ['postgresql', 'mysql', 'oracle']:
                lines.append(f"-- ALTER TABLE {table} ADD CONSTRAINT {fk_name}")
                lines.append(f"--     FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col});")
                lines.append(f"-- Confidence: {fk.confidence*100:.0f}% | {fk.reason}")
            elif self.dialect == 'sqlserver':
                lines.append(f"-- ALTER TABLE [{table}] ADD CONSTRAINT {fk_name}")
                lines.append(f"--     FOREIGN KEY ({col}) REFERENCES [{ref_table}]({ref_col});")
                lines.append(f"-- Confidence: {fk.confidence*100:.0f}% | {fk.reason}")
            elif self.dialect == 'sqlite':
                lines.append(f"-- FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})")
                lines.append(f"-- Confidence: {fk.confidence*100:.0f}% | {fk.reason}")
        
        return "\n".join(lines) + "\n"
    
    def generate_suggested_indexes_sql(self, suggestions: List[IndexSuggestion], table_name: str) -> str:
        """Generate suggested INDEX statements."""
        if not suggestions:
            return ""
        
        table = self.sanitize_identifier(table_name)
        lines = ["\n-- Suggested Indexes (auto-detected)"]
        
        for s in suggestions:
            cols = [self.sanitize_identifier(c) for c in s.columns]
            cols_str = ", ".join(cols)
            idx_name = f"idx_{table}_{'_'.join(cols)}"
            
            if s.index_type == 'unique':
                if self.dialect in ['postgresql', 'mysql', 'sqlite']:
                    lines.append(f"CREATE UNIQUE INDEX {idx_name} ON {table} ({cols_str});")
                elif self.dialect == 'sqlserver':
                    lines.append(f"CREATE UNIQUE INDEX {idx_name} ON [{table}] ({cols_str});")
                elif self.dialect == 'oracle':
                    lines.append(f"CREATE UNIQUE INDEX {idx_name} ON {table} ({cols_str});")
            else:
                if self.dialect in ['postgresql', 'mysql', 'sqlite']:
                    lines.append(f"CREATE INDEX {idx_name} ON {table} ({cols_str});")
                elif self.dialect == 'sqlserver':
                    lines.append(f"CREATE INDEX {idx_name} ON [{table}] ({cols_str});")
                elif self.dialect == 'oracle':
                    lines.append(f"CREATE INDEX {idx_name} ON {table} ({cols_str});")
            
            lines.append(f"-- Priority: {s.priority.upper()} | {s.reason}")
        
        return "\n".join(lines) + "\n"
    
    def generate_validation_rules_sql(self, rules: List[ValidationRule], table_name: str) -> str:
        """Generate validation rules as SQL comments/statements."""
        if not rules:
            return ""
        
        table = self.sanitize_identifier(table_name)
        lines = ["\n-- Data Validation Rules (recommendations)"]
        
        for r in rules:
            sql = r.rule_sql.replace('{table}', table)
            lines.append(f"-- {r.description}")
            if r.rule_type in ['not_null', 'unique', 'default']:
                lines.append(f"-- {sql}")
            else:
                lines.append(f"-- {sql}")
        
        return "\n".join(lines) + "\n"
    
    def generate_create_table(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema_name: Optional[str] = None,
        primary_key: Optional[str] = None,
        indexes: Optional[List[str]] = None
    ) -> str:
        """Generate CREATE TABLE statement."""
        table = self.sanitize_identifier(table_name)
        full_table_name = table
        
        if schema_name and self.dialect in ['postgresql', 'sqlserver', 'oracle']:
            schema = self.sanitize_identifier(schema_name)
            if self.dialect == 'sqlserver':
                full_table_name = f"[{schema}].[{table}]"
            else:
                full_table_name = f"{schema}.{table}"
        
        columns = []
        for col_name in df.columns:
            sanitized_col = self.sanitize_identifier(col_name)
            sql_type = self.infer_sql_type(df[col_name], col_name)
            
            has_nulls = df[col_name].isnull().any()
            null_constraint = "" if has_nulls else " NOT NULL"
            
            pk_constraint = ""
            if primary_key and sanitized_col == self.sanitize_identifier(primary_key):
                pk_constraint = " PRIMARY KEY"
            
            column_def = f"    {sanitized_col} {sql_type}{pk_constraint}{null_constraint}"
            columns.append(column_def)
        
        if self.dialect == 'postgresql':
            sql = f"CREATE TABLE IF NOT EXISTS {full_table_name} (\n"
        elif self.dialect == 'mysql':
            sql = f"CREATE TABLE IF NOT EXISTS {full_table_name} (\n"
        elif self.dialect == 'sqlite':
            sql = f"CREATE TABLE IF NOT EXISTS {full_table_name} (\n"
        elif self.dialect == 'sqlserver':
            sql = f"IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{table}')\n"
            sql += f"CREATE TABLE {full_table_name} (\n"
        elif self.dialect == 'oracle':
            sql = f"CREATE TABLE {full_table_name} (\n"
        
        sql += ",\n".join(columns)
        sql += "\n);\n"
        
        if indexes:
            for idx_col in indexes:
                sanitized_idx_col = self.sanitize_identifier(idx_col)
                idx_name = f"idx_{table}_{sanitized_idx_col}"
                sql += f"\nCREATE INDEX {idx_name} ON {full_table_name} ({sanitized_idx_col});\n"
        
        return sql
    
    def generate_insert_statements(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema_name: Optional[str] = None,
        batch_size: int = 100
    ) -> str:
        """Generate INSERT statements for data."""
        table = self.sanitize_identifier(table_name)
        full_table_name = table
        
        if schema_name and self.dialect in ['postgresql', 'sqlserver', 'oracle']:
            schema = self.sanitize_identifier(schema_name)
            if self.dialect == 'sqlserver':
                full_table_name = f"[{schema}].[{table}]"
            else:
                full_table_name = f"{schema}.{table}"
        
        sanitized_columns = [self.sanitize_identifier(col) for col in df.columns]
        sql = ""
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            if self.dialect in ['postgresql', 'sqlite']:
                sql += f"INSERT INTO {full_table_name} ({', '.join(sanitized_columns)}) VALUES\n"
            elif self.dialect == 'mysql':
                sql += f"INSERT INTO {full_table_name} ({', '.join(sanitized_columns)}) VALUES\n"
            elif self.dialect == 'sqlserver':
                sql += f"INSERT INTO {full_table_name} ({', '.join(sanitized_columns)}) VALUES\n"
            elif self.dialect == 'oracle':
                sql += f"INSERT ALL\n"
            
            value_rows = []
            for _, row in batch.iterrows():
                values = []
                for val in row:
                    if pd.isna(val):
                        values.append('NULL')
                    elif isinstance(val, (int, float, np.integer, np.floating)):
                        if pd.isna(val):
                            values.append('NULL')
                        else:
                            values.append(str(val))
                    elif isinstance(val, bool):
                        if self.dialect == 'postgresql':
                            values.append('TRUE' if val else 'FALSE')
                        else:
                            values.append('1' if val else '0')
                    elif isinstance(val, (datetime, date)):
                        values.append(f"'{val}'")
                    else:
                        escaped = str(val).replace("'", "''")
                        values.append(f"'{escaped}'")
                
                if self.dialect == 'oracle':
                    value_rows.append(f"    INTO {full_table_name} ({', '.join(sanitized_columns)}) VALUES ({', '.join(values)})")
                else:
                    value_rows.append(f"    ({', '.join(values)})")
            
            if self.dialect == 'oracle':
                sql += "\n".join(value_rows)
                sql += "\nSELECT 1 FROM DUAL;\n\n"
            else:
                sql += ",\n".join(value_rows)
                sql += ";\n\n"
        
        return sql
    
    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze DataFrame and return all detected patterns.
        
        Returns dict with:
        - foreign_keys: List[ForeignKeyDetection]
        - check_constraints: List[CheckConstraint]
        - index_suggestions: List[IndexSuggestion]
        - validation_rules: List[ValidationRule]
        """
        analyzer = DataAnalyzer(df)
        
        return {
            'foreign_keys': analyzer.detect_foreign_keys(),
            'check_constraints': analyzer.detect_check_constraints(),
            'index_suggestions': analyzer.suggest_indexes(),
            'validation_rules': analyzer.generate_validation_rules()
        }
    
    def generate_full_script(
        self,
        df: pd.DataFrame,
        database_name: str,
        table_name: str,
        schema_name: Optional[str] = None,
        primary_key: Optional[str] = None,
        indexes: Optional[List[str]] = None,
        include_database: bool = True,
        include_schema: bool = False,
        batch_size: int = 100,
        include_advanced_features: bool = False
    ) -> str:
        """
        Generate complete SQL script.
        
        Args:
            df: pandas DataFrame with data
            database_name: Database name
            table_name: Table name
            schema_name: Optional schema name
            primary_key: Column to use as primary key
            indexes: Columns to index
            include_database: Include CREATE DATABASE
            include_schema: Include CREATE SCHEMA
            batch_size: Rows per INSERT statement
            include_advanced_features: Include auto-detected FK, CHECK, indexes
            
        Returns:
            Complete SQL script as string
        """
        script = []
        
        # Header comment
        script.append(f"-- SQL Script Generated by Tahlil Platform")
        script.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        script.append(f"-- Dialect: {self.dialect.upper()}")
        script.append(f"-- Rows: {len(df)}")
        script.append(f"-- Columns: {len(df.columns)}")
        if include_advanced_features:
            script.append(f"-- Advanced Features: ENABLED")
        script.append(f"--\n")
        
        # Create database
        if include_database:
            script.append("-- Create Database")
            script.append(self.generate_create_database(database_name))
            
            if self.dialect in ['postgresql', 'mysql']:
                script.append(f"\\c {self.sanitize_identifier(database_name)}\n" if self.dialect == 'postgresql' else f"USE {self.sanitize_identifier(database_name)};\n")
            elif self.dialect == 'sqlserver':
                script.append(f"USE [{self.sanitize_identifier(database_name)}];")
                script.append("GO\n")
            
            script.append("")
        
        # Create schema
        if include_schema and schema_name:
            schema_sql = self.generate_create_schema(schema_name)
            if schema_sql:
                script.append("-- Create Schema")
                script.append(schema_sql)
                script.append("")
        
        # Create table
        script.append("-- Create Table")
        script.append(self.generate_create_table(
            df, table_name, schema_name, primary_key, indexes
        ))
        script.append("")
        
        # Advanced features
        if include_advanced_features:
            analysis = self.analyze_data(df)
            
            # Add CHECK constraints
            if analysis['check_constraints']:
                script.append(self.generate_check_constraints_sql(
                    analysis['check_constraints'], table_name
                ))
            
            # Add suggested indexes
            if analysis['index_suggestions']:
                script.append(self.generate_suggested_indexes_sql(
                    analysis['index_suggestions'], table_name
                ))
            
            # Add foreign key suggestions (commented out)
            if analysis['foreign_keys']:
                script.append(self.generate_foreign_keys_sql(
                    analysis['foreign_keys'], table_name
                ))
            
            # Add validation rules
            if analysis['validation_rules']:
                script.append(self.generate_validation_rules_sql(
                    analysis['validation_rules'], table_name
                ))
        
        # Insert data
        script.append(f"-- Insert Data ({len(df)} rows)")
        script.append(self.generate_insert_statements(
            df, table_name, schema_name, batch_size
        ))
        
        # Footer
        script.append(f"\n-- Script generation complete")
        script.append(f"-- Total INSERT statements: {(len(df) // batch_size) + 1}")
        
        return "\n".join(script)


def dataframe_to_sql(
    df: pd.DataFrame,
    database_name: str = "tahlil_db",
    table_name: str = "data_table",
    dialect: str = "postgresql",
    include_advanced_features: bool = False,
    **kwargs
) -> str:
    """
    Convenience function to convert DataFrame to SQL script.
    
    Args:
        df: pandas DataFrame
        database_name: Name for database
        table_name: Name for table
        dialect: SQL dialect
        include_advanced_features: Include auto-detected constraints and indexes
        **kwargs: Additional options for SQLGenerator
        
    Returns:
        Complete SQL script as string
    """
    generator = SQLGenerator(dialect=dialect)
    return generator.generate_full_script(
        df, database_name, table_name, 
        include_advanced_features=include_advanced_features,
        **kwargs
    )
