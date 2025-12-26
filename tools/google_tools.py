"""
Google Tools Integration for Tahlil Platform.
Provides integration with Google Sheets, Docs, and Forms.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class GoogleSheetsProvider(ToolProvider):
    """
    Integration with Google Sheets using gspread.
    Supports reading, writing, and manipulating spreadsheet data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
        self._credentials_file = config.get('credentials_file') if config else None
    
    @property
    def name(self) -> str:
        return "google_sheets"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DATA_SOURCE
    
    @property
    def description(self) -> str:
        return "Google Sheets integration for reading and writing spreadsheet data"
    
    @property
    def dependencies(self) -> List[str]:
        return ["gspread", "google-auth", "pandas"]
    
    @property
    def requires_auth(self) -> bool:
        return True
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "read_sheet",
            "write_sheet",
            "create_sheet",
            "update_cells",
            "append_rows",
            "get_worksheets",
            "share_sheet"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install Google packages if needed
            from .dependency_manager import check_and_install
            gspread_success, _ = check_and_install('gspread', 'gspread')
            auth_success, _ = check_and_install('google-auth', 'google.auth')
            
            if not gspread_success or not auth_success:
                return False
            
            import gspread
            import google.auth
            import pandas
            return True
        except ImportError:
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            self._gspread = gspread
            
            # Try to authenticate
            if self._credentials_file:
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                creds = Credentials.from_service_account_file(
                    self._credentials_file,
                    scopes=scopes
                )
                self._client = gspread.authorize(creds)
                return ToolResult(success=True, metadata={'authenticated': True})
            else:
                return ToolResult(
                    success=True,
                    metadata={
                        'authenticated': False,
                        'message': 'No credentials file provided. Set credentials_file in config.'
                    }
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a Google Sheets operation."""
        operations = {
            'read': self._read_sheet,
            'write': self._write_sheet,
            'create': self._create_sheet,
            'update_cells': self._update_cells,
            'append': self._append_rows,
            'worksheets': self._get_worksheets,
            'share': self._share_sheet,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        if not self._client:
            return ToolResult(
                success=False,
                error="Not authenticated. Provide credentials_file in config."
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"Google Sheets {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _read_sheet(self, spreadsheet_id: str, worksheet: str = None, 
                    range: str = None, **kwargs) -> ToolResult:
        """Read data from a Google Sheet."""
        import pandas as pd
        
        spreadsheet = self._client.open_by_key(spreadsheet_id)
        
        if worksheet:
            ws = spreadsheet.worksheet(worksheet)
        else:
            ws = spreadsheet.sheet1
        
        if range:
            data = ws.get(range)
        else:
            data = ws.get_all_values()
        
        # Convert to DataFrame
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
        elif data:
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame()
        
        return ToolResult(
            success=True,
            data={
                'records': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'row_count': len(df),
                'spreadsheet_title': spreadsheet.title,
                'worksheet': ws.title
            }
        )
    
    def _write_sheet(self, spreadsheet_id: str, data: List[List], 
                     worksheet: str = None, start_cell: str = 'A1', **kwargs) -> ToolResult:
        """Write data to a Google Sheet."""
        spreadsheet = self._client.open_by_key(spreadsheet_id)
        
        if worksheet:
            ws = spreadsheet.worksheet(worksheet)
        else:
            ws = spreadsheet.sheet1
        
        ws.update(start_cell, data)
        
        return ToolResult(
            success=True,
            data={
                'rows_written': len(data),
                'columns_written': len(data[0]) if data else 0,
                'start_cell': start_cell
            }
        )
    
    def _create_sheet(self, title: str, worksheets: List[str] = None, **kwargs) -> ToolResult:
        """Create a new Google Sheet."""
        spreadsheet = self._client.create(title)
        
        if worksheets:
            # Add additional worksheets
            for ws_title in worksheets[1:]:  # First one is already created
                spreadsheet.add_worksheet(title=ws_title, rows=1000, cols=26)
            # Rename the first worksheet
            if worksheets:
                spreadsheet.sheet1.update_title(worksheets[0])
        
        return ToolResult(
            success=True,
            data={
                'spreadsheet_id': spreadsheet.id,
                'title': title,
                'url': spreadsheet.url
            }
        )
    
    def _update_cells(self, spreadsheet_id: str, updates: Dict[str, Any],
                      worksheet: str = None, **kwargs) -> ToolResult:
        """Update specific cells."""
        spreadsheet = self._client.open_by_key(spreadsheet_id)
        
        if worksheet:
            ws = spreadsheet.worksheet(worksheet)
        else:
            ws = spreadsheet.sheet1
        
        for cell, value in updates.items():
            ws.update_acell(cell, value)
        
        return ToolResult(
            success=True,
            data={
                'cells_updated': len(updates)
            }
        )
    
    def _append_rows(self, spreadsheet_id: str, rows: List[List],
                     worksheet: str = None, **kwargs) -> ToolResult:
        """Append rows to the end of the sheet."""
        spreadsheet = self._client.open_by_key(spreadsheet_id)
        
        if worksheet:
            ws = spreadsheet.worksheet(worksheet)
        else:
            ws = spreadsheet.sheet1
        
        ws.append_rows(rows)
        
        return ToolResult(
            success=True,
            data={
                'rows_appended': len(rows)
            }
        )
    
    def _get_worksheets(self, spreadsheet_id: str, **kwargs) -> ToolResult:
        """List all worksheets in a spreadsheet."""
        spreadsheet = self._client.open_by_key(spreadsheet_id)
        
        worksheets = [
            {
                'title': ws.title,
                'id': ws.id,
                'row_count': ws.row_count,
                'col_count': ws.col_count
            }
            for ws in spreadsheet.worksheets()
        ]
        
        return ToolResult(
            success=True,
            data={
                'spreadsheet_title': spreadsheet.title,
                'worksheets': worksheets
            }
        )
    
    def _share_sheet(self, spreadsheet_id: str, email: str, 
                     role: str = 'reader', **kwargs) -> ToolResult:
        """Share a spreadsheet with a user."""
        spreadsheet = self._client.open_by_key(spreadsheet_id)
        spreadsheet.share(email, perm_type='user', role=role)
        
        return ToolResult(
            success=True,
            data={
                'shared_with': email,
                'role': role
            }
        )
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for Google Sheets operations."""
        code_templates = {
            'read': '''
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Authentication
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
client = gspread.authorize(creds)

# Open spreadsheet and read data
spreadsheet = client.open_by_key("{spreadsheet_id}")
worksheet = spreadsheet.sheet1  # or spreadsheet.worksheet("Sheet Name")

# Get all data as DataFrame
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

print(df.head())
print(f"Total rows: {{len(df)}}")
''',
            'write': '''
import gspread
from google.oauth2.service_account import Credentials

# Authentication
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open_by_key("{spreadsheet_id}")
worksheet = spreadsheet.sheet1

# Write data
data = {data}
worksheet.update('A1', data)

print("Data written successfully!")
''',
            'create': '''
import gspread
from google.oauth2.service_account import Credentials

# Authentication
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
client = gspread.authorize(creds)

# Create new spreadsheet
spreadsheet = client.create("{title}")

print(f"Created: {{spreadsheet.title}}")
print(f"URL: {{spreadsheet.url}}")
print(f"ID: {{spreadsheet.id}}")

# Share with yourself if needed
spreadsheet.share("your-email@example.com", perm_type='user', role='writer')
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'read',
                'description': 'Read data from Google Sheet',
                'params': ['spreadsheet_id', 'worksheet', 'range']
            },
            {
                'name': 'write',
                'description': 'Write data to Google Sheet',
                'params': ['spreadsheet_id', 'data', 'worksheet', 'start_cell']
            },
            {
                'name': 'create',
                'description': 'Create new Google Sheet',
                'params': ['title', 'worksheets']
            },
            {
                'name': 'update_cells',
                'description': 'Update specific cells',
                'params': ['spreadsheet_id', 'updates', 'worksheet']
            },
            {
                'name': 'append',
                'description': 'Append rows to sheet',
                'params': ['spreadsheet_id', 'rows', 'worksheet']
            },
            {
                'name': 'worksheets',
                'description': 'List worksheets',
                'params': ['spreadsheet_id']
            },
            {
                'name': 'share',
                'description': 'Share spreadsheet',
                'params': ['spreadsheet_id', 'email', 'role']
            }
        ]
