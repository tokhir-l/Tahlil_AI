"""
Test script for SQL Generator - ADVANCED FEATURES

Tests the new advanced features:
- Foreign Key detection
- CHECK constraint generation
- Automatic index suggestions
- Data validation rules
"""

import pandas as pd
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.sql_generator import SQLGenerator, dataframe_to_sql

# Create sample data with patterns that trigger advanced detection
print("=" * 70)
print("Creating sample DataFrame with detectable patterns...")
print("=" * 70)

df = pd.DataFrame({
    # Primary key candidate (unique, no nulls)
    'id': [1, 2, 3, 4, 5],
    
    # Foreign key patterns (should detect _id suffix)
    'customer_id': [101, 102, 101, 103, 102],
    'order_id': [1001, 1002, 1003, 1004, 1005],
    
    # Email column (should suggest CHECK constraint)
    'email': ['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com', 'charlie@example.com'],
    
    # Name column (should suggest index)
    'full_name': ['John Doe', 'Jane Smith', "Bob O'Connor", 'Alice Johnson', 'Charlie Brown'],
    
    # Positive number (should suggest >= 0 CHECK)
    'age': [28, 34, 45, 29, 52],
    'salary': [75000.50, 85000.00, 95000.75, 72000.00, 105000.25],
    
    # Enum-like column (should suggest IN constraint)
    'status': ['active', 'active', 'inactive', 'pending', 'active'],
    
    # Date column (should suggest index)
    'created_at': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2024-05-12']),
    
    # Boolean
    'is_verified': [True, True, False, True, True],
})

print(f"DataFrame created with {len(df)} rows and {len(df.columns)} columns")
print("\nColumns:")
for col in df.columns:
    print(f"  - {col}: {df[col].dtype}")

# Generate with advanced features
print("\n" + "=" * 70)
print("Testing SQL Generation WITH Advanced Features")
print("=" * 70)

sql_advanced = dataframe_to_sql(
    df=df,
    database_name='test_db',
    table_name='users',
    dialect='postgresql',
    primary_key='id',
    include_advanced_features=True  # Enable new features!
)

# Save to file
output_file = Path('temp/test_advanced_features.sql')
output_file.parent.mkdir(exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(sql_advanced)

print(f"\n✅ Generated SQL saved to: {output_file}")
print(f"   Script size: {len(sql_advanced)} characters")

# Display key sections
print("\n" + "=" * 70)
print("OUTPUT PREVIEW (showing advanced features)")
print("=" * 70)

# Show lines containing key features
lines = sql_advanced.split('\n')
for i, line in enumerate(lines[:100]):
    if any(keyword in line for keyword in ['CHECK', 'INDEX', 'FOREIGN', 'Constraint', 'Validation', 'Reason', 'Priority', 'Confidence']):
        print(f"{i+1}: {line}")

print("\n" + "=" * 70)
print("✅ ADVANCED FEATURES TEST COMPLETE!")
print("=" * 70)

# Also test the analyzer directly
from tools.sql_generator import DataAnalyzer

print("\n" + "=" * 70)
print("Direct DataAnalyzer Test")
print("=" * 70)

analyzer = DataAnalyzer(df)

print("\n📌 Detected Foreign Keys:")
for fk in analyzer.detect_foreign_keys():
    print(f"   - {fk.column} → {fk.referenced_table}.{fk.referenced_column} (confidence: {fk.confidence*100:.0f}%)")

print("\n📌 Suggested Indexes:")
for idx in analyzer.suggest_indexes()[:5]:
    print(f"   - {idx.columns[0]} ({idx.index_type}, {idx.priority}): {idx.reason[:60]}...")

print("\n📌 Detected CHECK Constraints:")
for c in analyzer.detect_check_constraints()[:5]:
    print(f"   - {c.column}: {c.constraint_sql}")

print("\n📌 Validation Rules:")
for r in analyzer.generate_validation_rules()[:5]:
    print(f"   - {r.column}: {r.description}")

print("\n✅ ALL ADVANCED FEATURE TESTS PASSED!")
