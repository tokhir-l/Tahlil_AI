# Apache Superset Integration Plan for Tahlil Platform

**Document Version:** 1.0  
**Date:** December 26, 2025  
**Status:** Ready for Implementation

---

## 📋 Executive Summary

This document outlines the complete integration strategy for Apache Superset with the Tahlil data science platform. The integration will enable enterprise-grade BI dashboards to be automatically generated from Tahlil's AI-powered analysis results.

---

## 🎯 Integration Objectives

1. **Automatic Dashboard Creation** - Generate Superset dashboards from Tahlil analysis results
2. **Seamless Data Flow** - Direct dataset transfer from Tahlil to Superset
3. **Unified User Experience** - Embed Superset dashboards within Tahlil UI
4. **Enterprise Features** - Enable row-level security, SSO, and audit logging

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface                               │
│                    (Tahlil React Frontend)                          │
└─────────────────────┬───────────────────────┬───────────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────┐   ┌─────────────────────────────────────┐
│      Tahlil Backend         │   │     Superset Dashboard              │
│      (Flask API)            │◄──│     (Embedded iframe)               │
│                             │   └─────────────────────────────────────┘
│  • Analysis Engine          │
│  • Chart Generator          │
│  • KPI Calculator           │
└─────────────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────┐
│   Superset Integration      │
│   Service Layer             │
│                             │
│  • SupersetClient           │
│  • Dataset Manager          │
│  • Dashboard Builder        │
└─────────────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────┐
│   Apache Superset           │
│   (Docker Container)        │
│                             │
│  • REST API (port 8088)     │
│  • PostgreSQL metadata      │
│  • Redis cache              │
└─────────────────────────────┘
```

---

## 📦 Phase 1: Infrastructure Setup (Week 1-2)

### 1.1 Docker Deployment

Create `docker-compose.superset.yml`:

```yaml
version: '3.8'

services:
  # Superset metadata database
  superset-db:
    image: postgres:14
    container_name: tahlil-superset-db
    environment:
      POSTGRES_USER: superset
      POSTGRES_PASSWORD: superset_secret
      POSTGRES_DB: superset
    volumes:
      - superset_db_data:/var/lib/postgresql/data
    networks:
      - tahlil-network
    restart: unless-stopped

  # Redis for caching
  superset-redis:
    image: redis:7
    container_name: tahlil-superset-redis
    networks:
      - tahlil-network
    restart: unless-stopped

  # Apache Superset
  superset:
    image: apache/superset:latest
    container_name: tahlil-superset
    environment:
      - SUPERSET_SECRET_KEY=your_secret_key_change_in_production
      - DATABASE_URL=postgresql://superset:superset_secret@superset-db:5432/superset
      - REDIS_URL=redis://superset-redis:6379/0
      # Enable public dashboard embedding
      - SUPERSET_FEATURE_FLAGS={"EMBEDDED_SUPERSET": true, "DASHBOARD_RBAC": true}
    ports:
      - "8088:8088"
    depends_on:
      - superset-db
      - superset-redis
    volumes:
      - superset_home:/app/superset_home
      - ./superset_config.py:/app/pythonpath/superset_config.py
    networks:
      - tahlil-network
    restart: unless-stopped

  # Tahlil Platform
  tahlil:
    build: .
    container_name: tahlil-app
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPERSET_HOST=http://superset:8088
      - SUPERSET_USERNAME=admin
      - SUPERSET_PASSWORD=admin
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./runs:/app/runs
    networks:
      - tahlil-network
    depends_on:
      - superset
    restart: unless-stopped

volumes:
  superset_db_data:
  superset_home:

networks:
  tahlil-network:
    driver: bridge
```

### 1.2 Superset Configuration

Create `superset_config.py`:

```python
"""
Superset configuration for Tahlil integration
"""
import os
from datetime import timedelta

# Security
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'your_secret_key')
CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365  # 1 year

# Database
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

# Redis cache
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL'),
}

# Feature flags for Tahlil integration
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ALERT_REPORTS": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
}

# Enable CORS for Tahlil frontend
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['http://localhost:5000', 'http://tahlil:5000'],
}

# Public role permissions for embedding
PUBLIC_ROLE_LIKE = "Gamma"

# Session configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# Tahlil-specific database connection
# This will be used to query Tahlil's analysis results
DATABASES = {
    "examples": {
        "allow_ctas": True,
        "allow_cvas": True,
        "allow_dml": True,
        "expose_in_sqllab": True,
    }
}
```

### 1.3 Startup Commands

Create `scripts/init_superset.sh`:

```bash
#!/bin/bash
# Initialize Superset for first-time setup

echo "🚀 Initializing Apache Superset..."

# Initialize database
docker exec tahlil-superset superset db upgrade

# Create admin user
docker exec tahlil-superset superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@tahlil.local \
    --password admin

# Initialize Superset
docker exec tahlil-superset superset init

echo "✅ Superset initialized!"
echo "   Access at: http://localhost:8088"
echo "   Username: admin"
echo "   Password: admin"
```

---

## 🔌 Phase 2: Python Integration Layer (Week 2-3)

### 2.1 Install Dependencies

Add to `requirements.txt`:

```
# Superset Integration
supersetapiclient>=0.5.0
requests>=2.32.0
```

### 2.2 Superset Service Module

Create `tools/superset_integration.py`:

```python
"""
Apache Superset Integration Module for Tahlil Platform

This module provides the bridge between Tahlil's analysis engine
and Apache Superset's visualization capabilities.
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SupersetIntegration:
    """
    Manages all interactions with Apache Superset.
    
    Features:
    - Dataset creation from Tahlil analysis results
    - Automatic chart generation
    - Dashboard building
    - Embedding support
    """
    
    def __init__(
        self,
        host: str = None,
        username: str = None,
        password: str = None
    ):
        """
        Initialize Superset connection.
        
        Args:
            host: Superset host URL (default: from env)
            username: Admin username (default: from env)
            password: Admin password (default: from env)
        """
        self.host = host or os.environ.get('SUPERSET_HOST', 'http://localhost:8088')
        self.username = username or os.environ.get('SUPERSET_USERNAME', 'admin')
        self.password = password or os.environ.get('SUPERSET_PASSWORD', 'admin')
        self.access_token = None
        self.csrf_token = None
        self.session = requests.Session()
        
    def connect(self) -> bool:
        """
        Authenticate with Superset and obtain access token.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Get CSRF token
            csrf_response = self.session.get(
                f"{self.host}/api/v1/security/csrf_token/",
                headers={"Content-Type": "application/json"}
            )
            if csrf_response.status_code == 200:
                self.csrf_token = csrf_response.json().get('result')
            
            # Login
            login_payload = {
                "username": self.username,
                "password": self.password,
                "provider": "db"
            }
            
            response = self.session.post(
                f"{self.host}/api/v1/security/login",
                json=login_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-CSRFToken": self.csrf_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                logger.info("✅ Connected to Superset successfully")
                return True
            else:
                logger.error(f"❌ Superset login failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Superset connection error: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authenticated request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-CSRFToken": self.csrf_token
        }
    
    def create_dataset_from_dataframe(
        self,
        df_json: Dict,
        dataset_name: str,
        database_id: int = 1
    ) -> Optional[int]:
        """
        Create a Superset dataset from Tahlil analysis result.
        
        Args:
            df_json: DataFrame as JSON (from pandas to_dict())
            dataset_name: Name for the dataset
            database_id: Target database ID in Superset
            
        Returns:
            Dataset ID if successful, None otherwise
        """
        try:
            # Step 1: Create a temporary table in the connected database
            # This assumes you have a database connection configured in Superset
            
            payload = {
                "database": database_id,
                "schema": "public",
                "table_name": dataset_name.lower().replace(" ", "_"),
                "owners": [],
                "columns": self._infer_columns(df_json)
            }
            
            response = self.session.post(
                f"{self.host}/api/v1/dataset/",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                dataset_id = response.json().get('id')
                logger.info(f"✅ Created dataset: {dataset_name} (ID: {dataset_id})")
                return dataset_id
            else:
                logger.error(f"❌ Dataset creation failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Dataset creation error: {e}")
            return None
    
    def _infer_columns(self, df_json: Dict) -> List[Dict]:
        """Infer column types from DataFrame JSON."""
        columns = []
        if 'columns' in df_json:
            for col in df_json['columns']:
                columns.append({
                    "column_name": col,
                    "type": "VARCHAR(255)",  # Default, will be refined
                    "filterable": True,
                    "groupby": True
                })
        return columns
    
    def create_chart(
        self,
        dataset_id: int,
        chart_name: str,
        chart_type: str,
        metrics: List[str],
        dimensions: List[str],
        filters: Optional[List[Dict]] = None
    ) -> Optional[int]:
        """
        Create a Superset chart.
        
        Args:
            dataset_id: ID of the dataset to visualize
            chart_name: Name for the chart
            chart_type: Type (bar, line, pie, scatter, etc.)
            metrics: List of metric columns
            dimensions: List of dimension columns
            filters: Optional filters
            
        Returns:
            Chart ID if successful, None otherwise
        """
        try:
            # Map Tahlil chart types to Superset viz types
            viz_type_map = {
                "bar": "echarts_timeseries_bar",
                "line": "echarts_timeseries_line",
                "pie": "pie",
                "scatter": "echarts_scatter",
                "histogram": "histogram",
                "heatmap": "heatmap",
                "table": "table",
                "area": "echarts_area",
                "box": "box_plot"
            }
            
            viz_type = viz_type_map.get(chart_type.lower(), "echarts_timeseries_bar")
            
            payload = {
                "datasource_id": dataset_id,
                "datasource_type": "table",
                "slice_name": chart_name,
                "viz_type": viz_type,
                "params": json.dumps({
                    "metrics": metrics,
                    "groupby": dimensions,
                    "adhoc_filters": filters or [],
                    "row_limit": 10000
                })
            }
            
            response = self.session.post(
                f"{self.host}/api/v1/chart/",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                chart_id = response.json().get('id')
                logger.info(f"✅ Created chart: {chart_name} (ID: {chart_id})")
                return chart_id
            else:
                logger.error(f"❌ Chart creation failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Chart creation error: {e}")
            return None
    
    def create_dashboard(
        self,
        dashboard_name: str,
        chart_ids: List[int],
        layout: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create a Superset dashboard with charts.
        
        Args:
            dashboard_name: Name for the dashboard
            chart_ids: List of chart IDs to include
            layout: Optional custom layout configuration
            
        Returns:
            Dictionary with dashboard info including embed URL
        """
        try:
            # Generate default layout if not provided
            if layout is None:
                layout = self._generate_auto_layout(chart_ids)
            
            payload = {
                "dashboard_title": dashboard_name,
                "slug": dashboard_name.lower().replace(" ", "-"),
                "owners": [],
                "position_json": json.dumps(layout),
                "published": True
            }
            
            response = self.session.post(
                f"{self.host}/api/v1/dashboard/",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                dashboard_data = response.json()
                dashboard_id = dashboard_data.get('id')
                
                # Add charts to dashboard
                for chart_id in chart_ids:
                    self._add_chart_to_dashboard(dashboard_id, chart_id)
                
                result = {
                    "id": dashboard_id,
                    "title": dashboard_name,
                    "url": f"{self.host}/superset/dashboard/{dashboard_id}/",
                    "embed_url": f"{self.host}/superset/dashboard/{dashboard_id}/?standalone=true",
                    "created_at": datetime.now().isoformat()
                }
                
                logger.info(f"✅ Created dashboard: {dashboard_name}")
                return result
            else:
                logger.error(f"❌ Dashboard creation failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Dashboard creation error: {e}")
            return None
    
    def _generate_auto_layout(self, chart_ids: List[int]) -> Dict:
        """Generate automatic dashboard layout."""
        # Simple grid layout
        layout = {
            "DASHBOARD_VERSION_KEY": "v2",
            "ROOT_ID": {
                "type": "ROOT",
                "id": "ROOT_ID",
                "children": ["GRID_ID"]
            },
            "GRID_ID": {
                "type": "GRID",
                "id": "GRID_ID",
                "children": [],
                "parents": ["ROOT_ID"]
            }
        }
        
        # Add chart components
        for i, chart_id in enumerate(chart_ids):
            row = i // 2
            col = i % 2
            component_id = f"CHART-{chart_id}"
            
            layout[component_id] = {
                "type": "CHART",
                "id": component_id,
                "meta": {
                    "chartId": chart_id,
                    "width": 6,
                    "height": 50
                },
                "parents": ["GRID_ID"]
            }
            layout["GRID_ID"]["children"].append(component_id)
        
        return layout
    
    def _add_chart_to_dashboard(self, dashboard_id: int, chart_id: int):
        """Add a chart to an existing dashboard."""
        try:
            response = self.session.put(
                f"{self.host}/api/v1/dashboard/{dashboard_id}/charts/{chart_id}",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error adding chart to dashboard: {e}")
            return False
    
    def create_dashboard_from_analysis(
        self,
        run_id: str,
        analysis_result: Dict,
        dashboard_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create complete dashboard from Tahlil analysis result.
        
        This is the main integration point - takes Tahlil output
        and creates a full Superset dashboard.
        
        Args:
            run_id: Tahlil run ID
            analysis_result: Complete analysis result from Tahlil
            dashboard_name: Optional custom name
            
        Returns:
            Dashboard info dictionary
        """
        try:
            # Generate dashboard name
            if not dashboard_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                dashboard_name = f"Tahlil Analysis - {run_id[:8]} ({timestamp})"
            
            # Connect if not already
            if not self.access_token:
                if not self.connect():
                    return None
            
            # Extract data and charts from analysis
            charts_created = []
            
            # Process each output type
            if 'data' in analysis_result:
                # Create dataset
                dataset_id = self.create_dataset_from_dataframe(
                    analysis_result['data'],
                    f"tahlil_{run_id[:8]}"
                )
                
                if dataset_id:
                    # Create chart based on analysis type
                    chart_config = self._infer_chart_config(analysis_result)
                    chart_id = self.create_chart(
                        dataset_id=dataset_id,
                        chart_name=chart_config['name'],
                        chart_type=chart_config['type'],
                        metrics=chart_config['metrics'],
                        dimensions=chart_config['dimensions']
                    )
                    if chart_id:
                        charts_created.append(chart_id)
            
            # Create dashboard with all charts
            if charts_created:
                return self.create_dashboard(dashboard_name, charts_created)
            else:
                logger.warning("No charts created, skipping dashboard")
                return None
                
        except Exception as e:
            logger.error(f"❌ Dashboard creation from analysis failed: {e}")
            return None
    
    def _infer_chart_config(self, analysis_result: Dict) -> Dict:
        """Infer chart configuration from analysis result."""
        # Default configuration
        config = {
            "name": "Analysis Result",
            "type": "bar",
            "metrics": [],
            "dimensions": []
        }
        
        # Try to extract from Tahlil output
        if 'chart_type' in analysis_result:
            config['type'] = analysis_result['chart_type']
        
        if 'columns' in analysis_result.get('data', {}):
            columns = analysis_result['data']['columns']
            # First column as dimension, rest as metrics
            if len(columns) > 0:
                config['dimensions'] = [columns[0]]
            if len(columns) > 1:
                config['metrics'] = columns[1:]
        
        return config
    
    def get_embed_url(self, dashboard_id: int) -> str:
        """Get embeddable URL for dashboard."""
        return f"{self.host}/superset/dashboard/{dashboard_id}/?standalone=true"
    
    def list_dashboards(self) -> List[Dict]:
        """List all dashboards."""
        try:
            if not self.access_token:
                self.connect()
            
            response = self.session.get(
                f"{self.host}/api/v1/dashboard/",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json().get('result', [])
            return []
        except Exception as e:
            logger.error(f"Error listing dashboards: {e}")
            return []
    
    def delete_dashboard(self, dashboard_id: int) -> bool:
        """Delete a dashboard."""
        try:
            response = self.session.delete(
                f"{self.host}/api/v1/dashboard/{dashboard_id}",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting dashboard: {e}")
            return False


# Convenience function for quick integration
def create_superset_dashboard(
    run_id: str,
    analysis_result: Dict,
    dashboard_name: Optional[str] = None
) -> Optional[Dict]:
    """
    Quick function to create Superset dashboard from Tahlil analysis.
    
    Usage:
        from tools.superset_integration import create_superset_dashboard
        
        result = create_superset_dashboard(
            run_id="abc123",
            analysis_result=tahlil_output,
            dashboard_name="My Sales Analysis"
        )
        
        if result:
            print(f"Dashboard URL: {result['url']}")
    """
    client = SupersetIntegration()
    return client.create_dashboard_from_analysis(
        run_id, analysis_result, dashboard_name
    )
```

---

## 🖥️ Phase 3: Frontend Integration (Week 3-4)

### 3.1 Add Superset Dashboard Component

Create `frontend/components/SupersetDashboard.tsx`:

```tsx
import React, { useState, useEffect } from 'react';

interface SupersetDashboardProps {
  dashboardId: string;
  supersetHost?: string;
}

export const SupersetDashboard: React.FC<SupersetDashboardProps> = ({
  dashboardId,
  supersetHost = 'http://localhost:8088'
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const embedUrl = `${supersetHost}/superset/dashboard/${dashboardId}/?standalone=true`;
  
  return (
    <div className="superset-dashboard-container">
      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      )}
      
      {error && (
        <div className="error-message">
          <p>❌ {error}</p>
          <button onClick={() => setError(null)}>Retry</button>
        </div>
      )}
      
      <iframe
        src={embedUrl}
        className="superset-iframe"
        title="Superset Dashboard"
        onLoad={() => setLoading(false)}
        onError={() => {
          setLoading(false);
          setError('Failed to load dashboard');
        }}
        frameBorder="0"
        width="100%"
        height="800px"
      />
    </div>
  );
};
```

### 3.2 Add Dashboard Gallery

Create `frontend/components/DashboardGallery.tsx`:

```tsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface Dashboard {
  id: string;
  title: string;
  url: string;
  embed_url: string;
  created_at: string;
}

export const DashboardGallery: React.FC = () => {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [selectedDashboard, setSelectedDashboard] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchDashboards();
  }, []);
  
  const fetchDashboards = async () => {
    try {
      const response = await api.listSupersetDashboards();
      setDashboards(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboards:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="dashboard-gallery">
      <h2>📊 Superset Dashboards</h2>
      
      {loading ? (
        <div className="loading">Loading dashboards...</div>
      ) : (
        <div className="dashboard-grid">
          {dashboards.map(dashboard => (
            <div 
              key={dashboard.id}
              className="dashboard-card"
              onClick={() => setSelectedDashboard(dashboard.id)}
            >
              <h3>{dashboard.title}</h3>
              <p>Created: {new Date(dashboard.created_at).toLocaleDateString()}</p>
              <div className="dashboard-actions">
                <button onClick={() => window.open(dashboard.url, '_blank')}>
                  Open in Superset ↗
                </button>
                <button onClick={() => setSelectedDashboard(dashboard.id)}>
                  View Embedded
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {selectedDashboard && (
        <div className="dashboard-modal">
          <button onClick={() => setSelectedDashboard(null)}>✕ Close</button>
          <SupersetDashboard dashboardId={selectedDashboard} />
        </div>
      )}
    </div>
  );
};
```

### 3.3 Add CSS Styles

Add to `frontend/styles.css`:

```css
/* Superset Dashboard Styles */
.superset-dashboard-container {
  position: relative;
  width: 100%;
  min-height: 600px;
  background: var(--bg-secondary);
  border-radius: 12px;
  overflow: hidden;
}

.superset-iframe {
  width: 100%;
  height: 800px;
  border: none;
  border-radius: 8px;
}

.dashboard-gallery {
  padding: 2rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.dashboard-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.dashboard-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.dashboard-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.dashboard-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 1000;
  padding: 2rem;
  overflow: auto;
}
```

---

## 🔗 Phase 4: API Endpoints (Week 4)

### 4.1 Add Superset Endpoints to app.py

```python
# Add to app.py

from tools.superset_integration import SupersetIntegration

superset_client = SupersetIntegration()

# =============================================================================
# SUPERSET INTEGRATION ENDPOINTS
# =============================================================================

@app.route('/api/superset/connect', methods=['POST'])
def superset_connect():
    """Test Superset connection."""
    try:
        success = superset_client.connect()
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/superset/dashboards', methods=['GET'])
def list_superset_dashboards():
    """List all Superset dashboards."""
    try:
        dashboards = superset_client.list_dashboards()
        return jsonify({"dashboards": dashboards})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/superset/dashboard', methods=['POST'])
def create_superset_dashboard():
    """Create Superset dashboard from Tahlil run."""
    try:
        data = request.json
        run_id = data.get('run_id')
        dashboard_name = data.get('name')
        
        # Get run results
        run_dir = Path(f"runs/{run_id}")
        final_output = run_dir / "final_output" / "output.json"
        
        if not final_output.exists():
            return jsonify({"error": "Run results not found"}), 404
        
        with open(final_output) as f:
            analysis_result = json.load(f)
        
        result = superset_client.create_dashboard_from_analysis(
            run_id, analysis_result, dashboard_name
        )
        
        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "Dashboard creation failed"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/superset/dashboard/<dashboard_id>', methods=['DELETE'])
def delete_superset_dashboard(dashboard_id):
    """Delete a Superset dashboard."""
    try:
        success = superset_client.delete_dashboard(int(dashboard_id))
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/superset/embed/<dashboard_id>', methods=['GET'])
def get_embed_url(dashboard_id):
    """Get embeddable URL for dashboard."""
    try:
        url = superset_client.get_embed_url(int(dashboard_id))
        return jsonify({"embed_url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

## ✅ Phase 5: Testing & Validation (Week 5)

### 5.1 Test Checklist

- [ ] Docker Compose starts all services
- [ ] Superset admin login works
- [ ] API authentication succeeds
- [ ] Dataset creation works
- [ ] Chart creation works
- [ ] Dashboard creation works
- [ ] Frontend embedding works
- [ ] Dashboard gallery loads
- [ ] End-to-end: Tahlil analysis → Superset dashboard

### 5.2 Test Script

Create `tests/test_superset_integration.py`:

```python
"""
Tests for Superset integration
"""
import pytest
from tools.superset_integration import SupersetIntegration

@pytest.fixture
def superset_client():
    return SupersetIntegration()

def test_connection(superset_client):
    """Test Superset connection."""
    assert superset_client.connect() == True

def test_list_dashboards(superset_client):
    """Test listing dashboards."""
    superset_client.connect()
    dashboards = superset_client.list_dashboards()
    assert isinstance(dashboards, list)

def test_dashboard_creation(superset_client):
    """Test creating a dashboard from analysis."""
    superset_client.connect()
    
    mock_analysis = {
        "data": {
            "columns": ["Category", "Revenue", "Count"],
            "records": [
                {"Category": "A", "Revenue": 1000, "Count": 10},
                {"Category": "B", "Revenue": 2000, "Count": 20},
            ]
        },
        "chart_type": "bar"
    }
    
    result = superset_client.create_dashboard_from_analysis(
        "test123",
        mock_analysis,
        "Test Dashboard"
    )
    
    assert result is not None
    assert "url" in result
```

---

## 📅 Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Infrastructure | Docker Compose, Superset deployment, config |
| 2-3 | Python Layer | SupersetIntegration class, API bridge |
| 3-4 | Frontend | Dashboard components, gallery, embedding |
| 4 | API Endpoints | REST endpoints in app.py |
| 5 | Testing | Integration tests, end-to-end validation |
| 6 | Polish | Documentation, error handling, optimization |

---

## 🔧 Maintenance & Operations

### Health Check Endpoint

```python
@app.route('/api/superset/health', methods=['GET'])
def superset_health():
    """Check Superset service health."""
    try:
        response = requests.get(f"{SUPERSET_HOST}/health", timeout=5)
        return jsonify({
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "superset_version": response.json().get("version", "unknown")
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503
```

### Logging Configuration

```python
# Add to superset_integration.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SUPERSET] %(levelname)s: %(message)s'
)
```

---

## 📚 Resources

- [Apache Superset Documentation](https://superset.apache.org/docs/intro)
- [Superset REST API Reference](https://superset.apache.org/docs/rest-api)
- [Superset Docker Deployment](https://superset.apache.org/docs/installation/docker-compose)
- [supersetapiclient Python Package](https://pypi.org/project/supersetapiclient/)

---

*This implementation plan is designed for the Tahlil Platform v1.0*
*Last Updated: December 26, 2025*
