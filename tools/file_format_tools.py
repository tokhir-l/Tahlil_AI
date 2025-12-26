"""
File Format Support Tools for Tahlil Platform.
Provides support for SPSS (.sav) and Stata (.dta) file formats.
Note: Limited to data import only, not native analysis capabilities.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class SPSSStataProvider(ToolProvider):
    """
    Integration for reading SPSS and Stata file formats.
    Limited to data import - no native analysis capabilities.
    """
    
    @property
    def name(self) -> str:
        return "spss_stata"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DATA_SOURCE
    
    @property
    def description(self) -> str:
        return "SPSS and Stata file format support (read-only, data import)"
    
    @property
    def dependencies(self) -> List[str]:
        return ["pandas", "pyreadstat"]  # pyreadstat for .sav and .dta files
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "read_spss",
            "read_stata",
            "get_metadata",
            "convert_to_csv"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install pyreadstat if needed
            from .dependency_manager import check_and_install
            success, _ = check_and_install('pyreadstat', 'pyreadstat')
            return success
        except ImportError:
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            import pyreadstat
            return ToolResult(success=True, metadata={'version': pyreadstat.__version__})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a file format operation."""
        operations = {
            'read_spss': self._read_spss,
            'read_stata': self._read_stata,
            'get_metadata': self._get_metadata,
            'convert_to_csv': self._convert_to_csv,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"File format {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _read_spss(self, filepath: str, **kwargs) -> ToolResult:
        """Read SPSS .sav file."""
        import pandas as pd
        import pyreadstat
        
        try:
            df, meta = pyreadstat.read_sav(filepath, **kwargs)
            
            return ToolResult(
                success=True,
                data={
                    'records': df.to_dict('records'),
                    'columns': df.columns.tolist(),
                    'row_count': len(df),
                    'metadata': {
                        'variable_labels': meta.column_labels,
                        'value_labels': meta.variable_value_labels,
                        'file_label': meta.file_label
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _read_stata(self, filepath: str, **kwargs) -> ToolResult:
        """Read Stata .dta file."""
        import pandas as pd
        import pyreadstat
        
        try:
            df, meta = pyreadstat.read_dta(filepath, **kwargs)
            
            return ToolResult(
                success=True,
                data={
                    'records': df.to_dict('records'),
                    'columns': df.columns.tolist(),
                    'row_count': len(df),
                    'metadata': {
                        'variable_labels': meta.column_labels,
                        'value_labels': meta.variable_value_labels
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _get_metadata(self, filepath: str, **kwargs) -> ToolResult:
        """Get metadata from SPSS/Stata file."""
        import pyreadstat
        from pathlib import Path
        
        try:
            file_ext = Path(filepath).suffix.lower()
            
            if file_ext == '.sav':
                _, meta = pyreadstat.read_sav(filepath, metadataonly=True)
            elif file_ext == '.dta':
                _, meta = pyreadstat.read_dta(filepath, metadataonly=True)
            else:
                return ToolResult(success=False, error=f"Unsupported file format: {file_ext}")
            
            return ToolResult(
                success=True,
                data={
                    'filepath': filepath,
                    'variable_count': meta.number_columns,
                    'variable_names': meta.column_names,
                    'variable_labels': meta.column_labels,
                    'value_labels': meta.variable_value_labels,
                    'file_label': getattr(meta, 'file_label', None)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _convert_to_csv(self, filepath: str, output_path: str = None, **kwargs) -> ToolResult:
        """Convert SPSS/Stata file to CSV."""
        import pandas as pd
        import pyreadstat
        from pathlib import Path
        
        try:
            file_ext = Path(filepath).suffix.lower()
            
            if file_ext == '.sav':
                df, _ = pyreadstat.read_sav(filepath)
            elif file_ext == '.dta':
                df, _ = pyreadstat.read_dta(filepath)
            else:
                return ToolResult(success=False, error=f"Unsupported file format: {file_ext}")
            
            if not output_path:
                output_path = str(Path(filepath).with_suffix('.csv'))
            
            df.to_csv(output_path, index=False)
            
            return ToolResult(
                success=True,
                data={
                    'input_file': filepath,
                    'output_file': output_path,
                    'rows_converted': len(df)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for file format operations."""
        code_templates = {
            'read_spss': '''
import pandas as pd
import pyreadstat

# Read SPSS file
filepath = "{filepath}"
df, meta = pyreadstat.read_sav(filepath)

print(f"Loaded {{len(df)}} rows, {{len(df.columns)}} columns")
print("\\nColumn labels:")
for col, label in meta.column_labels.items():
    print(f"  {{col}}: {{label}}")

print("\\nFirst few rows:")
print(df.head())
''',
            'read_stata': '''
import pandas as pd
import pyreadstat

# Read Stata file
filepath = "{filepath}"
df, meta = pyreadstat.read_dta(filepath)

print(f"Loaded {{len(df)}} rows, {{len(df.columns)}} columns")
print("\\nFirst few rows:")
print(df.head())
''',
            'convert_to_csv': '''
import pandas as pd
import pyreadstat
from pathlib import Path

# Read SPSS/Stata file
filepath = "{filepath}"
file_ext = Path(filepath).suffix.lower()

if file_ext == '.sav':
    df, _ = pyreadstat.read_sav(filepath)
elif file_ext == '.dta':
    df, _ = pyreadstat.read_dta(filepath)

# Convert to CSV
output_path = "{output_path}" or filepath.replace(file_ext, '.csv')
df.to_csv(output_path, index=False)

print(f"Converted {{len(df)}} rows to {{output_path}}")
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'read_spss', 'description': 'Read SPSS .sav file', 'params': ['filepath']},
            {'name': 'read_stata', 'description': 'Read Stata .dta file', 'params': ['filepath']},
            {'name': 'get_metadata', 'description': 'Get file metadata', 'params': ['filepath']},
            {'name': 'convert_to_csv', 'description': 'Convert to CSV', 'params': ['filepath', 'output_path']}
        ]
