"""
Test script for SQL Generator

Run this to verify the SQL generator works correctly.
"""

import pandas as pd
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.sql_generator import SQLGenerator, dataframe_to_sql

# Create sample data
print("Creating sample DataFrame...")
df = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'name': ['John Doe', 'Jane Smith', "Bob O'Connor", 'Alice Johnson', 'Charlie Brown'],
    'email': ['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com', 'charlie@example.com'],
    'age': [28, 34, 45, 29, 52],
    'salary': [75000.50, 85000.00, 95000.75, 72000.00, 105000.25],
    'is_active': [True, True, False, True, True],
    'created_at': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2024-05-12'])
})

print(f"DataFrame created with {len(df)} rows and {len(df.columns)} columns")
print("\nData preview:")
print(df)

# Test PostgreSQL
print("\n" + "="*70)
print("Testing PostgreSQL SQL Generation")
print("="*70)

generator_pg = SQLGenerator(dialect='postgresql')
sql_pg = generator_pg.generate_full_script(
    df=df,
    database_name='test_db',
    table_name='employees',
    primary_key='id',
    indexes=['email'],
    batch_size=3  # Small batch for testing
)

print("\nPostgreSQL Script (first 1000 chars):")
print(sql_pg[:1000])
print("...")
print(f"\nTotal script length: {len(sql_pg)} characters")

# Save to file
output_file = Path('temp/test_employees_postgresql.sql')
output_file.parent.mkdir(exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(sql_pg)
print(f"✅ Saved to: {output_file}")

# Test MySQL
print("\n" + "="*70)
print("Testing MySQL SQL Generation")
print("="*70)

sql_mysql = dataframe_to_sql(
    df=df,
    database_name='test_db',
    table_name='employees',
    dialect='mysql'
)

mysql_file = Path('temp/test_employees_mysql.sql')
with open(mysql_file, 'w', encoding='utf-8') as f:
    f.write(sql_mysql)
print(f"✅ Saved to: {mysql_file}")

# Test SQLite
print("\n" + "="*70)
print("Testing SQLite SQL Generation")
print("="*70)

sql_sqlite = dataframe_to_sql(
    df=df,
    database_name='test_db',
    table_name='employees',
    dialect='sqlite'
)

sqlite_file = Path('temp/test_employees_sqlite.sql')
with open(sqlite_file, 'w', encoding='utf-8') as f:
    f.write(sql_sqlite)
print(f"✅ Saved to: {sqlite_file}")

print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print("\nGenerated SQL files:")
print(f"  - {output_file}")
print(f"  - {mysql_file}")
print(f"  - {sqlite_file}")
print("\nYou can now review these files and test executing them in your database.")
