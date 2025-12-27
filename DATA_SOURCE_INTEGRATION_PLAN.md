# Data Source Integration Strategy for Tahlil Platform

**Document Version:** 1.0  
**Date:** December 26, 2025  
**Status:** Implementation Ready

---

## 📋 Executive Summary

This document outlines the architecture and implementation strategy for expanding Tahlil's data input capabilities beyond file uploads to include:

1. **Spreadsheet Links** (Google Sheets, Excel Online, Notion databases)
2. **Direct API Connections** (REST APIs, GraphQL, webhooks)
3. **CRM Platform Integrations** (1C, AmoCRM, Bitrix24, Salesforce, HubSpot)
4. **Database Connections** (PostgreSQL, MySQL, MongoDB, etc.)

---

## 🎯 Current State Analysis

### Current Capabilities ✅

Your platform currently supports:
- **File Upload Only**: CSV, Excel (.xlsx, .xls), JSON, TXT, Parquet
- **Local Storage**: SQLite-based deduplication system
- **Single Upload Method**: HTML file input via `/api/data/upload`
- **✅ SQL Export (NEW)**: Convert any data to SQL scripts with advanced features:
  - 5 SQL dialects (PostgreSQL, MySQL, SQLite, SQL Server, Oracle)
  - Auto-detection of foreign keys, CHECK constraints, indexes, validation rules
  - See [SQL_GENERATOR_FEATURE.md](SQL_GENERATOR_FEATURE.md) for details

### Architecture Review

```python
# Current flow: app.py line 176-215
@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    file = request.files['file']
    file_content = file.read()
    file_info = storage_manager.store_file(file_content, filename, user_id)
    # Stores in data/files/ with hash-based deduplication
```

**Limitation**: Only accepts `multipart/form-data` file uploads

---

## 🏗️ Proposed Architecture: Universal Data Connector

### Concept: "Data Sources" Instead of "Files"

Transform the current file-centric approach into a **data source connector** system:

```
┌─────────────────────────────────────────────────────────────┐
│               User Interface (Frontend)                     │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  Upload  │ Paste    │  API     │  CRM     │  Database       │
│  File    │  Link    │  Connect │  Connect │  Connect        │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
           │          │          │          │          │
           ▼          ▼          ▼          ▼          ▼
┌──────────────────────────────────────────────────────────────┐
│         Data Source Router (New Abstraction Layer)           │
│  • Determines source type                                    │
│  • Validates credentials                                     │
│  • Fetches data                                              │
│  • Converts to standard format (pandas DataFrame)            │
└──────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│              Unified Storage Manager                         │
│  • Stores data snapshot                                      │
│  • Saves connection metadata                                 │
│  • Handles refresh logic                                     │
└──────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│              Tahlil Analysis Engine                          │
│         (Continues as normal from here)                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Phase 1: Spreadsheet Link Integration (Week 1-3)

### 1.1 Google Sheets Integration

**How It Works:**
- User pastes Google Sheets URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
- Platform extracts `SHEET_ID`
- Uses Google Sheets API to fetch data
- Converts to pandas DataFrame

**Implementation:**

```python
# tools/spreadsheet_connector.py

import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Optional
import pandas as pd
import re

class SpreadsheetConnector:
    """
    Handles connections to online spreadsheets.
    Supports: Google Sheets, Excel Online, Notion
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.google_creds = None
        if credentials_path:
            self.google_creds = Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
    
    def detect_spreadsheet_type(self, url: str) -> str:
        """Detect spreadsheet platform from URL."""
        if 'docs.google.com/spreadsheets' in url:
            return 'google_sheets'
        elif 'onedrive.live.com' in url or 'sharepoint.com' in url:
            return 'excel_online'
        elif 'notion.so' in url:
            return 'notion'
        else:
            raise ValueError(f"Unsupported spreadsheet URL: {url}")
    
    def extract_google_sheet_id(self, url: str) -> str:
        """Extract sheet ID from Google Sheets URL."""
        # Pattern: /spreadsheets/d/SHEET_ID/
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if match:
            return match.group(1)
        raise ValueError("Invalid Google Sheets URL")
    
    def fetch_google_sheets_data(
        self, 
        sheet_id: str, 
        worksheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch data from Google Sheets.
        
        Args:
            sheet_id: Google Sheets document ID
            worksheet_name: Specific worksheet name (default: first sheet)
            
        Returns:
            pandas DataFrame with sheet data
        """
        try:
            # Authenticate
            client = gspread.authorize(self.google_creds)
            
            # Open spreadsheet
            spreadsheet = client.open_by_key(sheet_id)
            
            # Get worksheet
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0)  # First sheet
            
            # Get all values
            data = worksheet.get_all_records()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to fetch Google Sheets data: {e}")
    
    def fetch_from_url(
        self, 
        url: str, 
        worksheet_name: Optional[str] = None
    ) -> Dict:
        """
        Universal method to fetch data from any supported spreadsheet URL.
        
        Returns:
            Dict with 'data' (DataFrame as dict) and 'metadata'
        """
        spreadsheet_type = self.detect_spreadsheet_type(url)
        
        if spreadsheet_type == 'google_sheets':
            sheet_id = self.extract_google_sheet_id(url)
            df = self.fetch_google_sheets_data(sheet_id, worksheet_name)
            
            return {
                'data': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'metadata': {
                    'source_type': 'google_sheets',
                    'sheet_id': sheet_id,
                    'url': url,
                    'rows': len(df),
                    'columns_count': len(df.columns)
                }
            }
        
        elif spreadsheet_type == 'excel_online':
            # TODO: Implement Excel Online support
            raise NotImplementedError("Excel Online support coming soon")
        
        elif spreadsheet_type == 'notion':
            # TODO: Implement Notion support
            raise NotImplementedError("Notion support coming soon")
```

**Google Sheets Setup Guide:**

1. **Create Service Account** (for server-side access):
   - Go to Google Cloud Console
   - Create new project
   - Enable Google Sheets API
   - Create Service Account
   - Download JSON credentials

2. **Alternative: OAuth2 Flow** (for user access):
   - Better UX: users authenticate with their Google account
   - Platform accesses only sheets they have access to

**Best Practice Recommendation:** Use OAuth2 for production, Service Account for development.

---

### 1.2 Frontend: Link Input UI

Add new input method to frontend:

```tsx
// frontend/components/DataSourceSelector.tsx

import React, { useState } from 'react';

type SourceType = 'file' | 'link' | 'api' | 'crm' | 'database';

export const DataSourceSelector: React.FC = () => {
  const [sourceType, setSourceType] = useState<SourceType>('file');
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleLinkSubmit = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/data/from-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, source_type: 'spreadsheet' })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Data fetched:', data);
        // Update file list
      }
    } catch (error) {
      console.error('Failed to fetch from link:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="data-source-selector">
      <div className="source-tabs">
        <button 
          className={sourceType === 'file' ? 'active' : ''}
          onClick={() => setSourceType('file')}
        >
          📁 Upload File
        </button>
        <button 
          className={sourceType === 'link' ? 'active' : ''}
          onClick={() => setSourceType('link')}
        >
          🔗 Paste Link
        </button>
        <button 
          className={sourceType === 'api' ? 'active' : ''}
          onClick={() => setSourceType('api')}
        >
          🔌 API Connection
        </button>
        <button 
          className={sourceType === 'crm' ? 'active' : ''}
          onClick={() => setSourceType('crm')}
        >
          👥 CRM Integration
        </button>
      </div>
      
      {sourceType === 'file' && (
        <div className="upload-area">
          {/* Existing file upload UI */}
        </div>
      )}
      
      {sourceType === 'link' && (
        <div className="link-input">
          <h3>📊 Connect Spreadsheet</h3>
          <p>Paste a link to Google Sheets, Excel Online, or Notion database</p>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://docs.google.com/spreadsheets/d/..."
            className="link-input-field"
          />
          <button 
            onClick={handleLinkSubmit}
            disabled={!url || loading}
            className="fetch-btn"
          >
            {loading ? 'Fetching...' : '📥 Fetch Data'}
          </button>
          
          <div className="supported-platforms">
            <p>Supported platforms:</p>
            <ul>
              <li>✅ Google Sheets</li>
              <li>🔜 Excel Online (coming soon)</li>
              <li>🔜 Notion (coming soon)</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

### 1.3 Backend: New API Endpoint

Add to `app.py`:

```python
# Add to app.py

from tools.spreadsheet_connector import SpreadsheetConnector

spreadsheet_connector = SpreadsheetConnector(
    credentials_path=os.environ.get('GOOGLE_CREDENTIALS_PATH', 'config/google_credentials.json')
)

@app.route('/api/data/from-link', methods=['POST'])
def fetch_from_link():
    """
    Fetch data from external link (Google Sheets, Excel Online, etc.)
    """
    try:
        data = request.json
        url = data.get('url')
        source_type = data.get('source_type', 'spreadsheet')
        worksheet_name = data.get('worksheet_name')
        user_id = data.get('user_id', 'default')
        
        if not url:
            return jsonify({'error': 'URL is required', 'success': False}), 400
        
        # Fetch data from spreadsheet
        result = spreadsheet_connector.fetch_from_url(url, worksheet_name)
        
        # Convert to CSV and store like a regular file
        df = pd.DataFrame(result['data'])
        csv_content = df.to_csv(index=False).encode('utf-8')
        
        # Generate filename from URL
        filename = f"sheet_{result['metadata']['sheet_id'][:8]}.csv"
        
        # Store using existing storage manager
        file_info = storage_manager.store_file(csv_content, filename, user_id)
        
        # Add metadata about the link
        file_info['source_url'] = url
        file_info['source_type'] = source_type
        file_info['fetched_at'] = datetime.now().isoformat()
        
        logger.info(f"Data fetched from link: {url} (rows: {result['metadata']['rows']})")
        
        return jsonify({
            'success': True,
            'file': file_info,
            'preview': result['data'][:5]  # First 5 rows
        })
        
    except ValueError as e:
        logger.warning(f"Link fetch validation failed: {e}")
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        logger.error(f"Error fetching from link: {e}")
        return jsonify({'error': str(e), 'success': False}), 500
```

---

## 🔌 Phase 2: Direct API Connections (Week 3-5)

### 2.1 API Connector Architecture

**Use Case:** User wants to analyze data from their company's REST API

**Example:**
- API Endpoint: `https://api.company.com/sales/data`
- Authentication: API key or OAuth
- Response: JSON array of sales records

**Implementation:**

```python
# tools/api_connector.py

import requests
from typing import Dict, List, Optional, Any
import pandas as pd
from urllib.parse import urljoin

class APIConnector:
    """
    Universal API connection handler.
    Supports: REST APIs, GraphQL, webhooks
    """
    
    def __init__(self):
        self.session = requests.Session()
    
    def connect_rest_api(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None,
        auth_type: Optional[str] = None,
        credentials: Optional[Dict] = None
    ) -> Dict:
        """
        Connect to REST API and fetch data.
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            headers: Custom headers
            params: Query parameters
            body: Request body (for POST/PUT)
            auth_type: 'api_key', 'bearer', 'basic', or 'oauth'
            credentials: Authentication credentials
            
        Returns:
            Dict with 'data' and 'metadata'
        """
        # Set up authentication
        if auth_type and credentials:
            headers = headers or {}
            
            if auth_type == 'api_key':
                # API key can be in header or query param
                if 'header_name' in credentials:
                    headers[credentials['header_name']] = credentials['api_key']
                else:
                    params = params or {}
                    params['api_key'] = credentials['api_key']
            
            elif auth_type == 'bearer':
                headers['Authorization'] = f"Bearer {credentials['token']}"
            
            elif auth_type == 'basic':
                from requests.auth import HTTPBasicAuth
                auth = HTTPBasicAuth(credentials['username'], credentials['password'])
                self.session.auth = auth
            
            elif auth_type == 'oauth':
                # OAuth token
                headers['Authorization'] = f"Bearer {credentials['access_token']}"
        
        # Make request
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=body,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Check for common data wrappers
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'results' in data:
                    df = pd.DataFrame(data['results'])
                elif 'items' in data:
                    df = pd.DataFrame(data['items'])
                else:
                    # Single record
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Unexpected API response format")
            
            return {
                'data': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'metadata': {
                    'source_type': 'rest_api',
                    'url': url,
                    'method': method,
                    'rows': len(df),
                    'status_code': response.status_code,
                    'fetched_at': pd.Timestamp.now().isoformat()
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API request failed: {e}")
    
    def connect_graphql(
        self,
        endpoint: str,
        query: str,
        variables: Optional[Dict] = None,
        auth_token: Optional[str] = None
    ) -> Dict:
        """Connect to GraphQL API."""
        headers = {'Content-Type': 'application/json'}
        if auth_token:
            headers['Authorization'] = f"Bearer {auth_token}"
        
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        # Extract data from GraphQL response
        data = result.get('data', {})
        
        # Find the actual data array (usually nested)
        for key, value in data.items():
            if isinstance(value, list):
                df = pd.DataFrame(value)
                break
        else:
            df = pd.DataFrame([data])
        
        return {
            'data': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'metadata': {
                'source_type': 'graphql',
                'endpoint': endpoint,
                'rows': len(df)
            }
        }
```

### 2.2 API Connection UI

```tsx
// frontend/components/APIConnectionForm.tsx

export const APIConnectionForm: React.FC = () => {
  const [config, setConfig] = useState({
    url: '',
    method: 'GET',
    auth_type: 'none',
    headers: {},
    // ... more fields
  });
  
  return (
    <div className="api-connection-form">
      <h3>🔌 Connect to API</h3>
      
      <label>API Endpoint URL</label>
      <input
        type="url"
        value={config.url}
        onChange={(e) => setConfig({...config, url: e.target.value})}
        placeholder="https://api.example.com/data"
      />
      
      <label>HTTP Method</label>
      <select value={config.method} onChange={(e) => setConfig({...config, method: e.target.value})}>
        <option value="GET">GET</option>
        <option value="POST">POST</option>
        <option value="PUT">PUT</option>
      </select>
      
      <label>Authentication</label>
      <select value={config.auth_type} onChange={(e) => setConfig({...config, auth_type: e.target.value})}>
        <option value="none">None</option>
        <option value="api_key">API Key</option>
        <option value="bearer">Bearer Token</option>
        <option value="basic">Basic Auth</option>
        <option value="oauth">OAuth 2.0</option>
      </select>
      
      {config.auth_type === 'api_key' && (
        <div>
          <input 
            type="text" 
            placeholder="API Key"
            onChange={(e) => setConfig({...config, api_key: e.target.value})}
          />
        </div>
      )}
      
      {/* Add more auth fields based on type */}
      
      <button onClick={handleConnect}>
        🔗 Test Connection & Fetch Data
      </button>
    </div>
  );
};
```

---

## 👥 Phase 3: CRM Platform Integrations (Week 5-8)

### 3.1 CRM Integration Strategy

**Supported CRMs:**
1. **Bitrix24** (Russian market leader)
2. **AmoCRM** (Popular in CIS)
3. **1C:CRM** (Enterprise ERP/CRM)
4. **Salesforce** (Global standard)
5. **HubSpot** (Marketing-focused)

**Common Pattern:**
- Each CRM has a REST API
- OAuth 2.0 or API key authentication
- Standard endpoints: `/leads`, `/contacts`, `/deals`, `/companies`

### 3.2 Universal CRM Connector

```python
# tools/crm_connector.py

from typing import Dict, List, Optional
import requests
import pandas as pd
from abc import ABC, abstractmethod

class BaseCRMConnector(ABC):
    """Base class for all CRM connectors."""
    
    def __init__(self, credentials: Dict):
        self.credentials = credentials
        self.session = requests.Session()
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with CRM."""
        pass
    
    @abstractmethod
    def fetch_leads(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch leads/prospects."""
        pass
    
    @abstractmethod
    def fetch_deals(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch deals/opportunities."""
        pass
    
    @abstractmethod
    def fetch_companies(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch companies/accounts."""
        pass


class Bitrix24Connector(BaseCRMConnector):
    """
    Bitrix24 CRM connector.
    
    Setup:
    1. Go to Bitrix24 > Settings > Developer Resources
    2. Create webhook or OAuth app
    3. Get access token
    """
    
    def __init__(self, domain: str, access_token: str):
        super().__init__({'domain': domain, 'access_token': access_token})
        self.base_url = f"https://{domain}/rest/"
    
    def authenticate(self) -> bool:
        """Test authentication."""
        try:
            response = self.session.get(
                f"{self.base_url}/user.current.json",
                params={'auth': self.credentials['access_token']}
            )
            return response.status_code == 200
        except:
            return False
    
    def fetch_leads(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch leads from Bitrix24."""
        leads = []
        start = 0
        
        while len(leads) < limit:
            response = self.session.get(
                f"{self.base_url}/crm.lead.list.json",
                params={
                    'auth': self.credentials['access_token'],
                    'start': start,
                    'limit': 50
                }
            )
            
            data = response.json()
            if 'result' not in data or not data['result']:
                break
            
            leads.extend(data['result'])
            start += 50
            
            if len(data['result']) < 50:
                break
        
        return pd.DataFrame(leads)
    
    def fetch_deals(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch deals from Bitrix24."""
        deals = []
        start = 0
        
        while len(deals) < limit:
            response = self.session.get(
                f"{self.base_url}/crm.deal.list.json",
                params={
                    'auth': self.credentials['access_token'],
                    'start': start,
                    'limit': 50
                }
            )
            
            data = response.json()
            if 'result' not in data or not data['result']:
                break
            
            deals.extend(data['result'])
            start += 50
        
        return pd.DataFrame(deals)
    
    def fetch_companies(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch companies from Bitrix24."""
        companies = []
        start = 0
        
        while len(companies) < limit:
            response = self.session.get(
                f"{self.base_url}/crm.company.list.json",
                params={
                    'auth': self.credentials['access_token'],
                    'start': start,
                    'limit': 50
                }
            )
            
            data = response.json()
            if 'result' not in data or not data['result']:
                break
            
            companies.extend(data['result'])
            start += 50
        
        return pd.DataFrame(companies)


class AmoCRMConnector(BaseCRMConnector):
    """
    AmoCRM connector.
    
    Setup:
    1. Go to AmoCRM > Settings > Integrations > API
    2. Create integration
    3. Get access token via OAuth
    """
    
    def __init__(self, subdomain: str, access_token: str):
        super().__init__({'subdomain': subdomain, 'access_token': access_token})
        self.base_url = f"https://{subdomain}.amocrm.ru/api/v4"
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })
    
    def authenticate(self) -> bool:
        """Test authentication."""
        try:
            response = self.session.get(f"{self.base_url}/account")
            return response.status_code == 200
        except:
            return False
    
    def fetch_leads(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch leads from AmoCRM."""
        page = 1
        leads = []
        
        while len(leads) < limit:
            response = self.session.get(
                f"{self.base_url}/leads",
                params={'page': page, 'limit': 250}
            )
            
            data = response.json()
            if '_embedded' not in data or 'leads' not in data['_embedded']:
                break
            
            leads.extend(data['_embedded']['leads'])
            page += 1
            
            if len(data['_embedded']['leads']) < 250:
                break
        
        return pd.DataFrame(leads[:limit])
    
    def fetch_deals(self, limit: int = 1000) -> pd.DataFrame:
        """AmoCRM calls everything 'leads', so this is an alias."""
        return self.fetch_leads(limit)
    
    def fetch_companies(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch companies from AmoCRM."""
        page = 1
        companies = []
        
        while len(companies) < limit:
            response = self.session.get(
                f"{self.base_url}/companies",
                params={'page': page, 'limit': 250}
            )
            
            data = response.json()
            if '_embedded' not in data or 'companies' not in data['_embedded']:
                break
            
            companies.extend(data['_embedded']['companies'])
            page += 1
        
        return pd.DataFrame(companies[:limit])


class OneCConnector(BaseCRMConnector):
    """
    1C:Enterprise CRM connector.
    
    Note: 1C typically uses OData protocol or custom REST API
    Setup depends on your 1C configuration.
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        super().__init__({'base_url': base_url, 'username': username, 'password': password})
        from requests.auth import HTTPBasicAuth
        self.session.auth = HTTPBasicAuth(username, password)
        self.base_url = base_url
    
    def authenticate(self) -> bool:
        """Test authentication."""
        try:
            response = self.session.get(f"{self.base_url}/$metadata")
            return response.status_code == 200
        except:
            return False
    
    def fetch_leads(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch leads from 1C via OData."""
        # OData query
        response = self.session.get(
            f"{self.base_url}/Catalog_Потенциальные клиенты",
            params={'$top': limit, '$format': 'json'}
        )
        
        data = response.json()
        if 'value' in data:
            return pd.DataFrame(data['value'])
        return pd.DataFrame()
    
    def fetch_deals(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch deals from 1C."""
        response = self.session.get(
            f"{self.base_url}/Document_Сделка",
            params={'$top': limit, '$format': 'json'}
        )
        
        data = response.json()
        if 'value' in data:
            return pd.DataFrame(data['value'])
        return pd.DataFrame()
    
    def fetch_companies(self, limit: int = 1000) -> pd.DataFrame:
        """Fetch companies from 1C."""
        response = self.session.get(
            f"{self.base_url}/Catalog_Контрагенты",
            params={'$top': limit, '$format': 'json'}
        )
        
        data = response.json()
        if 'value' in data:
            return pd.DataFrame(data['value'])
        return pd.DataFrame()


# Factory pattern for easy CRM selection
class CRMConnectorFactory:
    """Factory to create appropriate CRM connector."""
    
    @staticmethod
    def create(crm_type: str, credentials: Dict) -> BaseCRMConnector:
        """
        Create CRM connector based on type.
        
        Args:
            crm_type: 'bitrix24', 'amocrm', '1c', 'salesforce', 'hubspot'
            credentials: Dict with required credentials for that CRM
        """
        if crm_type == 'bitrix24':
            return Bitrix24Connector(
                domain=credentials['domain'],
                access_token=credentials['access_token']
            )
        
        elif crm_type == 'amocrm':
            return AmoCRMConnector(
                subdomain=credentials['subdomain'],
                access_token=credentials['access_token']
            )
        
        elif crm_type == '1c':
            return OneCConnector(
                base_url=credentials['base_url'],
                username=credentials['username'],
                password=credentials['password']
            )
        
        # Add more CRMs...
        else:
            raise ValueError(f"Unsupported CRM type: {crm_type}")
```

### 3.3 CRM Integration UI

```tsx
// frontend/components/CRMConnectionForm.tsx

export const CRMConnectionForm: React.FC = () => {
  const [crmType, setCRMType] = useState('bitrix24');
  const [config, setConfig] = useState({});
  const [dataType, setDataType] = useState('leads');
  
  return (
    <div className="crm-connection-form">
      <h3>👥 Connect to CRM</h3>
      
      <label>Select CRM Platform</label>
      <select value={crmType} onChange={(e) => setCRMType(e.target.value)}>
        <option value="bitrix24">Bitrix24</option>
        <option value="amocrm">AmoCRM</option>
        <option value="1c">1C:CRM</option>
        <option value="salesforce">Salesforce</option>
        <option value="hubspot">HubSpot</option>
      </select>
      
      {crmType === 'bitrix24' && (
        <div className="bitrix24-config">
          <label>Bitrix24 Domain</label>
          <input 
            type="text" 
            placeholder="yourcompany.bitrix24.ru"
            onChange={(e) => setConfig({...config, domain: e.target.value})}
          />
          
          <label>Webhook URL or Access Token</label>
          <input 
            type="text" 
            placeholder="Paste your webhook URL or token"
            onChange={(e) => setConfig({...config, access_token: e.target.value})}
          />
        </div>
      )}
      
      {crmType === 'amocrm' && (
        <div className="amocrm-config">
          <label>AmoCRM Subdomain</label>
          <input 
            type="text" 
            placeholder="yourcompany"
            onChange={(e) => setConfig({...config, subdomain: e.target.value})}
          />
          
          <label>Access Token</label>
          <input 
            type="password" 
            placeholder="Your access token"
            onChange={(e) => setConfig({...config, access_token: e.target.value})}
          />
          
          <a href="#" className="oauth-link">
            🔐 Authenticate via OAuth →
          </a>
        </div>
      )}
      
      <label>Data to Fetch</label>
      <select value={dataType} onChange={(e) => setDataType(e.target.value)}>
        <option value="leads">Leads / Prospects</option>
        <option value="deals">Deals / Opportunities</option>
        <option value="companies">Companies / Accounts</option>
        <option value="contacts">Contacts</option>
      </select>
      
      <button onClick={handleConnect}>
        🔗 Connect & Fetch Data
      </button>
    </div>
  );
};
```

---

## 🗄️ Phase 4: Database Connections (Week 8-10)

### 4.1 Database Connector

```python
# tools/database_connector.py

from sqlalchemy import create_engine, inspect
import pandas as pd
from typing import Dict, List, Optional

class DatabaseConnector:
    """
    Connect to SQL databases directly.
    Supports: PostgreSQL, MySQL, SQLite, SQL Server, Oracle
    """
    
    def __init__(self):
        self.engine = None
    
    def connect(
        self,
        db_type: str,
        host: str = None,
        port: int = None,
        database: str = None,
        username: str = None,
        password: str = None,
        connection_string: str = None
    ) -> bool:
        """
        Connect to database.
        
        Args:
            db_type: 'postgresql', 'mysql', 'sqlite', 'mssql', 'oracle'
            host, port, database, username, password: Connection details
            connection_string: Alternative full connection string
        """
        try:
            if connection_string:
                self.engine = create_engine(connection_string)
            else:
                # Build connection string
                if db_type == 'postgresql':
                    conn_str = f"postgresql://{username}:{password}@{host}:{port or 5432}/{database}"
                elif db_type == 'mysql':
                    conn_str = f"mysql+pymysql://{username}:{password}@{host}:{port or 3306}/{database}"
                elif db_type == 'sqlite':
                    conn_str = f"sqlite:///{database}"
                elif db_type == 'mssql':
                    conn_str = f"mssql+pyodbc://{username}:{password}@{host}:{port or 1433}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
                else:
                    raise ValueError(f"Unsupported database type: {db_type}")
                
                self.engine = create_engine(conn_str)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            
            return True
            
        except Exception as e:
            raise ValueError(f"Database connection failed: {e}")
    
    def list_tables(self) -> List[str]:
        """List all tables in database."""
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame."""
        return pd.read_sql(query, self.engine)
    
    def fetch_table(self, table_name: str, limit: int = 1000) -> pd.DataFrame:
        """Fetch data from specific table."""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return pd.read_sql(query, self.engine)
```

---

## 🔐 Security Considerations

### Credential Storage

**CRITICAL:** Never store credentials in plain text!

```python
# tools/credential_manager.py

from cryptography.fernet import Fernet
import os
import json
from pathlib import Path

class CredentialManager:
    """Secure credential storage using encryption."""
    
    def __init__(self, encryption_key: str = None):
        # Use environment variable or generate key
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Load from environment or generate
            key_file = Path('.credentials_key')
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def encrypt_credentials(self, credentials: Dict) -> str:
        """Encrypt credentials dictionary."""
        json_str = json.dumps(credentials)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted: str) -> Dict:
        """Decrypt credentials."""
        decrypted = self.cipher.decrypt(encrypted.encode())
        return json.loads(decrypted.decode())
    
    def store_connection(
        self,
        user_id: str,
        connection_name: str,
        source_type: str,
        credentials: Dict
    ):
        """Store encrypted connection credentials."""
        encrypted = self.encrypt_credentials(credentials)
        
        # Store in database
        # connections table: (user_id, connection_name, source_type, encrypted_credentials)
        conn = sqlite3.connect('data/credentials.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO connections 
            (user_id, connection_name, source_type, encrypted_credentials)
            VALUES (?, ?, ?, ?)
        ''', (user_id, connection_name, source_type, encrypted))
        conn.commit()
        conn.close()
    
    def get_connection(self, user_id: str, connection_name: str) -> Dict:
        """Retrieve and decrypt connection credentials."""
        conn = sqlite3.connect('data/credentials.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT encrypted_credentials FROM connections
            WHERE user_id = ? AND connection_name = ?
        ''', (user_id, connection_name))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return self.decrypt_credentials(result[0])
        return None
```

---

## 📊 Database Schema Updates

Add new table to track data sources:

```sql
-- storage.py database additions

CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'file', 'spreadsheet', 'api', 'crm', 'database'
    source_name TEXT NOT NULL,
    source_config TEXT,  -- JSON with connection details (encrypted)
    file_id INTEGER,  -- Reference to files table (snapshot)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    auto_refresh BOOLEAN DEFAULT 0,
    refresh_interval_minutes INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id)
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_source_id INTEGER NOT NULL,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT,  -- 'success', 'failed'
    rows_fetched INTEGER,
    error_message TEXT,
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id)
);
```

---

## 🔄 Auto-Refresh Feature

Allow users to set automatic data refresh:

```python
# tools/data_refresh_scheduler.py

import schedule
import time
import threading

class DataRefreshScheduler:
    """Background scheduler for auto-refreshing data sources."""
    
    def __init__(self, storage_manager, spreadsheet_connector, api_connector, crm_connector):
        self.storage = storage_manager
        self.spreadsheet = spreadsheet_connector
        self.api = api_connector
        self.crm = crm_connector
        self.running = False
    
    def schedule_refresh(self, data_source_id: int, interval_minutes: int):
        """Schedule periodic refresh for a data source."""
        schedule.every(interval_minutes).minutes.do(
            self.refresh_data_source, 
            data_source_id
        )
    
    def refresh_data_source(self, data_source_id: int):
        """Re-fetch data from source and update snapshot."""
        # Get source config from database
        # Fetch new data
        # Update file snapshot
        # Log sync
        pass
    
    def start(self):
        """Start background scheduler thread."""
        self.running = True
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop scheduler."""
        self.running = False
```

---

## 🎯 Best Practices Summary

### 1. **OAuth over API Keys** (when possible)
- More secure
- User controls access
- Can be revoked easily

### 2. **Always Encrypt Credentials**
- Never store in plain text
- Use environment variables
- Encrypt in database

### 3. **Data Snapshots**
- Always create a static snapshot when data is fetched
- Store as regular file in system
- Preserve source metadata

### 4. **Error Handling**
- Connection timeouts
- Invalid credentials
- Rate limiting
- API changes

### 5. **Rate Limiting**
- Respect API rate limits
- Implement retry logic with backoff
- Cache when possible

### 6. **User Education**
- Clear instructions for getting API keys
- Video tutorials for each CRM
- Example configurations

---

## 📅 Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Google Sheets | SpreadsheetConnector class, UI, endpoint |
| 2-3 | API Connections | APIConnector class, auth methods, UI |
| 3-4 | Bitrix24 + AmoCRM | First CRM connectors, factory pattern |
| 4-5 | 1C Integration | OneCConnector, OData protocol |
| 5-6 | Database Connectors | DatabaseConnector, UI for SQL |
| 6-7 | Security Layer | CredentialManager, encryption |
| 7-8 | Auto-Refresh | Scheduler, background tasks |
| 8 | Testing | Integration tests, documentation |

---

## 🧪 Testing Checklist

- [ ] Google Sheets connection works
- [ ] Spreadsheet data converts to DataFrame correctly
- [ ] API authentication (all types) works
- [ ] Bitrix24 connector fetches leads/deals
- [ ] AmoCRM connector works
- [ ] 1C connector works with OData
- [ ] Database connections (PostgreSQL, MySQL)
- [ ] Credentials are encrypted
- [ ] Auto-refresh scheduler runs
- [ ] UI handles all source types
- [ ] Error messages are clear

---

## 📚 Setup Guides for Each Platform

### 🔗 Google Sheets Setup

1. **Method 1: Public Sheet (No auth)**
   - File → Share → Get link → Anyone with link can view
   - Use link directly

2. **Method 2: Service Account (Server)**
   - Google Cloud Console → Create Service Account
   - Download JSON credentials
   - Share sheet with service account email

3. **Method 3: OAuth (User auth)**
   - Create OAuth credentials
   - User authenticates once
   - Platform accesses their sheets

### 💼 Bitrix24 Setup

1. Go to Bitrix24 → Settings → Developer Resources
2. Choose "Incoming Webhook" or "OAuth Application"
3. For webhook: Copy webhook URL (contains access token)
4. For OAuth: Get Client ID + Secret, implement OAuth flow

### 📧 AmoCRM Setup

1. Go to AmoCRM → Settings → Integrations → API
2. Create new integration
3. Get OAuth credentials
4. Implement OAuth 2.0 authorization code flow
5. Exchange code for access token

### 🏢 1C Setup

1. Enable OData publication in 1C configuration
2. Set up HTTP service
3. Configure basic authentication
4. Note the base URL (e.g., `http://server:port/base/odata/standard.odata/`)

---

## 📖 API Endpoint Reference

### New Endpoints to Add

```python
# Data source management
POST   /api/data/from-link         # Fetch from spreadsheet URL
POST   /api/data/from-api          # Connect to REST API
POST   /api/data/from-crm          # Connect to CRM
POST   /api/data/from-database     # Connect to database

# Connection management
GET    /api/connections            # List saved connections
POST   /api/connections            # Save new connection
DELETE /api/connections/:id        # Delete connection
POST   /api/connections/:id/test   # Test connection
POST   /api/connections/:id/sync   # Manually sync data

# OAuth flows
GET    /api/oauth/authorize/:platform  # Start OAuth flow
GET    /api/oauth/callback/:platform   # OAuth callback
```

---

*This implementation plan provides a complete roadmap for expanding Tahlil's data input capabilities to include spreadsheet links, API connections, CRM integrations, and database connections.*

*Last Updated: December 26, 2025*
