
import requests
import pandas as pd
from typing import Dict, List, Optional, Any
import logging
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

class OneCConnector:
    """
    Connector for 1C:Enterprise (1S) via OData Standard Interface.
    URL Format: http://host/base/odata/standard.odata/
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({'Accept': 'application/json'})

    def authenticate(self) -> bool:
        """Test connection by fetching metadata or simple catalog."""
        try:
            # Try to fetch root $metadata or a standard catalog
            # Some OData services return XML for metadata, but we just check 200 OK
            response = self.session.get(f"{self.base_url}/$metadata")
            if response.status_code == 200:
                return True
                
            # Fallback: try to list catalogs
            response = self.session.get(f"{self.base_url}/Catalog_Clients?$top=1")
            return response.status_code in [200, 404] # 404 means catalog doesn't exist but auth worked
        except Exception as e:
            logger.error(f"1C connection error: {e}")
            return False

    def fetch_data(self, resource_name: str, limit: int = 1000, query_params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Fetch data from a specific OData resource (Catalog, Document, etc.)
        
        Args:
            resource_name: e.g. "Catalog_Clients", "Document_Order"
            limit: Max records
            query_params: Additional OData params like $filter
        """
        items = []
        skip = 0
        batch_size = min(limit, 100)
        
        # Ensure resource name is clean
        resource_name = resource_name.replace(' ', '_')
        
        while len(items) < limit:
            params = {
                '$format': 'json',
                '$top': batch_size,
                '$skip': skip
            }
            if query_params:
                params.update(query_params)

            try:
                url = f"{self.base_url}/{resource_name}"
                response = self.session.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"1C Fetch Error {response.status_code}: {response.text}")
                    break
                    
                data = response.json()
                
                # OData standard wrapper: {'value': [...]}
                value = data.get('value', [])
                if not value:
                    break
                    
                items.extend(value)
                
                if len(value) < batch_size:
                    break
                    
                skip += len(value)
                
            except Exception as e:
                logger.error(f"Error fetching from 1C: {e}")
                break
                
        return pd.DataFrame(items)
