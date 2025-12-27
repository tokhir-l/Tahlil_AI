"""
Tahlil Web Application Backend API
Provides REST API endpoints for the frontend to interact with Tahlil
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from pathlib import Path
import json
import os
import subprocess
import threading
from datetime import datetime
import uuid
from typing import Dict, List
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# API CONFIGURATION
# ============================================================================
# Load API keys from environment variables
# IMPORTANT: Never hardcode API keys in source code!
# Set them as environment variables or use a .env file
# 
# Required: GEMINI_API_KEY
# Optional: OPENAI_API_KEY, OLLAMA_HOST
#
# Option 1: Environment variable
#   Windows (PowerShell): $env:GEMINI_API_KEY = "your-api-key"
#   Windows (CMD): set GEMINI_API_KEY=your-api-key
#   Linux/Mac: export GEMINI_API_KEY="your-api-key"
#
# Option 2: .env file (recommended)
#   Create a .env file in the project root with:
#   GEMINI_API_KEY=your-api-key-here
#   Get your API key from: https://aistudio.google.com/app/apikey

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ Loaded environment variables from .env file (if present)")
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

# Load API key from multiple sources (in order of priority):
# 1. Environment variable (highest priority)
# 2. gemini_api_key.txt file
# 3. .env file (already loaded above if python-dotenv is installed)

api_key = None

# Priority 1: Environment variable
if os.environ.get('GEMINI_API_KEY'):
    api_key = os.environ.get('GEMINI_API_KEY')
    logger.info("✅ GEMINI_API_KEY loaded from environment variable")

# Priority 2: gemini_api_key.txt file
if not api_key:
    api_key_file = Path('gemini_api_key.txt')
    if api_key_file.exists():
        try:
            # Try reading with explicit encoding
            with open(api_key_file, 'r', encoding='utf-8') as f:
                api_key = f.read().strip()
            
            # Also try reading as bytes and decoding (handles BOM and encoding issues)
            if not api_key:
                with open(api_key_file, 'rb') as f:
                    raw_content = f.read()
                    # Try to decode, removing BOM if present
                    if raw_content.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
                        api_key = raw_content[3:].decode('utf-8').strip()
                    else:
                        api_key = raw_content.decode('utf-8', errors='ignore').strip()
            
            if api_key:
                os.environ['GEMINI_API_KEY'] = api_key
                logger.info("✅ GEMINI_API_KEY loaded from gemini_api_key.txt file")
            else:
                logger.warning("⚠️  gemini_api_key.txt file exists but is empty or contains only whitespace")
        except Exception as e:
            logger.warning(f"Could not read gemini_api_key.txt: {e}")
            logger.warning(f"File path: {api_key_file.resolve()}")

# Validate API key is set
if not api_key:
    logger.error("=" * 70)
    logger.error("❌ GEMINI_API_KEY is not set!")
    logger.error("=" * 70)
    logger.error("Please set your Gemini API key using one of these methods:")
    logger.error("")
    logger.error("Method 1: gemini_api_key.txt file (Easiest)")
    logger.error("  Create a file named 'gemini_api_key.txt' in the project root")
    logger.error("  Put your API key on the first line (no quotes, no spaces)")
    logger.error("")
    logger.error("Method 2: Environment Variable")
    logger.error("  Windows (PowerShell): $env:GEMINI_API_KEY = 'your-api-key'")
    logger.error("  Windows (CMD):        set GEMINI_API_KEY=your-api-key")
    logger.error("  Linux/Mac:           export GEMINI_API_KEY='your-api-key'")
    logger.error("")
    logger.error("Method 3: .env File")
    logger.error("  Create a .env file in the project root with:")
    logger.error("  GEMINI_API_KEY=your-api-key-here")
    logger.error("")
    logger.error("Get your API key from: https://aistudio.google.com/app/apikey")
    logger.error("=" * 70)
    raise ValueError("GEMINI_API_KEY is required. Please set it using one of the methods above.")
else:
    logger.info("✅ GEMINI_API_KEY is set (length: {})".format(len(api_key)))

# Check if React build exists, otherwise serve from frontend source
FRONTEND_DIST = Path('frontend/dist')
FRONTEND_SOURCE = Path('frontend')

# Don't use static_folder - we'll handle file serving manually to block TypeScript files
app = Flask(__name__)
CORS(app)

if FRONTEND_DIST.exists() and (FRONTEND_DIST / 'index.html').exists():
    logger.info("✅ React app found in frontend/dist (production build)")
else:
    logger.warning("⚠️  React app not built!")
    logger.warning("   Flask cannot serve TypeScript files directly.")
    logger.warning("   Options:")
    logger.warning("   1. Build React: cd frontend && npm install && npm run build")
    logger.warning("   2. Use Vite dev server: cd frontend && npm run dev (port 3000)")

# Configuration
DATA_DIR = Path("data")
RUNS_DIR = Path("runs")
TEMP_DIR = Path("temp")
DATA_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Import storage manager
from storage import StorageManager
storage_manager = StorageManager(DATA_DIR)

# Import new services
from file_validator import FileValidator
from chart_generator import ChartGenerator, ChartConfig
from kpi_calculator import KPICalculator
from tools.sql_generator import SQLGenerator, dataframe_to_sql
from tools.spreadsheet_connector import SpreadsheetConnector, fetch_spreadsheet

# Add required imports for new services
import pandas as pd
try:
    import plotly.graph_objects as go
    import plotly.offline as pyo
except ImportError:
    logger.warning("plotly not installed. Chart generation will use fallback.")
    go = None
    pyo = None

# Initialize new services
file_validator = FileValidator(DATA_DIR)
chart_generator = ChartGenerator()
kpi_calculator = KPICalculator()

# Initialize spreadsheet connector (credentials path is optional)
google_credentials_path = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'config/google_credentials.json')
if Path(google_credentials_path).exists():
    spreadsheet_connector = SpreadsheetConnector(google_credentials_path)
    logger.info("✅ SpreadsheetConnector initialized with Google credentials")
else:
    spreadsheet_connector = SpreadsheetConnector()
    logger.info("ℹ️  SpreadsheetConnector initialized without credentials (public sheets only)")

# In-memory store for run status
run_status: Dict[str, Dict] = {}

# In-memory store for process objects (for cancellation)
run_processes: Dict[str, subprocess.Popen] = {}

# =============================================================================
# DATA MANAGEMENT ENDPOINTS
# =============================================================================


@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    """Upload a new data file with deduplication and quota checking."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'success': False}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No file selected', 'success': False}), 400
        
        # Get user_id from request (default to 'default' for now)
        user_id = request.form.get('user_id', 'default')
        
        # Read file content
        file_content = file.read()
        filename = file.filename
        
        # Store file using storage manager
        file_info = storage_manager.store_file(file_content, filename, user_id)
        
        logger.info(f"File uploaded: {filename} (ID: {file_info['id']}, Duplicate: {file_info.get('is_duplicate', False)})")
        
        return jsonify({
            'success': True,
            'file': {
                'id': file_info['id'],
                'name': file_info['original_filename'],
                'size': file_info['file_size'],
                'is_duplicate': file_info.get('is_duplicate', False),
                'message': 'File already exists (deduplicated)' if file_info.get('is_duplicate') else 'File uploaded successfully'
            }
        })
    except ValueError as e:
        # Validation errors (size, type, quota)
        logger.warning(f"File upload validation failed: {e}")
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/data/list', methods=['GET'])
def list_data():
    """List all data files for the current user."""
    try:
        user_id = request.args.get('user_id', 'default')
        
        files = storage_manager.list_files(user_id)
        
        # Format files for response
        file_list = []
        for file_info in files:
            file_list.append({
                'id': file_info['id'],
                'name': file_info['original_filename'],
                'size': file_info['file_size'],
                'type': file_info.get('file_type', ''),
                'uploaded_at': file_info.get('upload_date', ''),
                'stored_filename': file_info.get('stored_filename', '')
            })
        
        return jsonify({
            'success': True,
            'files': file_list
        })
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/data/delete/<int:file_id>', methods=['DELETE'])
def delete_data(file_id):
    """Delete a data file by ID."""
    try:
        user_id = request.args.get('user_id', 'default')
        
        success = storage_manager.delete_file(file_id, user_id)
        
        if success:
            logger.info(f"File deleted: {file_id} for user {user_id}")
            return jsonify({'success': True, 'message': f'File deleted successfully'})
        else:
            return jsonify({'error': 'File not found or access denied', 'success': False}), 404
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/data/preview/<int:file_id>', methods=['GET'])
def preview_data(file_id):
    """Preview a data file (first few rows and structure)."""
    try:
        user_id = request.args.get('user_id', 'default')
        rows = int(request.args.get('rows', 5))
        
        preview = storage_manager.preview_file(file_id, user_id, rows)
        
        if preview:
            return jsonify({'success': True, 'preview': preview})
        else:
            return jsonify({'error': 'File not found or access denied', 'success': False}), 404
    except Exception as e:
        logger.error(f"Error previewing file: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

# =============================================================================
# DATA SOURCE INTEGRATION ENDPOINTS
# =============================================================================

@app.route('/api/data/from-link', methods=['POST'])
def fetch_from_link():
    """
    Fetch data from external link (Google Sheets, Excel Online, etc.)
    
    Request body:
    {
        "url": "https://docs.google.com/spreadsheets/d/...",
        "source_type": "spreadsheet",  # optional
        "worksheet_name": "Sheet1",    # optional
        "user_id": "default"           # optional
    }
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
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error
            }), 400
        
        # Convert DataFrame to CSV and store like a regular file
        df = result.data
        csv_content = df.to_csv(index=False).encode('utf-8')
        
        # Generate filename from metadata
        sheet_id = result.metadata.get('sheet_id', 'sheet')[:12]
        filename = f"gsheet_{sheet_id}.csv"
        
        # Store using existing storage manager
        file_info = storage_manager.store_file(csv_content, filename, user_id)
        
        # Add metadata about the link source
        file_info['source_url'] = url
        file_info['source_type'] = source_type
        file_info['fetched_at'] = datetime.now().isoformat()
        
        logger.info(f"Data fetched from link: {url} (rows: {result.metadata.get('rows', 0)})")
        
        return jsonify({
            'success': True,
            'file': {
                'id': file_info['id'],
                'name': file_info['original_filename'],
                'size': file_info['file_size'],
                'source_url': url,
                'source_type': result.metadata.get('source_type', 'spreadsheet')
            },
            'preview': df.head(5).to_dict('records'),  # First 5 rows
            'metadata': result.metadata
        })
        
    except ValueError as e:
        logger.warning(f"Link fetch validation failed: {e}")
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        logger.error(f"Error fetching from link: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/data/sources', methods=['GET'])
def list_data_sources():
    """Get list of supported data source types."""
    platforms = spreadsheet_connector.get_supported_platforms()
    return jsonify({
        'success': True,
        'sources': platforms
    })


@app.route('/api/data/from-api', methods=['POST'])
def fetch_from_api():
    """
    Fetch data from external REST API.
    
    Request body:
    {
        "url": "https://api.example.com/data",
        "method": "GET",  # or "POST"
        "auth_type": "none",  # or "api_key", "bearer", "basic"
        "auth_config": {},  # Auth-specific config
        "headers": {},  # Additional headers
        "params": {},  # Query parameters
        "body": {},  # Request body for POST
        "json_path": "data.items",  # Path to data in response
        "user_id": "default"
    }
    """
    try:
        from tools.api_connector import APIConnector
        
        data = request.json
        url = data.get('url')
        method = data.get('method', 'GET')
        auth_type = data.get('auth_type', 'none')
        auth_config = data.get('auth_config', {})
        headers = data.get('headers', {})
        params = data.get('params', {})
        body = data.get('body')
        json_path = data.get('json_path')
        user_id = data.get('user_id', 'default')
        
        if not url:
            return jsonify({'error': 'URL is required', 'success': False}), 400
        
        # Fetch data from API
        connector = APIConnector()
        result = connector.fetch_from_url(
            url=url,
            method=method,
            auth_type=auth_type,
            auth_config=auth_config,
            headers=headers,
            params=params,
            body=body,
            json_path=json_path
        )
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error
            }), 400
        
        # Convert DataFrame to CSV and store
        df = result.data
        csv_content = df.to_csv(index=False).encode('utf-8')
        
        # Generate filename from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('.', '_')[:20]
        filename = f"api_{domain}.csv"
        
        # Store using existing storage manager
        file_info = storage_manager.store_file(csv_content, filename, user_id)
        
        logger.info(f"Data fetched from API: {url} (rows: {result.metadata.get('rows', 0)})")
        
        return jsonify({
            'success': True,
            'file': {
                'id': file_info['id'],
                'name': file_info['original_filename'],
                'size': file_info['file_size'],
                'source_url': url,
                'source_type': 'api'
            },
            'preview': df.head(5).to_dict('records'),
            'metadata': result.metadata
        })
        
    except ValueError as e:
        logger.warning(f"API fetch validation failed: {e}")
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        logger.error(f"Error fetching from API: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/data/auth-types', methods=['GET'])
def get_auth_types():
    """Get list of supported authentication types for APIs."""
    from tools.api_connector import APIConnector
    return jsonify({
        'success': True,
        'auth_types': APIConnector.get_supported_auth_types()
    })


# =============================================================================
# QUERY & RUN ENDPOINTS
# =============================================================================


@app.route('/api/run/start', methods=['POST'])
def start_run():
    """Start a new Tahlil analysis run."""
    try:
        data = request.json
        query = data.get('query', '')
        file_ids = data.get('file_ids', [])  # Changed from 'files' to 'file_ids'
        model = data.get('model', 'gemini-2.5-flash')
        max_rounds = data.get('max_refinement_rounds', 3)
        user_id = data.get('user_id', 'default')
        
        if not query:
            return jsonify({'error': 'Query is required', 'success': False}), 400
        if not file_ids:
            return jsonify({'error': 'At least one data file is required', 'success': False}), 400
        
        # Convert file IDs to actual file paths
        file_paths = []
        file_names = []
        user_files = storage_manager.list_files(user_id)
        
        for file_id in file_ids:
            # Find file by ID
            file_info = next((f for f in user_files if f['id'] == file_id), None)
            if not file_info:
                return jsonify({'error': f'File ID {file_id} not found or access denied', 'success': False}), 404
            
            # Use stored filename (hash-based) for actual file path
            # Files are stored in data/files/ directory
            file_paths.append(file_info['stored_filename'])
            file_names.append(file_info['original_filename'])
        
        # Generate run ID
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{uuid.uuid4().hex[:6]}"
        
        # Create run directory
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save run metadata
        metadata = {
            'run_id': run_id,
            'query': query,
            'file_ids': file_ids,
            'file_names': file_names,
            'model': model,
            'max_refinement_rounds': max_rounds,
            'status': 'running',
            'created_at': datetime.now().isoformat(),
            'started_at': datetime.now().isoformat()
        }
        
        with open(run_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Store in memory
        run_status[run_id] = metadata.copy()
        
        # Start Tahlil in background thread
        thread = threading.Thread(
            target=run_tahlil_pipeline,
            args=(run_id, query, file_paths, model, max_rounds)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Run started: {run_id}")
        return jsonify({'success': True, 'run_id': run_id})
    except Exception as e:
        logger.error(f"Error starting run: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

def run_tahlil_pipeline(run_id: str, query: str, files: List[str], model: str, max_rounds: int):
    """Execute Tahlil pipeline in background."""
    try:
        run_status[run_id]['status'] = 'running'
        run_status[run_id]['progress'] = 0
        
        # Create a temporary config for this run
        # Note: Files are stored in data/files/ with hash-based names
        # tahlil.py will look in data_dir, so we use 'data/files' as data_dir
        run_config = {
            'run_id': run_id,
            'model_name': model,
            'query': query,
            'max_refinement_rounds': max_rounds,
            'interactive': False,
            'preserve_artifacts': True,
            'runs_dir': 'runs',
            'data_dir': 'data/files'  # Storage manager stores files here
        }
        
        # Save run config
        run_config_path = f'runs/{run_id}/config.yaml'
        os.makedirs(f'runs/{run_id}', exist_ok=True)
        with open(run_config_path, 'w') as f:
            yaml.dump(run_config, f)
        
        # Build command
        cmd = [
            'python', 'tahlil.py',
            '--query', query,
            '--config', run_config_path,
            '--max-rounds', str(max_rounds),
        ]
        
        for file in files:
            # Pass stored filename (hash-based) - tahlil.py will find it in data/files/
            cmd.extend(['--data-files', file])  # Pass stored filename (hash-based)
        
        # Execute (use Popen instead of run to store process)
        # Pass environment variables to ensure API keys are available
        env = os.environ.copy()
        
        # CRITICAL: Ensure API key is in subprocess environment
        # Get API key from Flask's environment
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment for subprocess!")
            raise ValueError("GEMINI_API_KEY environment variable is required for analysis runs.")
        
        env['GEMINI_API_KEY'] = api_key
        logger.info(f"Subprocess API key set: {api_key[:10]}... (length: {len(api_key)})")
        
        # Log command for debugging
        logger.info(f"Executing command: {' '.join(cmd)}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Data files: {files}")
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            env=env,
            cwd=os.getcwd(),  # Ensure we're in the right directory
            shell=False
        )
        logger.info(f"Subprocess started with PID: {process.pid}")
        run_processes[run_id] = process
        
        # Wait for completion
        try:
            stdout, stderr = process.communicate(timeout=3600)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            run_status[run_id]['status'] = 'timeout'
            run_status[run_id]['error'] = 'Analysis timed out after 1 hour'
            logger.error(f"Run timed out: {run_id}")
        except Exception as e:
            logger.error(f"Error waiting for process: {e}")
            run_status[run_id]['status'] = 'error'
            run_status[run_id]['error'] = str(e)
            stderr = str(e)
            stdout = ""
        
        # Remove from active processes
        if run_id in run_processes:
            del run_processes[run_id]
        
        # Log output for debugging
        if stdout:
            logger.info(f"Run {run_id} stdout (first 500 chars): {stdout[:500]}")
        if stderr:
            logger.warning(f"Run {run_id} stderr: {stderr[:500]}")
        
        if process.returncode == 0:
            run_status[run_id]['status'] = 'completed'
            run_status[run_id]['progress'] = 100
            logger.info(f"Run completed successfully: {run_id}")
        else:
            run_status[run_id]['status'] = 'failed'
            run_status[run_id]['error'] = stderr[:1000] if stderr else "Unknown error"
            logger.error(f"Run failed: {run_id} (return code: {process.returncode})")
            logger.error(f"Error output: {stderr[:500] if stderr else 'No stderr'}")
        
        run_status[run_id]['finished_at'] = datetime.now().isoformat()
        
        # IMPORTANT: Persist status to metadata.json so it survives app restart
        try:
            run_dir = Path('runs') / run_id
            metadata_file = run_dir / 'metadata.json'
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            # Update metadata with final status
            metadata.update(run_status[run_id])
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Status persisted to disk for run: {run_id}")
        except Exception as e:
            logger.error(f"Failed to persist status to disk: {e}")
    except Exception as e:
        # Clean up process if exception occurs
        if run_id in run_processes:
            try:
                run_processes[run_id].terminate()
                run_processes[run_id].wait(timeout=5)
            except:
                run_processes[run_id].kill()
            del run_processes[run_id]
        
        run_status[run_id]['status'] = 'error'
        run_status[run_id]['error'] = str(e)
        logger.error(f"Pipeline error: {e}")

@app.route('/api/run/<run_id>/status', methods=['GET'])
def get_run_status(run_id):
    """Get the status of a run."""
    try:
        if run_id in run_status:
            return jsonify({'success': True, 'data': run_status[run_id]})
        else:
            # Try to load from disk
            run_dir = RUNS_DIR / run_id
            metadata_file = run_dir / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                return jsonify({'success': True, 'data': data})
            else:
                return jsonify({'error': 'Run not found', 'success': False}), 404
    except Exception as e:
        logger.error(f"Error getting run status: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/run/<run_id>/progress', methods=['GET'])
def get_run_progress(run_id):
    """Get detailed progress of a run."""
    try:
        run_dir = RUNS_DIR / run_id
        progress_file = run_dir / 'progress.json'
        
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            return jsonify({'success': True, 'data': progress_data})
        else:
            # Return empty progress if file doesn't exist yet
            return jsonify({'success': True, 'data': {
                'run_id': run_id,
                'total_steps': 0,
                'completed_steps': 0,
                'current_phase': None,
                'steps': []
            }})
    except Exception as e:
        logger.error(f"Error getting run progress: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/run/<run_id>/cancel', methods=['POST'])
def cancel_run(run_id):
    """Cancel an ongoing run."""
    try:
        if run_id not in run_status:
            return jsonify({'error': 'Run not found', 'success': False}), 404
        
        run = run_status[run_id]
        
        # Can only cancel running or queued runs
        if run['status'] not in ['running', 'queued']:
            return jsonify({
                'error': f'Cannot cancel run with status: {run["status"]}',
                'success': False
            }), 400
        
        # Terminate the process
        if run_id in run_processes:
            try:
                process = run_processes[run_id]
                logger.info(f"Terminating process for run {run_id}")
                process.terminate()
                
                # Wait for graceful shutdown (5 seconds)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if doesn't terminate gracefully
                    logger.warning(f"Force killing process for run {run_id}")
                    process.kill()
                    process.wait()
                
                del run_processes[run_id]
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
        
        # Update status
        run['status'] = 'cancelled'
        run['finished_at'] = datetime.now().isoformat()
        
        logger.info(f"Run cancelled: {run_id}")
        return jsonify({
            'success': True,
            'message': f'Run {run_id} has been cancelled'
        })
    
    except Exception as e:
        logger.error(f"Error cancelling run: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/run/<run_id>/results', methods=['GET'])
def get_run_results(run_id):
    """Get the final results of a run."""
    try:
        run_dir = RUNS_DIR / run_id
        final_output_dir = run_dir / 'final_output'
        
        if not final_output_dir.exists():
            return jsonify({'error': 'No results yet', 'success': False}), 404
        
        results = {
            'output': None,
            'files': []
        }
        
        # Read result.json for output
        result_file = final_output_dir / 'result.json'
        if result_file.exists():
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    logger.info(f"Reading result.json for run {run_id}, content length: {len(content)}")
                    if content:
                        try:
                            # Try to parse as JSON
                            parsed = json.loads(content)
                            results['output'] = parsed
                            logger.info(f"Successfully parsed JSON for run {run_id}")
                        except json.JSONDecodeError as e:
                            # Not valid JSON, return as string
                            logger.warning(f"result.json is not valid JSON for run {run_id}: {e}")
                            logger.warning(f"Content preview: {content[:200]}")
                            results['output'] = content
                    else:
                        # Empty file
                        results['output'] = None
                        logger.warning(f"result.json is empty for run {run_id}")
            except Exception as e:
                logger.error(f"Error reading result.json for run {run_id}: {e}")
                results['output'] = None
        else:
            logger.warning(f"result.json does not exist for run {run_id}")
        
        # List all files in final_output directory
        for file in final_output_dir.iterdir():
            if file.is_file() and file.name != 'result.json':
                results['files'].append(file.name)
        
        # If output is None or empty, try to get the last execution result from steps
        if not results['output'] or (isinstance(results['output'], str) and not results['output'].strip()):
            try:
                steps_dir = run_dir / 'steps'
                if steps_dir.exists():
                    # Get the last step with a result
                    step_dirs = sorted([d for d in steps_dir.iterdir() if d.is_dir()], 
                                      key=lambda x: x.name, reverse=True)
                    for step_dir in step_dirs:
                        result_file = step_dir / 'result.txt'
                        if result_file.exists():
                            with open(result_file, 'r', encoding='utf-8') as f:
                                step_result = f.read().strip()
                                if step_result:
                                    # Use the last non-empty step result as fallback
                                    results['output'] = step_result
                                    logger.info(f"Using step result as fallback for run {run_id}")
                                    break
            except Exception as e:
                logger.warning(f"Could not get fallback result from steps: {e}")
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/humanize', methods=['POST'])
def humanize_data():
    """Humanize technical data for non-technical users using AI."""
    try:
        data = request.json
        technical_data = data.get('data')
        context = data.get('context', '')
        
        if not technical_data:
            return jsonify({'error': 'No data provided', 'success': False}), 400
        
        # Import provider to use AI for humanization
        from provider import GeminiProvider
        
        # Get API key from environment
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return jsonify({'error': 'API key not configured', 'success': False}), 500
        
        # Use a lightweight model for humanization
        provider = GeminiProvider(api_key, 'gemini-2.0-flash')
        
        # Create prompt for humanization
        prompt = f"""You are a helpful assistant that converts technical data into natural, easy-to-understand language for non-technical users.

Context: {context}

Technical data:
{json.dumps(technical_data, indent=2) if isinstance(technical_data, (dict, list)) else str(technical_data)}

Your task:
Convert this technical data into clear, natural language that a non-technical person can easily understand. 
- Use simple, everyday words
- Avoid technical jargon
- Make it conversational and friendly
- If it's a list of items, describe each item naturally
- If it's data about people/employees, describe them as if telling a story
- Keep it concise but informative

Output only the humanized text, nothing else:"""
        
        humanized = provider.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'humanized': humanized.strip()
        })
    except Exception as e:
        logger.error(f"Error humanizing data: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/run/<run_id>/steps', methods=['GET'])
def get_run_steps(run_id):
    """Get all steps from a run in ProcessStep format."""
    try:
        run_dir = RUNS_DIR / run_id
        progress_file = run_dir / 'progress.json'
        
        # Get step directories (these have the actual code/prompt/result)
        steps_dir = run_dir / 'steps'
        step_dirs_list = []
        if steps_dir.exists():
            for step_dir in sorted(steps_dir.iterdir()):
                if step_dir.is_dir():
                    step_dirs_list.append(step_dir)
        
        # Get progress.json for status and additional info
        progress_steps_map = {}
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                progress_steps = progress_data.get('steps', [])
                # Create a map by name for quick lookup
                for ps in progress_steps:
                    progress_steps_map[ps.get('name', '')] = ps
        
        # Build formatted steps from step directories (these have step_id)
        formatted_steps = []
        for step_dir in step_dirs_list:
            step_id = step_dir.name
            metadata_file = step_dir / 'metadata.json'
            
            # Get step info from metadata
            step_type = 'unknown'
            timestamp = datetime.now().isoformat()
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        step_type = metadata.get('step_type', step_id.split('_')[1] if '_' in step_id else 'unknown')
                        timestamp = metadata.get('timestamp', timestamp)
                except:
                    pass
            
            # Determine phase from step number
            step_num = int(step_id.split('_')[0]) if step_id.split('_')[0].isdigit() else 0
            phase = 'PHASE 2'
            if step_num == 0:
                phase = 'PHASE 1'
            elif 'finalizer' in step_type.lower():
                phase = 'PHASE 3'
            
            # Get status from result file or progress.json
            result_file = step_dir / 'result.txt'
            status = 'completed'
            message = ''
            if result_file.exists():
                try:
                    with open(result_file, 'r') as f:
                        result = f.read()
                        if 'error' in result.lower() or 'Error' in result or 'failed' in result.lower():
                            status = 'failed'
                        message = result[:200] if result else ''
                except:
                    pass
            
            # Try to get status from progress.json
            step_name = step_type.replace('_', ' ').title()
            if step_name in progress_steps_map:
                ps = progress_steps_map[step_name]
                status = ps.get('status', status)
                if ps.get('message'):
                    message = ps.get('message', message)
            
            formatted_step = {
                'step_id': step_id,
                'name': step_name,
                'phase': phase,
                'status': status,
                'timestamp': timestamp,
                'message': message
            }
            formatted_steps.append(formatted_step)
        
        # Also add progress steps that don't have corresponding step directories (like "Executing generated code", "Verifying results")
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                progress_steps = progress_data.get('steps', [])
                for ps in progress_steps:
                    ps_name = ps.get('name', '')
                    # Only add if it's not already in formatted_steps (check by name similarity)
                    if not any(ps_name.lower() in fs.get('name', '').lower() or fs.get('name', '').lower() in ps_name.lower() for fs in formatted_steps):
                        formatted_step = {
                            'step_id': '',  # No step directory for these
                            'name': ps_name,
                            'phase': ps.get('phase', 'PHASE 2'),
                            'status': ps.get('status', 'completed'),
                            'timestamp': ps.get('timestamp', datetime.now().isoformat()),
                            'message': ps.get('message', '')
                        }
                        formatted_steps.append(formatted_step)
        
        # Sort by timestamp or step number
        formatted_steps.sort(key=lambda x: (
            int(x['step_id'].split('_')[0]) if x['step_id'] and x['step_id'].split('_')[0].isdigit() else 999,
            x.get('timestamp', '')
        ))
        
        return jsonify({'success': True, 'steps': formatted_steps})
        
        # Fallback: construct steps from step directories
        steps_dir = run_dir / 'steps'
        if not steps_dir.exists():
            return jsonify({'success': True, 'steps': []})
        
        formatted_steps = []
        for step_dir in sorted(steps_dir.iterdir()):
            if step_dir.is_dir():
                metadata_file = step_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    step_id = step_dir.name
                    step_type = metadata.get('step_type', step_id.split('_')[1] if '_' in step_id else 'unknown')
                    step_num = int(step_id.split('_')[0]) if step_id.split('_')[0].isdigit() else 0
                    
                    # Determine phase
                    phase = 'PHASE 2'
                    if step_num == 0:
                        phase = 'PHASE 1'
                    elif 'finalizer' in step_type.lower():
                        phase = 'PHASE 3'
                    
                    # Determine status
                    result_file = step_dir / 'result.txt'
                    status = 'completed'
                    if result_file.exists():
                        with open(result_file, 'r') as f:
                            result = f.read()
                            if 'error' in result.lower() or 'Error' in result or 'failed' in result.lower():
                                status = 'failed'
                    
                    formatted_step = {
                        'step_id': step_id,
                        'name': step_type.replace('_', ' ').title(),
                        'phase': phase,
                        'status': status,
                        'timestamp': metadata.get('timestamp', datetime.now().isoformat()),
                        'message': ''
                    }
                    
                    # Add message from result if available
                    if result_file.exists():
                        with open(result_file, 'r') as f:
                            result = f.read()
                            if result:
                                formatted_step['message'] = result[:200]  # First 200 chars
                    
                    formatted_steps.append(formatted_step)
        
        return jsonify({'success': True, 'steps': formatted_steps})
    except Exception as e:
        logger.error(f"Error getting steps: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/run/<run_id>/step/<step_id>/details', methods=['GET'])
def get_step_details(run_id, step_id):
    """Get detailed information for a specific step (code, prompt, full result)."""
    try:
        run_dir = RUNS_DIR / run_id
        step_dir = run_dir / 'steps' / step_id
        
        if not step_dir.exists():
            return jsonify({'error': 'Step not found', 'success': False}), 404
        
        details = {
            'step_id': step_id,
            'code': None,
            'prompt': None,
            'result': None,
            'metadata': None
        }
        
        # Read code.py if exists
        code_file = step_dir / 'code.py'
        if code_file.exists():
            details['code'] = code_file.read_text(encoding='utf-8')
        
        # Read prompt.md if exists
        prompt_file = step_dir / 'prompt.md'
        if prompt_file.exists():
            details['prompt'] = prompt_file.read_text(encoding='utf-8')
        
        # Read result.txt if exists
        result_file = step_dir / 'result.txt'
        if result_file.exists():
            details['result'] = result_file.read_text(encoding='utf-8')
        
        # Read metadata.json if exists
        metadata_file = step_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                details['metadata'] = json.load(f)
        
        return jsonify({'success': True, 'details': details})
    except Exception as e:
        logger.error(f"Error getting step details: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

# =============================================================================
# RUN HISTORY ENDPOINTS
# =============================================================================

@app.route('/api/runs/list', methods=['GET'])
def list_runs():
    """List all past runs."""
    try:
        runs = []
        if RUNS_DIR.exists():
            for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True)[:50]:  # Last 50 runs
                if run_dir.is_dir():
                    metadata_file = run_dir / 'metadata.json'
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        runs.append(metadata)
        
        return jsonify({'success': True, 'runs': runs})
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/runs/delete/<run_id>', methods=['DELETE'])
def delete_run(run_id):
    """Delete a run and its artifacts."""
    try:
        run_dir = RUNS_DIR / run_id
        if run_dir.exists():
            import shutil
            shutil.rmtree(run_dir)
            if run_id in run_status:
                del run_status[run_id]
            logger.info(f"Run deleted: {run_id}")
            return jsonify({'success': True, 'message': f'Run {run_id} deleted'})
        else:
            return jsonify({'error': 'Run not found', 'success': False}), 404
    except Exception as e:
        logger.error(f"Error deleting run: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/run/<run_id>/file/<filename>', methods=['GET'])
def get_run_file(run_id, filename):
    """Serve a file from a run's final_output directory."""
    try:
        run_dir = RUNS_DIR / run_id
        final_output_dir = run_dir / 'final_output'
        file_path = final_output_dir / filename
        
        # Security check: ensure file is within the final_output directory
        if not file_path.resolve().is_relative_to(final_output_dir.resolve()):
            return jsonify({'error': 'Invalid file path', 'success': False}), 403
        
        if not file_path.exists() or not file_path.is_file():
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        return send_file(file_path, as_attachment=False)
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/dashboards/list', methods=['GET'])
def list_dashboards():
    """List all generated dashboards."""
    try:
        dashboards = []
        if RUNS_DIR.exists():
            for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True):
                if run_dir.is_dir():
                    dashboard_file = run_dir / 'final_output' / 'dashboard.html'
                    if dashboard_file.exists():
                        metadata = {}
                        metadata_file = run_dir / 'metadata.json'
                        if metadata_file.exists():
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                        
                        dashboards.append({
                            'id': run_dir.name,
                            'title': metadata.get('user_query', f'Dashboard {run_dir.name[:8]}'),
                            'date': metadata.get('timestamp', datetime.fromtimestamp(dashboard_file.stat().st_mtime).isoformat()),
                            'run_id': run_dir.name,
                            'file_url': f'/api/run/{run_dir.name}/file/dashboard.html'
                        })
        
        return jsonify({'success': True, 'dashboards': dashboards})
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================

@app.route('/api/config/models', methods=['GET'])
def get_available_models():
    """Get list of available models."""
    models = {
        'gemini': [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-2.0-flash-exp',
        ],
        'openai': [
            'gpt-4',
            'gpt-4-turbo',
            'gpt-3.5-turbo',
        ],
        'ollama': [
            'ollama/llama2',
            'ollama/mistral',
        ]
    }
    return jsonify({'success': True, 'models': models})

# =============================================================================
# CHART GENERATION ENDPOINT
# =============================================================================

@app.route('/api/generate-chart', methods=['POST'])
def generate_chart():
    """Generate chart from data with automatic type detection."""
    try:
        data = request.json.get('data')
        chart_type = request.json.get('chart_type')  # Optional: auto-detect if not provided
        config_data = request.json.get('config', {})
        
        if not data:
            return jsonify({'error': 'No data provided', 'success': False}), 400
        
        # Create chart config from provided data
        config = ChartConfig(
            width=config_data.get('width', 800),
            height=config_data.get('height', 600),
            theme=config_data.get('theme', 'plotly_white'),
            responsive=config_data.get('responsive', True)
        )
        
        # Generate chart
        chart_data = chart_generator.generate_chart(data, chart_type, config)
        
        return jsonify({
            'success': True,
            'chart': {
                'type': chart_data.chart_type,
                'title': chart_data.title,
                'x_axis': chart_data.x_axis,
                'y_axis': chart_data.y_axis,
                'data': chart_data.data,
                'config': chart_data.config,
                'html': chart_data.html
            }
        })
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/validate-chart-data', methods=['POST'])
def validate_chart_data():
    """Validate chart data and provide recommendations."""
    try:
        data = request.json.get('data')
        
        if not data:
            return jsonify({'error': 'No data provided', 'success': False}), 400
        
        # Validate data and get recommendations
        validation = chart_generator.validate_chart_data(data)
        
        return jsonify({
            'success': True,
            'validation': validation
        })
    except Exception as e:
        logger.error(f"Error validating chart data: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/kpi/suggestions', methods=['POST'])
def get_kpi_suggestions():
    """Get KPI suggestions based on data columns."""
    try:
        data = request.json
        columns = data.get('columns', [])
        
        if not columns:
            return jsonify({'error': 'No columns provided', 'success': False}), 400
        
        suggestions = kpi_calculator.get_kpi_suggestions(columns)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        logger.error(f"Error getting KPI suggestions: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/kpi/detect', methods=['POST'])
def detect_kpi():
    """Detect KPI from user query."""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided', 'success': False}), 400
        
        kpi_info = kpi_calculator.detect_kpi_from_query(query)
        
        if kpi_info:
            prompt = kpi_calculator.generate_kpi_prompt(query, kpi_info)
            return jsonify({
                'success': True,
                'kpi': kpi_info['kpi'],
                'category': kpi_info['category'],
                'prompt': prompt
            })
        else:
            return jsonify({
                'success': True,
                'kpi': None,
                'message': 'No specific KPI detected, will use general calculation'
            })
    except Exception as e:
        logger.error(f"Error detecting KPI: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

# =============================================================================
# TOOL INTEGRATION ENDPOINTS
# =============================================================================

# Initialize tool registry
try:
    from tools.base import tool_registry, register_default_tools, ToolCategory
    register_default_tools()
    logger.info("✅ Tool integrations initialized")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize tool integrations: {e}")
    tool_registry = None

@app.route('/api/tools/list', methods=['GET'])
def list_tools():
    """List all available tools."""
    try:
        if not tool_registry:
            return jsonify({'error': 'Tool registry not initialized', 'success': False}), 500
        
        category = request.args.get('category')
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        cat_enum = None
        if category:
            try:
                cat_enum = ToolCategory(category)
            except ValueError:
                pass
        
        tools = tool_registry.list_tools(category=cat_enum, available_only=available_only)
        
        return jsonify({
            'success': True,
            'tools': [
                {
                    'name': t.name,
                    'category': t.category.value,
                    'description': t.description,
                    'version': t.version,
                    'is_available': t.is_available,
                    'requires_auth': t.requires_auth,
                    'capabilities': t.capabilities
                }
                for t in tools
            ]
        })
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/tools/<tool_name>/info', methods=['GET'])
def get_tool_info(tool_name):
    """Get detailed information about a tool."""
    try:
        if not tool_registry:
            return jsonify({'error': 'Tool registry not initialized', 'success': False}), 500
        
        tool = tool_registry.get(tool_name)
        if not tool:
            return jsonify({'error': f'Tool {tool_name} not found', 'success': False}), 404
        
        info = tool.get_info()
        operations = tool.get_operations()
        
        return jsonify({
            'success': True,
            'tool': {
                'name': info.name,
                'category': info.category.value,
                'description': info.description,
                'version': info.version,
                'is_available': info.is_available,
                'requires_auth': info.requires_auth,
                'dependencies': info.dependencies,
                'capabilities': info.capabilities,
                'operations': operations
            }
        })
    except Exception as e:
        logger.error(f"Error getting tool info: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/tools/<tool_name>/execute', methods=['POST'])
def execute_tool(tool_name):
    """Execute an operation on a tool."""
    try:
        if not tool_registry:
            return jsonify({'error': 'Tool registry not initialized', 'success': False}), 500
        
        data = request.json
        operation = data.get('operation')
        params = data.get('params', {})
        
        if not operation:
            return jsonify({'error': 'Operation is required', 'success': False}), 400
        
        result = tool_registry.execute(tool_name, operation, **params)
        
        return jsonify({
            'success': result.success,
            'data': result.data,
            'error': result.error,
            'metadata': result.metadata
        })
    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/tools/<tool_name>/generate-code', methods=['POST'])
def generate_tool_code(tool_name):
    """Generate Python code for a tool operation."""
    try:
        if not tool_registry:
            return jsonify({'error': 'Tool registry not initialized', 'success': False}), 500
        
        tool = tool_registry.get(tool_name)
        if not tool:
            return jsonify({'error': f'Tool {tool_name} not found', 'success': False}), 404
        
        data = request.json
        operation = data.get('operation')
        params = data.get('params', {})
        
        if not operation:
            return jsonify({'error': 'Operation is required', 'success': False}), 400
        
        code = tool.generate_code(operation, **params)
        
        return jsonify({
            'success': True,
            'code': code,
            'operation': operation
        })
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/tools/categories', methods=['GET'])
def get_tool_categories():
    """Get all available tool categories."""
    try:
        categories = [
            {'id': c.value, 'name': c.name.replace('_', ' ').title()}
            for c in ToolCategory
        ]
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

# =============================================================================
# FEEDBACK ENDPOINT
# =============================================================================

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Receive user feedback about results quality."""
    try:
        feedback_data = request.json
        
        if not feedback_data:
            return jsonify({'error': 'No feedback data provided', 'success': False}), 400
        
        # Extract feedback information
        message_id = feedback_data.get('messageId')
        is_helpful = feedback_data.get('isHelpful', True)
        user_query = feedback_data.get('userQuery', '')
        assistant_response = feedback_data.get('assistantResponse', '')
        issues = feedback_data.get('issues', [])
        details = feedback_data.get('details', '')
        run_id = feedback_data.get('runId')
        timestamp = feedback_data.get('timestamp', datetime.now().isoformat())
        
        # Store feedback in a feedback directory
        FEEDBACK_DIR = Path("feedback")
        FEEDBACK_DIR.mkdir(exist_ok=True)
        
        feedback_file = FEEDBACK_DIR / f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{message_id[:8] if message_id else 'unknown'}.json"
        
        feedback_record = {
            'message_id': message_id,
            'is_helpful': is_helpful,
            'user_query': user_query,
            'assistant_response_preview': assistant_response[:500] if assistant_response else '',
            'issues': issues,
            'details': details,
            'run_id': run_id,
            'timestamp': timestamp
        }
        
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_record, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Feedback received: {'Helpful' if is_helpful else 'Not helpful'} - {message_id}")
        
        return jsonify({
            'success': True,
            'message': 'Feedback received successfully'
        })
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

# =============================================================================
# SERVE FRONTEND
# =============================================================================

@app.route('/')
def serve_frontend():
    """Serve frontend index.html"""
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / 'index.html').exists():
        return send_from_directory(str(FRONTEND_DIST), 'index.html')
    else:
        return send_from_directory(str(FRONTEND_SOURCE), 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    # Check if React is built
    react_built = FRONTEND_DIST.exists() and (FRONTEND_DIST / 'index.html').exists()
    
    # IMPORTANT: Block TypeScript files FIRST if React not built
    if path.endswith(('.tsx', '.ts', '.tsx.map', '.ts.map')):
        if not react_built:
            # React not built - block TypeScript files
            logger.warning(f"Blocked request for TypeScript file: {path} (React not built)")
            return jsonify({
                'error': 'React app not built',
                'message': 'TypeScript files cannot be served directly. Please build React first.',
                'instructions': [
                    '1. Install dependencies: cd frontend && npm install',
                    '2. Build React: npm run build',
                    '3. Or use Vite dev server: npm run dev (port 3000)'
                ]
            }), 503
        # If React is built, check dist for compiled JS files
        # TypeScript files shouldn't be in dist, but handle gracefully
        if react_built:
            # Try to find compiled JS version
            js_path = path.replace('.tsx', '.js').replace('.ts', '.js')
            dist_js_path = FRONTEND_DIST / js_path
            if dist_js_path.exists():
                return send_from_directory(str(FRONTEND_DIST), js_path)
            # If no JS version, return 404
            return jsonify({'error': 'File not found'}), 404
    
    # Check dist first (production)
    if react_built:
        dist_path = FRONTEND_DIST / path
        if dist_path.exists() and dist_path.is_file():
            return send_from_directory(str(FRONTEND_DIST), path)
    
    # Handle missing CSS files gracefully
    if path.endswith('.css'):
        if react_built and (FRONTEND_DIST / path).exists():
            return send_from_directory(str(FRONTEND_DIST), path)
        if not (FRONTEND_SOURCE / path).exists():
            # Return empty CSS instead of 404
            return '', 204  # No Content
    
    # Fallback to source (but NEVER for TypeScript files)
    if not path.endswith(('.tsx', '.ts', '.tsx.map', '.ts.map')):
        source_path = FRONTEND_SOURCE / path
        if source_path.exists() and source_path.is_file():
            return send_from_directory(str(FRONTEND_SOURCE), path)
    
    # For React Router or SPA: serve index.html for all routes
    if react_built:
        return send_from_directory(str(FRONTEND_DIST), 'index.html')
    else:
        # Return helpful error page if React not built
        if path not in ['index.html', '']:
            return jsonify({
                'error': 'React app not built',
                'message': 'Please build the React app first or use Vite dev server',
                'build_command': 'cd frontend && npm install && npm run build'
            }), 503
        return send_from_directory(str(FRONTEND_SOURCE), 'index.html')

# =============================================================================
# SQL EXPORT ENDPOINTS
# =============================================================================

@app.route('/api/data/export-sql/<int:file_id>', methods=['POST'])
def export_to_sql(file_id):
    """
    Export data file to SQL script.
    
    Request body:
    {
        "dialect": "postgresql",  # or mysql, sqlite, sqlserver, oracle
        "database_name": "my_database",
        "table_name": "my_table",
        "schema_name": "public",  # optional
        "primary_key": "id",  # optional
        "indexes": ["email", "created_at"],  # optional
        "include_database": true,
        "include_schema": false,
        "batch_size": 100
    }
    """
    try:
        data = request.json or {}
        user_id = data.get('user_id', 'default')
        
        # Get file
        file_path = storage_manager.get_file_path(file_id, user_id)
        if not file_path:
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        # Load data into DataFrame
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        elif file_ext == '.parquet':
            df = pd.read_parquet(file_path)
        else:
            return jsonify({'error': 'Unsupported file type', 'success': False}), 400
        
        # Generate SQL
        dialect = data.get('dialect', 'postgresql')
        database_name = data.get('database_name', 'tahlil_db')
        table_name = data.get('table_name', Path(file_path).stem)
        
        generator = SQLGenerator(dialect=dialect)
        sql_script = generator.generate_full_script(
            df=df,
            database_name=database_name,
            table_name=table_name,
            schema_name=data.get('schema_name'),
            primary_key=data.get('primary_key'),
            indexes=data.get('indexes', []),
            include_database=data.get('include_database', True),
            include_schema=data.get('include_schema', False),
            batch_size=data.get('batch_size', 100),
            include_advanced_features=data.get('include_advanced_features', False)
        )
        
        # Save SQL file
        sql_filename = f"{table_name}_{dialect}.sql"
        sql_filepath = TEMP_DIR / sql_filename
        
        with open(sql_filepath, 'w', encoding='utf-8') as f:
            f.write(sql_script)
        
        logger.info(f"Generated SQL script: {sql_filename} ({len(sql_script)} bytes)")
        
        return jsonify({
            'success': True,
            'sql_script': sql_script,
            'filename': sql_filename,
            'download_url': f'/api/data/download-sql/{sql_filename}',
            'stats': {
                'rows': len(df),
                'columns': len(df.columns),
                'script_size': len(sql_script),
                'dialect': dialect
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/data/download-sql/<filename>', methods=['GET'])
def download_sql_file(filename):
    """Download generated SQL file."""
    try:
        filepath = TEMP_DIR / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )
    except Exception as e:
        logger.error(f"Error downloading SQL file: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


# =============================================================================
# SERVER UTILITIES
# =============================================================================

def check_port_available(port: int) -> bool:
    """Check if a port is available."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except OSError:
        return False

def kill_processes_on_port(port: int):
    """Attempt to kill processes using the specified port (Windows)."""
    try:
        import subprocess
        # Find processes using the port
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True
        )
        pids = []
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    if pid.isdigit():
                        pids.append(pid)
        
        # Kill found processes
        for pid in pids:
            try:
                subprocess.run(['taskkill', '/PID', pid, '/F'], 
                             capture_output=True, check=False)
                logger.warning(f"Killed process {pid} using port {port}")
            except Exception as e:
                logger.warning(f"Could not kill process {pid}: {e}")
    except Exception as e:
        logger.warning(f"Could not check/kill processes on port {port}: {e}")

if __name__ == '__main__':
    PORT = 5000
    
    # Check if port is available
    if not check_port_available(PORT):
        logger.warning(f"⚠️  Port {PORT} is already in use!")
        logger.warning("Attempting to kill processes using port 5000...")
        kill_processes_on_port(PORT)
        
        # Wait a moment for processes to terminate
        import time
        time.sleep(2)
        
        # Check again
        if not check_port_available(PORT):
            logger.error(f"❌ Port {PORT} is still in use after cleanup attempt.")
            logger.error("Please manually kill processes using port 5000:")
            logger.error("  Windows: taskkill /PID <PID> /F")
            logger.error("  Or change the port in app.py")
            raise OSError(f"Port {PORT} is already in use. Please free it or change the port.")
        else:
            logger.info(f"✅ Port {PORT} is now available")
    
    logger.info(f"🚀 Starting Flask server on port {PORT}...")
    logger.info("=" * 70)
    app.run(debug=True, port=PORT, use_reloader=False)  # use_reloader=False prevents duplicate processes
