"""
Spreadsheet Connector for Tahlil Platform.
Handles connections to online spreadsheets (Google Sheets, Excel Online, Notion).
"""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

# Try to import Google Sheets dependencies
try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google.oauth2.credentials import Credentials as OAuthCredentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    logger.warning("gspread not installed. Google Sheets integration unavailable.")


@dataclass
class SpreadsheetResult:
    """Result from fetching spreadsheet data."""
    success: bool
    data: Optional[pd.DataFrame] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data.to_dict('records') if self.data is not None else None,
            'columns': self.data.columns.tolist() if self.data is not None else [],
            'error': self.error,
            'metadata': self.metadata or {}
        }


class SpreadsheetConnector:
    """
    Handles connections to online spreadsheets.
    Supports: Google Sheets, Excel Online (future), Notion (future)
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize the spreadsheet connector.
        
        Args:
            credentials_path: Path to Google service account credentials JSON file.
                            If None, will try to use OAuth or public sheets.
        """
        self.credentials_path = credentials_path
        self.google_client = None
        
        if GSPREAD_AVAILABLE and credentials_path:
            try:
                self._init_google_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Google client: {e}")
    
    def _init_google_client(self):
        """Initialize Google Sheets client with service account credentials."""
        if not self.credentials_path:
            return
            
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )
            self.google_client = gspread.authorize(creds)
            logger.info("Google Sheets client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def detect_spreadsheet_type(self, url: str) -> str:
        """
        Detect spreadsheet platform from URL.
        
        Args:
            url: The spreadsheet URL
            
        Returns:
            Platform type: 'google_sheets', 'excel_online', 'notion', or 'unknown'
        """
        if 'docs.google.com/spreadsheets' in url:
            return 'google_sheets'
        elif 'onedrive.live.com' in url or 'sharepoint.com' in url:
            return 'excel_online'
        elif 'notion.so' in url or 'notion.site' in url:
            return 'notion'
        else:
            return 'unknown'
    
    def extract_google_sheet_id(self, url: str) -> str:
        """
        Extract sheet ID from Google Sheets URL.
        
        Args:
            url: Google Sheets URL
            
        Returns:
            Sheet ID string
            
        Raises:
            ValueError: If URL is invalid
        """
        # Pattern: /spreadsheets/d/SHEET_ID/
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if match:
            return match.group(1)
        
        # Try alternative pattern for short URLs
        match = re.search(r'spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if match:
            return match.group(1)
            
        raise ValueError(f"Could not extract sheet ID from URL: {url}")
    
    def fetch_google_sheets_public(self, sheet_id: str, worksheet_index: int = 0) -> SpreadsheetResult:
        """
        Fetch data from a PUBLIC Google Sheet (no auth required).
        Uses the CSV export endpoint.
        
        Args:
            sheet_id: Google Sheets document ID
            worksheet_index: Index of the worksheet (0 = first sheet)
            
        Returns:
            SpreadsheetResult with DataFrame
        """
        try:
            # Public CSV export URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={worksheet_index}"
            
            df = pd.read_csv(csv_url)
            
            return SpreadsheetResult(
                success=True,
                data=df,
                metadata={
                    'source_type': 'google_sheets_public',
                    'sheet_id': sheet_id,
                    'worksheet_index': worksheet_index,
                    'rows': len(df),
                    'columns': len(df.columns)
                }
            )
        except Exception as e:
            logger.error(f"Failed to fetch public Google Sheet: {e}")
            return SpreadsheetResult(
                success=False,
                error=f"Failed to fetch sheet. Make sure it's publicly accessible. Error: {str(e)}"
            )
    
    def fetch_google_sheets_auth(
        self, 
        sheet_id: str, 
        worksheet_name: Optional[str] = None
    ) -> SpreadsheetResult:
        """
        Fetch data from Google Sheets using authenticated client.
        
        Args:
            sheet_id: Google Sheets document ID
            worksheet_name: Specific worksheet name (default: first sheet)
            
        Returns:
            SpreadsheetResult with DataFrame
        """
        if not GSPREAD_AVAILABLE:
            return SpreadsheetResult(
                success=False,
                error="gspread library not installed. Run: pip install gspread google-auth"
            )
        
        if not self.google_client:
            return SpreadsheetResult(
                success=False,
                error="Google Sheets client not initialized. Check credentials."
            )
        
        try:
            # Open spreadsheet
            spreadsheet = self.google_client.open_by_key(sheet_id)
            
            # Get worksheet
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0)  # First sheet
            
            # Get all values
            data = worksheet.get_all_records()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            return SpreadsheetResult(
                success=True,
                data=df,
                metadata={
                    'source_type': 'google_sheets',
                    'sheet_id': sheet_id,
                    'spreadsheet_title': spreadsheet.title,
                    'worksheet_title': worksheet.title,
                    'rows': len(df),
                    'columns': len(df.columns)
                }
            )
            
        except gspread.exceptions.APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            return SpreadsheetResult(
                success=False,
                error=f"Google Sheets API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to fetch Google Sheet: {e}")
            return SpreadsheetResult(
                success=False,
                error=f"Failed to fetch sheet: {str(e)}"
            )
    
    def fetch_from_url(
        self, 
        url: str, 
        worksheet_name: Optional[str] = None,
        use_public_method: bool = True
    ) -> SpreadsheetResult:
        """
        Universal method to fetch data from any supported spreadsheet URL.
        
        Args:
            url: Spreadsheet URL
            worksheet_name: Optional worksheet name
            use_public_method: If True, try public CSV export first (no auth needed)
            
        Returns:
            SpreadsheetResult with data and metadata
        """
        spreadsheet_type = self.detect_spreadsheet_type(url)
        
        if spreadsheet_type == 'google_sheets':
            try:
                sheet_id = self.extract_google_sheet_id(url)
            except ValueError as e:
                return SpreadsheetResult(success=False, error=str(e))
            
            # Try public method first if enabled
            if use_public_method:
                result = self.fetch_google_sheets_public(sheet_id)
                if result.success:
                    result.metadata['url'] = url
                    return result
            
            # Fall back to authenticated method
            if self.google_client:
                result = self.fetch_google_sheets_auth(sheet_id, worksheet_name)
                if result.success:
                    result.metadata['url'] = url
                return result
            else:
                return SpreadsheetResult(
                    success=False,
                    error="Sheet is not public and no Google credentials configured. "
                          "Either make the sheet public or configure Google API credentials."
                )
        
        elif spreadsheet_type == 'excel_online':
            return SpreadsheetResult(
                success=False,
                error="Excel Online support coming soon. Please export to CSV or use Google Sheets."
            )
        
        elif spreadsheet_type == 'notion':
            return SpreadsheetResult(
                success=False,
                error="Notion database support coming soon. Please export to CSV."
            )
        
        else:
            return SpreadsheetResult(
                success=False,
                error=f"Unsupported spreadsheet URL format: {url}"
            )
    
    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        """Get list of supported platforms and their status."""
        return [
            {
                'name': 'Google Sheets',
                'id': 'google_sheets',
                'status': 'available',
                'requires_auth': False,  # Public sheets work without auth
                'icon': '📊',
                'description': 'Connect to Google Sheets. Public sheets work instantly, private sheets need credentials.'
            },
            {
                'name': 'Excel Online',
                'id': 'excel_online', 
                'status': 'coming_soon',
                'requires_auth': True,
                'icon': '📗',
                'description': 'Connect to Microsoft Excel Online (SharePoint/OneDrive).'
            },
            {
                'name': 'Notion Database',
                'id': 'notion',
                'status': 'coming_soon',
                'requires_auth': True,
                'icon': '📝',
                'description': 'Connect to Notion databases and tables.'
            }
        ]


# Convenience function
def fetch_spreadsheet(url: str, credentials_path: Optional[str] = None) -> SpreadsheetResult:
    """
    Convenience function to fetch data from a spreadsheet URL.
    
    Args:
        url: Spreadsheet URL (Google Sheets, etc.)
        credentials_path: Optional path to Google credentials JSON
        
    Returns:
        SpreadsheetResult with DataFrame and metadata
    """
    connector = SpreadsheetConnector(credentials_path)
    return connector.fetch_from_url(url)
