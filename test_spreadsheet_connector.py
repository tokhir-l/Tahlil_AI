"""Test the SpreadsheetConnector module."""

from tools.spreadsheet_connector import SpreadsheetConnector

def test_spreadsheet_connector():
    print("Testing SpreadsheetConnector...")
    
    # Initialize connector (no credentials for public sheet testing)
    connector = SpreadsheetConnector()
    print("✅ SpreadsheetConnector initialized")
    
    # Get supported platforms
    platforms = connector.get_supported_platforms()
    print(f"✅ Supported platforms: {[p['name'] for p in platforms]}")
    
    # Test URL detection
    test_urls = [
        "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
        "https://onedrive.live.com/edit.aspx?resid=ABC123",
        "https://notion.so/workspace/database123",
        "https://example.com/data.csv"
    ]
    
    for url in test_urls:
        detected = connector.detect_spreadsheet_type(url)
        print(f"   URL: {url[:50]}... -> Type: {detected}")
    
    # Test Google Sheets ID extraction
    sheet_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
    try:
        sheet_id = connector.extract_google_sheet_id(sheet_url)
        print(f"✅ Extracted Sheet ID: {sheet_id}")
    except Exception as e:
        print(f"❌ Failed to extract ID: {e}")
    
    # Test fetching from a public Google Sheet (Sample Sheet)
    print("\nTesting fetch from public Google Sheet...")
    result = connector.fetch_from_url(sheet_url)
    
    if result.success:
        print(f"✅ Successfully fetched data!")
        print(f"   Rows: {result.metadata.get('rows', 0)}")
        print(f"   Columns: {result.metadata.get('columns', 0)}")
        print(f"   First few column names: {list(result.data.columns[:5])}")
    else:
        print(f"⚠️  Fetch failed (expected for non-public sheets): {result.error}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_spreadsheet_connector()
