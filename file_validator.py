"""
File Validation Module for Tahlil Platform
Provides comprehensive file validation, security scanning, and preprocessing
"""

import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging
from dataclasses import dataclass

# Try to import magic, fallback to basic validation
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logging.warning("python-magic not installed. Basic file validation only.")

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of file validation."""
    is_valid: bool
    error_message: str = ""
    file_size: int = 0
    file_type: str = ""
    mime_type: str = ""
    is_duplicate: bool = False
    security_scan_passed: bool = True
    preview_data: Optional[Dict] = None

@dataclass
class FileInfo:
    """Information about uploaded file."""
    original_filename: str
    stored_filename: str
    file_size: int
    file_type: str
    mime_type: str
    upload_date: str
    file_hash: str
    user_id: str

class FileValidator:
    """Comprehensive file validation and security scanning."""
    
    # Allowed file extensions and their corresponding MIME types
    ALLOWED_EXTENSIONS = {
        '.csv': ['text/csv', 'application/csv'],
        '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        '.xls': ['application/vnd.ms-excel'],
        '.json': ['application/json', 'text/json'],
        '.parquet': ['application/octet-stream', 'application/x-parquet'],
        '.txt': ['text/plain', 'application/text'],
        '.tsv': ['text/tab-separated-values'],
    }
    
    # Security settings
    MAX_FILE_SIZE_MB = 100  # 100MB per file
    MAX_FILES_PER_UPLOAD = 10
    SCAN_FOR_MALWARE = True
    
    # Dangerous file patterns to block
    DANGEROUS_PATTERNS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.app', '.deb', '.pkg', '.dmg', '.rpm', '.msi', '.php', '.asp',
        '.jsp', '.py', '.rb', '.pl', '.sh', '.ps1'
    ]
    
    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path("data/files")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.existing_hashes = self._load_existing_hashes()
    
    def _load_existing_hashes(self) -> set:
        """Load existing file hashes for duplicate detection."""
        hashes = set()
        if self.storage_dir.exists():
            for file_path in self.storage_dir.iterdir():
                if file_path.is_file():
                    try:
                        file_hash = self._calculate_file_hash(file_path)
                        hashes.add(file_hash)
                    except Exception as e:
                        logger.warning(f"Could not hash existing file {file_path}: {e}")
        return hashes
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension in lowercase."""
        return Path(filename).suffix.lower()
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type using python-magic."""
        if not HAS_MAGIC:
            # Fallback to extension-based detection
            ext = file_path.suffix.lower()
            if ext in self.ALLOWED_EXTENSIONS:
                return self.ALLOWED_EXTENSIONS[ext][0]
            return 'application/octet-stream'
        
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(str(file_path))
        except Exception as e:
            logger.warning(f"Could not determine MIME type: {e}")
            # Fallback to extension-based detection
            ext = file_path.suffix.lower()
            if ext in self.ALLOWED_EXTENSIONS:
                return self.ALLOWED_EXTENSIONS[ext][0]
            return 'application/octet-stream'
    
    def _check_file_security(self, file_path: Path, filename: str) -> bool:
        """Basic security scan for malicious files."""
        if not self.SCAN_FOR_MALWARE:
            return True
        
        # Check filename for dangerous patterns
        filename_lower = filename.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if filename_lower.endswith(pattern):
                logger.warning(f"Blocked potentially dangerous file: {filename}")
                return False
        
        # Check file content (basic heuristics)
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024)  # Read first 1KB
                
                # Check for suspicious patterns
                suspicious_patterns = [
                    b'<script', b'javascript:', b'vbscript:', b'data:text/html',
                    b'eval(', b'exec(', b'system(', b'shell_exec'
                ]
                
                for pattern in suspicious_patterns:
                    if pattern in content.lower():
                        logger.warning(f"Suspicious content detected in {filename}")
                        return False
                        
        except Exception as e:
            logger.warning(f"Security scan failed for {filename}: {e}")
            # Fail safe - block if scan fails
            return False
        
        return True
    
    def _generate_preview_data(self, file_path: Path, file_type: str) -> Dict:
        """Generate preview data for the file."""
        try:
            if file_type == '.csv' or file_type == '.tsv':
                return self._preview_csv(file_path)
            elif file_type == '.json':
                return self._preview_json(file_path)
            elif file_type in ['.xlsx', '.xls']:
                return self._preview_excel(file_path)
            elif file_type == '.txt':
                return self._preview_text(file_path)
            elif file_type == '.parquet':
                return self._preview_parquet(file_path)
            else:
                return {"error": "Preview not supported for this file type"}
        except Exception as e:
            logger.warning(f"Could not generate preview for {file_path}: {e}")
            return {"error": str(e)}
    
    def _preview_csv(self, file_path: Path, max_rows: int = 5) -> Dict:
        """Generate CSV preview."""
        import pandas as pd
        try:
            df = pd.read_csv(file_path, nrows=max_rows)
            return {
                "type": "csv",
                "columns": list(df.columns),
                "rows": len(df),
                "preview": df.to_dict('records'),
                "shape": df.shape
            }
        except Exception as e:
            return {"error": f"CSV parsing error: {str(e)}"}
    
    def _preview_json(self, file_path: Path) -> Dict:
        """Generate JSON preview."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read(2048)  # Read first 2KB
                
            try:
                parsed = json.loads(data)
                return {
                    "type": "json",
                    "valid": True,
                    "preview": parsed,
                    "size": len(data)
                }
            except json.JSONDecodeError:
                return {
                    "type": "json",
                    "valid": False,
                    "preview": data[:500],  # First 500 chars
                    "error": "Invalid JSON format"
                }
        except Exception as e:
            return {"error": f"JSON reading error: {str(e)}"}
    
    def _preview_excel(self, file_path: Path) -> Dict:
        """Generate Excel preview."""
        try:
            import pandas as pd
            df = pd.read_excel(file_path, nrows=5)
            return {
                "type": "excel",
                "columns": list(df.columns),
                "rows": len(df),
                "preview": df.to_dict('records'),
                "shape": df.shape
            }
        except Exception as e:
            return {"error": f"Excel parsing error: {str(e)}"}
    
    def _preview_text(self, file_path: Path) -> Dict:
        """Generate text preview."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # First 1KB
                
            lines = content.split('\n')
            return {
                "type": "text",
                "lines": len(lines),
                "preview": content,
                "word_count": len(content.split())
            }
        except Exception as e:
            return {"error": f"Text reading error: {str(e)}"}
    
    def _preview_parquet(self, file_path: Path) -> Dict:
        """Generate Parquet preview."""
        try:
            import pandas as pd
            df = pd.read_parquet(file_path)
            # Get first few rows
            preview_df = df.head(5)
            return {
                "type": "parquet",
                "columns": list(df.columns),
                "rows": len(df),
                "preview": preview_df.to_dict('records'),
                "shape": df.shape
            }
        except Exception as e:
            return {"error": f"Parquet reading error: {str(e)}"}
    
    def validate_single_file(self, file_content: bytes, filename: str, user_id: str = 'default') -> ValidationResult:
        """Validate a single file."""
        result = ValidationResult(is_valid=False)
        
        # Basic checks
        if not filename or not file_content:
            result.error_message = "No file provided"
            return result
        
        result.file_size = len(file_content)
        
        # Check file size
        max_size_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024
        if result.file_size > max_size_bytes:
            result.is_valid = False
            result.error_message = f"File size ({result.file_size / 1024 / 1024:.1f}MB) exceeds maximum ({self.MAX_FILE_SIZE_MB}MB)"
            return result
        
        # Check file extension
        file_ext = self._get_file_extension(filename)
        if file_ext not in self.ALLOWED_EXTENSIONS:
            result.is_valid = False
            result.error_message = f"File type '{file_ext}' not supported. Allowed types: {list(self.ALLOWED_EXTENSIONS.keys())}"
            return result
        
        result.file_type = file_ext
        
        # Create temporary file for MIME detection and security scan
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_path = Path(temp_file.name)
            try:
                temp_path.write_bytes(file_content)
                
                # Get MIME type
                result.mime_type = self._get_mime_type(temp_path)
                
                # Validate MIME type matches extension
                if result.mime_type not in self.ALLOWED_EXTENSIONS[file_ext]:
                    result.is_valid = False
                    result.error_message = f"File content doesn't match extension. Detected: {result.mime_type}"
                    return result
                
                # Security scan
                result.security_scan_passed = self._check_file_security(temp_path, filename)
                if not result.security_scan_passed:
                    result.is_valid = False
                    result.error_message = "File failed security scan"
                    return result
                
                # Check for duplicates
                file_hash = self._calculate_file_hash(temp_path)
                result.is_duplicate = file_hash in self.existing_hashes
                
                # Generate preview
                result.preview_data = self._generate_preview_data(temp_path, file_ext)
                
            finally:
                # Clean up temp file
                try:
                    temp_path.unlink()
                except:
                    pass
        
        result.is_valid = True
        return result
    
    def validate_multiple_files(self, files_data: List[Tuple[bytes, str]], user_id: str = 'default') -> List[ValidationResult]:
        """Validate multiple files."""
        if len(files_data) > self.MAX_FILES_PER_UPLOAD:
            error_result = ValidationResult(is_valid=False)
            error_result.error_message = f"Too many files. Maximum {self.MAX_FILES_PER_UPLOAD} files per upload"
            return [error_result]
        
        results = []
        for file_content, filename in files_data:
            result = self.validate_single_file(file_content, filename, user_id)
            results.append(result)
        
        return results
    
    def store_file(self, file_content: bytes, filename: str, user_id: str = 'default') -> FileInfo:
        """Store a validated file and return file info."""
        # Validate first
        validation = self.validate_single_file(file_content, filename, user_id)
        if not validation.is_valid:
            raise ValueError(f"File validation failed: {validation.error_message}")
        
        # Generate unique filename based on hash
        file_hash = self._calculate_file_hash_bytes(file_content)
        stored_filename = f"{file_hash}_{Path(filename).suffix}"
        
        # Store file
        file_path = self.storage_dir / stored_filename
        file_path.write_bytes(file_content)
        
        # Update existing hashes
        self.existing_hashes.add(file_hash)
        
        # Return file info
        return FileInfo(
            original_filename=filename,
            stored_filename=stored_filename,
            file_size=validation.file_size,
            file_type=validation.file_type,
            mime_type=validation.mime_type,
            upload_date="",
            file_hash=file_hash,
            user_id=user_id
        )
    
    def _calculate_file_hash_bytes(self, content: bytes) -> str:
        """Calculate SHA-256 hash of bytes."""
        return hashlib.sha256(content).hexdigest()
    
    def get_file_info(self, stored_filename: str) -> Optional[FileInfo]:
        """Get information about a stored file."""
        file_path = self.storage_dir / stored_filename
        if not file_path.exists():
            return None
        
        # Extract original filename from stored filename
        if '_' in stored_filename:
            file_hash, original_ext = stored_filename.split('_', 1)
            # Find matching original filename from existing files
            for ext in self.ALLOWED_EXTENSIONS:
                if original_ext == ext:
                    # Look for files with this hash to get original name
                    for existing_file in self.storage_dir.glob(f"{file_hash}_{ext}"):
                        return FileInfo(
                            original_filename=existing_file.name,
                            stored_filename=stored_filename,
                            file_size=file_path.stat().st_size,
                            file_type=ext,
                            mime_type=self._get_mime_type(file_path),
                            upload_date="",
                            file_hash=file_hash,
                            user_id=""
                        )
        
        return None
    
    def delete_file(self, stored_filename: str) -> bool:
        """Delete a stored file."""
        file_path = self.storage_dir / stored_filename
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            # Update existing hashes
            file_hash = stored_filename.split('_')[0]
            self.existing_hashes.discard(file_hash)
            return True
        except Exception as e:
            logger.error(f"Error deleting file {stored_filename}: {e}")
            return False
    
    def list_files(self, user_id: str = 'default') -> List[FileInfo]:
        """List all stored files."""
        files = []
        if self.storage_dir.exists():
            for file_path in self.storage_dir.iterdir():
                if file_path.is_file():
                    file_info = self.get_file_info(file_path.name)
                    if file_info:
                        files.append(file_info)
        
        # Sort by upload date (newest first)
        files.sort(key=lambda x: x.upload_date, reverse=True)
        return files
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        total_size = 0
        file_count = 0
        
        if self.storage_dir.exists():
            for file_path in self.storage_dir.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        return {
            "used": total_size,
            "total": self.MAX_FILE_SIZE_MB * 1024 * 1024 * 50,  # 5GB total limit
            "file_count": file_count
        }
