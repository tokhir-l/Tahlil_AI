"""
Storage management module for Tahlil platform.
Handles file storage, deduplication, metadata tracking, and cleanup.
"""

import sqlite3
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default
DEFAULT_USER_QUOTA = 1 * 1024 * 1024 * 1024  # 1GB default per user
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.txt', '.parquet', '.pdf'}
CLEANUP_DAYS = 90  # Delete files not used for 90 days

class StorageManager:
    """Manages file storage with deduplication, metadata tracking, and quotas."""
    
    def __init__(self, data_dir: Path, db_path: Optional[Path] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Files directory for actual file storage
        self.files_dir = self.data_dir / "files"
        self.files_dir.mkdir(exist_ok=True)
        
        # Database path
        if db_path is None:
            db_path = self.data_dir / "storage.db"
        self.db_path = Path(db_path)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL UNIQUE,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                version INTEGER DEFAULT 1
            )
        """)
        
        # File tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                tag TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        
        # File access log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                user_id TEXT,
                access_type TEXT,
                access_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        
        # User storage quotas
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS user_quotas (
                user_id TEXT PRIMARY KEY,
                quota_bytes INTEGER DEFAULT {DEFAULT_USER_QUOTA},
                used_bytes INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON files(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON files(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_used ON files(last_used)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON files(is_active)")
        
        conn.commit()
        conn.close()
        logger.info(f"Storage database initialized at {self.db_path}")
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validate file before upload."""
        # Check file size
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        return True, None
    
    def check_user_quota(self, user_id: str, additional_size: int) -> Tuple[bool, Optional[str]]:
        """Check if user has enough quota for new file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get or create user quota
        cursor.execute("""
            SELECT quota_bytes, used_bytes FROM user_quotas WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            quota_bytes, used_bytes = result
        else:
            # Create default quota for user
            quota_bytes = DEFAULT_USER_QUOTA
            used_bytes = 0
            cursor.execute("""
                INSERT INTO user_quotas (user_id, quota_bytes, used_bytes)
                VALUES (?, ?, ?)
            """, (user_id, quota_bytes, used_bytes))
            conn.commit()
        
        if used_bytes + additional_size > quota_bytes:
            conn.close()
            return False, f"Storage quota exceeded. Available: {(quota_bytes - used_bytes) / 1024 / 1024:.2f}MB, Required: {additional_size / 1024 / 1024:.2f}MB"
        
        conn.close()
        return True, None
    
    def find_duplicate_file(self, file_hash: str) -> Optional[Dict]:
        """Check if file with same hash already exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, stored_filename, file_size, user_id, original_filename
            FROM files
            WHERE file_hash = ? AND is_active = 1
            LIMIT 1
        """, (file_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'stored_filename': result[1],
                'file_size': result[2],
                'user_id': result[3],
                'original_filename': result[4]
            }
        return None
    
    def store_file(self, file_content: bytes, original_filename: str, user_id: str = 'default') -> Dict:
        """Store file with deduplication and metadata tracking."""
        # Validate file
        file_size = len(file_content)
        is_valid, error_msg = self.validate_file(original_filename, file_size)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Check user quota
        quota_ok, quota_error = self.check_user_quota(user_id, file_size)
        if not quota_ok:
            raise ValueError(quota_error)
        
        # Calculate hash
        file_hash = self.calculate_file_hash(file_content)
        
        # Check for duplicate
        duplicate = self.find_duplicate_file(file_hash)
        if duplicate:
            # File already exists, create reference for this user
            logger.info(f"Duplicate file found: {original_filename} (hash: {file_hash[:16]}...)")
            
            # Check if this user already has access to this file
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM files
                WHERE file_hash = ? AND user_id = ? AND is_active = 1
            """, (file_hash, user_id))
            
            existing = cursor.fetchone()
            
            if not existing:
                # Create new entry for this user (same file, different user reference)
                file_ext = Path(original_filename).suffix
                stored_filename = f"{file_hash}{file_ext}"
                stored_path = self.files_dir / stored_filename
                
                # File already exists on disk, just create database entry
                cursor.execute("""
                    INSERT INTO files (user_id, original_filename, stored_filename, file_hash, 
                                     file_size, file_type, upload_date, last_used, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, original_filename, stored_filename, file_hash, file_size,
                      file_ext, datetime.now().isoformat(), datetime.now().isoformat(), 1))
                
                file_id = cursor.lastrowid
            else:
                # User already has this file
                file_id = existing[0]
                cursor.execute("""
                    UPDATE files SET last_used = ?, access_count = access_count + 1
                    WHERE id = ?
                """, (datetime.now().isoformat(), file_id))
            
            conn.commit()
            conn.close()
            
            return {
                'id': file_id,
                'original_filename': original_filename,
                'stored_filename': duplicate['stored_filename'],
                'file_hash': file_hash,
                'file_size': file_size,
                'is_duplicate': True,
                'duplicate_of': duplicate['id']
            }
        
        # New file, store it
        file_ext = Path(original_filename).suffix
        stored_filename = f"{file_hash}{file_ext}"
        stored_path = self.files_dir / stored_filename
        
        # Save file
        stored_path.write_bytes(file_content)
        
        # Store metadata
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO files (user_id, original_filename, stored_filename, file_hash,
                             file_size, file_type, upload_date, last_used, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, original_filename, stored_filename, file_hash, file_size,
              file_ext, datetime.now().isoformat(), datetime.now().isoformat(), 1))
        
        file_id = cursor.lastrowid
        
        # Update user quota
        cursor.execute("""
            UPDATE user_quotas SET used_bytes = used_bytes + ?
            WHERE user_id = ?
        """, (file_size, user_id))
        
        # Log access
        cursor.execute("""
            INSERT INTO file_access_log (file_id, user_id, access_type)
            VALUES (?, ?, ?)
        """, (file_id, user_id, 'upload'))
        
        conn.commit()
        conn.close()
        
        logger.info(f"File stored: {original_filename} -> {stored_filename} (hash: {file_hash[:16]}...)")
        
        return {
            'id': file_id,
            'original_filename': original_filename,
            'stored_filename': stored_filename,
            'file_hash': file_hash,
            'file_size': file_size,
            'is_duplicate': False
        }
    
    def get_file_path(self, file_id: int, user_id: str = 'default') -> Optional[Path]:
        """Get file path by ID, checking user access."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT stored_filename FROM files
            WHERE id = ? AND user_id = ? AND is_active = 1
        """, (file_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stored_filename = result[0]
            file_path = self.files_dir / stored_filename
            if file_path.exists():
                # Update last_used
                self._update_last_used(file_id)
                return file_path
        
        return None
    
    def get_file_by_name(self, filename: str, user_id: str = 'default') -> Optional[Dict]:
        """Get file metadata by original filename."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, original_filename, stored_filename, file_hash, file_size,
                   file_type, upload_date, last_used, access_count
            FROM files
            WHERE original_filename = ? AND user_id = ? AND is_active = 1
            ORDER BY upload_date DESC
            LIMIT 1
        """, (filename, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'original_filename': result[1],
                'stored_filename': result[2],
                'file_hash': result[3],
                'file_size': result[4],
                'file_type': result[5],
                'upload_date': result[6],
                'last_used': result[7],
                'access_count': result[8]
            }
        return None
    
    def list_files(self, user_id: str = 'default') -> List[Dict]:
        """List all files for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, original_filename, stored_filename, file_hash, file_size,
                   file_type, upload_date, last_used, access_count
            FROM files
            WHERE user_id = ? AND is_active = 1
            ORDER BY upload_date DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        files = []
        for row in results:
            files.append({
                'id': row[0],
                'original_filename': row[1],
                'stored_filename': row[2],
                'file_hash': row[3],
                'file_size': row[4],
                'file_type': row[5],
                'upload_date': row[6],
                'last_used': row[7],
                'access_count': row[8]
            })
        
        return files
    
    def delete_file(self, file_id: int, user_id: str = 'default') -> bool:
        """Delete file (soft delete - mark as inactive)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get file info
        cursor.execute("""
            SELECT stored_filename, file_hash, file_size FROM files
            WHERE id = ? AND user_id = ? AND is_active = 1
        """, (file_id, user_id))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        stored_filename, file_hash, file_size = result
        
        # Check if other users have this file
        cursor.execute("""
            SELECT COUNT(*) FROM files
            WHERE file_hash = ? AND is_active = 1
        """, (file_hash,))
        
        other_users_count = cursor.fetchone()[0] - 1  # Exclude current user
        
        # Mark as inactive for this user
        cursor.execute("""
            UPDATE files SET is_active = 0 WHERE id = ? AND user_id = ?
        """, (file_id, user_id))
        
        # Update user quota
        cursor.execute("""
            UPDATE user_quotas SET used_bytes = used_bytes - ?
            WHERE user_id = ?
        """, (file_size, user_id))
        
        # Log deletion
        cursor.execute("""
            INSERT INTO file_access_log (file_id, user_id, access_type)
            VALUES (?, ?, ?)
        """, (file_id, user_id, 'delete'))
        
        conn.commit()
        conn.close()
        
        # If no other users have this file, delete physical file
        if other_users_count == 0:
            file_path = self.files_dir / stored_filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Physical file deleted: {stored_filename}")
        
        logger.info(f"File deleted (soft): {file_id} for user {user_id}")
        return True
    
    def _update_last_used(self, file_id: int):
        """Update last_used timestamp and access_count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE files SET last_used = ?, access_count = access_count + 1
            WHERE id = ?
        """, (datetime.now().isoformat(), file_id))
        
        conn.commit()
        conn.close()
    
    def get_storage_stats(self, user_id: str = 'default') -> Dict:
        """Get storage statistics for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get quota info
        cursor.execute("""
            SELECT quota_bytes, used_bytes FROM user_quotas WHERE user_id = ?
        """, (user_id,))
        
        quota_result = cursor.fetchone()
        if quota_result:
            quota_bytes, used_bytes = quota_result
        else:
            quota_bytes = DEFAULT_USER_QUOTA
            used_bytes = 0
        
        # Get file count
        cursor.execute("""
            SELECT COUNT(*), SUM(file_size) FROM files
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        
        count_result = cursor.fetchone()
        file_count = count_result[0] or 0
        total_size = count_result[1] or 0
        
        conn.close()
        
        return {
            'user_id': user_id,
            'file_count': file_count,
            'total_size': total_size,
            'total_size_mb': total_size / 1024 / 1024,
            'quota_bytes': quota_bytes,
            'quota_mb': quota_bytes / 1024 / 1024,
            'used_bytes': used_bytes,
            'used_mb': used_bytes / 1024 / 1024,
            'available_bytes': quota_bytes - used_bytes,
            'available_mb': (quota_bytes - used_bytes) / 1024 / 1024,
            'usage_percentage': (used_bytes / quota_bytes * 100) if quota_bytes > 0 else 0
        }
    
    def cleanup_old_files(self, days: int = CLEANUP_DAYS, user_id: Optional[str] = None) -> int:
        """Clean up files not used for specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find old files
        if user_id:
            cursor.execute("""
                SELECT id, stored_filename, file_hash, file_size FROM files
                WHERE user_id = ? AND is_active = 1 AND last_used < ?
            """, (user_id, cutoff_str))
        else:
            cursor.execute("""
                SELECT id, stored_filename, file_hash, file_size FROM files
                WHERE is_active = 1 AND last_used < ?
            """, (cutoff_str,))
        
        old_files = cursor.fetchall()
        deleted_count = 0
        
        for file_id, stored_filename, file_hash, file_size in old_files:
            # Get user_id for this file
            cursor.execute("SELECT user_id FROM files WHERE id = ?", (file_id,))
            file_user_id = cursor.fetchone()[0]
            
            # Check if other users have this file
            cursor.execute("""
                SELECT COUNT(*) FROM files
                WHERE file_hash = ? AND is_active = 1
            """, (file_hash,))
            
            other_users_count = cursor.fetchone()[0] - 1
            
            # Mark as inactive
            cursor.execute("""
                UPDATE files SET is_active = 0 WHERE id = ?
            """, (file_id,))
            
            # Update user quota
            cursor.execute("""
                UPDATE user_quotas SET used_bytes = used_bytes - ?
                WHERE user_id = ?
            """, (file_size, file_user_id))
            
            # If no other users, delete physical file
            if other_users_count == 0:
                file_path = self.files_dir / stored_filename
                if file_path.exists():
                    file_path.unlink()
            
            deleted_count += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old files (not used for {days} days)")
        return deleted_count
    
    def preview_file(self, file_id: int, user_id: str = 'default', rows: int = 5) -> Optional[Dict]:
        """Preview file structure and first few rows."""
        file_path = self.get_file_path(file_id, user_id)
        if not file_path:
            return None
        
        try:
            import pandas as pd
            
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path, nrows=rows)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=rows)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
                if len(df) > rows:
                    df = df.head(rows)
            elif file_ext == '.parquet':
                df = pd.read_parquet(file_path)
                if len(df) > rows:
                    df = df.head(rows)
            else:
                # For text files, just read first few lines
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [f.readline().strip() for _ in range(rows)]
                return {
                    'type': 'text',
                    'preview': lines,
                    'columns': None,
                    'dtypes': None
                }
            
            # Get total row count (approximate for large files)
            try:
                total_rows = len(pd.read_csv(file_path) if file_ext == '.csv' else pd.read_excel(file_path))
            except:
                total_rows = len(df)
            
            return {
                'type': 'dataframe',
                'preview': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'row_count': total_rows,
                'preview_rows': len(df)
            }
        except Exception as e:
            logger.error(f"Error previewing file: {e}")
            return {
                'type': 'error',
                'error': str(e)
            }

