"""
API Connector for Tahlil Platform.
Handles connections to REST APIs with various authentication methods.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)

# Import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not installed. API connector unavailable.")


class AuthType(Enum):
    """Supported authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"


class HttpMethod(Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"


@dataclass
class APIConfig:
    """Configuration for an API request."""
    url: str
    method: HttpMethod = HttpMethod.GET
    auth_type: AuthType = AuthType.NONE
    auth_config: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    json_path: Optional[str] = None  # JSONPath to extract data array
    timeout: int = 30


@dataclass
class APIResult:
    """Result from an API request."""
    success: bool
    data: Optional[pd.DataFrame] = None
    raw_response: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data.to_dict('records') if self.data is not None else None,
            'columns': self.data.columns.tolist() if self.data is not None else [],
            'error': self.error,
            'metadata': self.metadata
        }


class APIConnector:
    """
    Connects to REST APIs and fetches data.
    Supports various authentication methods and response parsing.
    """
    
    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout
        self.session = requests.Session() if REQUESTS_AVAILABLE else None
    
    def _build_auth_headers(self, config: APIConfig) -> Dict[str, str]:
        """Build authentication headers based on config."""
        headers = config.headers.copy()
        
        if config.auth_type == AuthType.API_KEY:
            # API key can be in header or query param
            key_name = config.auth_config.get('key_name', 'X-API-Key')
            key_value = config.auth_config.get('key_value', '')
            key_location = config.auth_config.get('location', 'header')
            
            if key_location == 'header':
                headers[key_name] = key_value
            # Query param handled separately
            
        elif config.auth_type == AuthType.BEARER:
            token = config.auth_config.get('token', '')
            headers['Authorization'] = f'Bearer {token}'
            
        elif config.auth_type == AuthType.BASIC:
            import base64
            username = config.auth_config.get('username', '')
            password = config.auth_config.get('password', '')
            credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        
        return headers
    
    def _build_params(self, config: APIConfig) -> Dict[str, str]:
        """Build query parameters including API key if needed."""
        params = config.params.copy()
        
        if config.auth_type == AuthType.API_KEY:
            location = config.auth_config.get('location', 'header')
            if location == 'query':
                key_name = config.auth_config.get('key_name', 'api_key')
                key_value = config.auth_config.get('key_value', '')
                params[key_name] = key_value
        
        return params
    
    def _extract_data(self, response_json: Any, json_path: Optional[str] = None) -> List[Dict]:
        """
        Extract data array from JSON response.
        
        Args:
            response_json: The JSON response
            json_path: Optional dot-notation path to data (e.g., "data.items")
        
        Returns:
            List of dictionaries suitable for DataFrame
        """
        data = response_json
        
        # Navigate to nested path if specified
        if json_path:
            for key in json_path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                elif isinstance(data, list) and key.isdigit():
                    data = data[int(key)]
                else:
                    raise ValueError(f"Path '{json_path}' not found in response")
        
        # Handle different response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # If it's a single object, wrap in list
            if all(not isinstance(v, (list, dict)) for v in data.values()):
                return [data]
            # If it has a nested array, try common keys
            for key in ['data', 'items', 'results', 'records', 'rows', 'entries']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Fallback: wrap in list
            return [data]
        else:
            raise ValueError(f"Cannot parse response type: {type(data)}")
    
    def fetch(self, config: APIConfig) -> APIResult:
        """
        Fetch data from an API endpoint.
        
        Args:
            config: APIConfig with all request details
            
        Returns:
            APIResult with DataFrame and metadata
        """
        if not REQUESTS_AVAILABLE:
            return APIResult(
                success=False,
                error="requests library not installed. Run: pip install requests"
            )
        
        try:
            # Build request
            headers = self._build_auth_headers(config)
            params = self._build_params(config)
            
            # Set content type for JSON body
            if config.body and 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            # Make request
            if config.method == HttpMethod.GET:
                response = self.session.get(
                    config.url,
                    headers=headers,
                    params=params,
                    timeout=config.timeout
                )
            else:  # POST
                response = self.session.post(
                    config.url,
                    headers=headers,
                    params=params,
                    json=config.body,
                    timeout=config.timeout
                )
            
            # Check response status
            response.raise_for_status()
            
            # Parse JSON response
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                return APIResult(
                    success=False,
                    error="Response is not valid JSON"
                )
            
            # Extract data array
            try:
                data_list = self._extract_data(response_json, config.json_path)
            except ValueError as e:
                return APIResult(
                    success=False,
                    error=str(e),
                    raw_response=response_json
                )
            
            # Convert to DataFrame
            if not data_list:
                return APIResult(
                    success=False,
                    error="No data found in response",
                    raw_response=response_json
                )
            
            df = pd.DataFrame(data_list)
            
            return APIResult(
                success=True,
                data=df,
                raw_response=response_json,
                metadata={
                    'source_type': 'api',
                    'url': config.url,
                    'method': config.method.value,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'status_code': response.status_code
                }
            )
            
        except requests.exceptions.Timeout:
            return APIResult(
                success=False,
                error=f"Request timed out after {config.timeout} seconds"
            )
        except requests.exceptions.ConnectionError:
            return APIResult(
                success=False,
                error="Connection failed. Check the URL and try again."
            )
        except requests.exceptions.HTTPError as e:
            return APIResult(
                success=False,
                error=f"HTTP Error {e.response.status_code}: {e.response.reason}"
            )
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return APIResult(
                success=False,
                error=f"Request failed: {str(e)}"
            )
    
    def fetch_from_url(
        self,
        url: str,
        method: str = "GET",
        auth_type: str = "none",
        auth_config: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None,
        json_path: Optional[str] = None
    ) -> APIResult:
        """
        Convenience method to fetch from URL with simple parameters.
        """
        config = APIConfig(
            url=url,
            method=HttpMethod[method.upper()],
            auth_type=AuthType(auth_type.lower()),
            auth_config=auth_config or {},
            headers=headers or {},
            params=params or {},
            body=body,
            json_path=json_path
        )
        return self.fetch(config)
    
    @staticmethod
    def get_supported_auth_types() -> List[Dict[str, str]]:
        """Get list of supported authentication types."""
        return [
            {'id': 'none', 'name': 'No Authentication', 'description': 'Public API, no auth required'},
            {'id': 'api_key', 'name': 'API Key', 'description': 'API key in header or query parameter'},
            {'id': 'bearer', 'name': 'Bearer Token', 'description': 'OAuth2 Bearer token authentication'},
            {'id': 'basic', 'name': 'Basic Auth', 'description': 'Username and password authentication'},
        ]


# Convenience function
def fetch_api(
    url: str,
    method: str = "GET",
    auth_type: str = "none",
    auth_config: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    json_path: Optional[str] = None
) -> APIResult:
    """
    Convenience function to fetch data from an API.
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET or POST)
        auth_type: Authentication type (none, api_key, bearer, basic)
        auth_config: Authentication configuration
        headers: Additional headers
        json_path: Path to data array in response
        
    Returns:
        APIResult with DataFrame and metadata
    """
    connector = APIConnector()
    return connector.fetch_from_url(
        url=url,
        method=method,
        auth_type=auth_type,
        auth_config=auth_config,
        headers=headers,
        json_path=json_path
    )
