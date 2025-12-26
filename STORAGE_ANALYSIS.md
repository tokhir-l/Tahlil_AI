# Tahlil Platform - Storage Analysis & Improvement Plan
## Current State & Future Enhancements

---

## 🔍 Current Storage Implementation

### How Files Are Currently Stored

**Location:**
- All files stored in `data/` directory (local filesystem)
- Path: `Tahlil/data/`
- No subdirectories or user isolation

**Current Flow:**
1. User uploads file via web interface
2. File saved directly to `data/` directory with original filename
3. File persists until manually deleted
4. All users share the same storage space

**Storage Structure:**
```
data/
├── Sales.csv
├── HR_Analytics.csv
├── Customers.xlsx
└── ...
```

**Current Limitations:**
- ❌ No user isolation (all files in one directory)
- ❌ No file size limits
- ❌ No storage quotas
- ❌ No file deduplication
- ❌ No automatic cleanup
- ❌ No file metadata (upload date, user, tags)
- ❌ No file versioning
- ❌ No cloud storage option
- ❌ No database tracking
- ❌ Files can overwrite each other (same filename)

---

## 🎯 What's Left to Work On

### Priority 1: Core Storage Improvements (Essential)

#### 1. **User Isolation & Multi-User Support**
**Problem:** All files stored together, no user separation
**Solution:**
- Create user-specific directories: `data/users/{user_id}/`
- Or use database to track file ownership
- Implement user authentication system

**Implementation:**
```python
# Option 1: Directory-based
data/
├── users/
│   ├── user_123/
│   │   ├── Sales.csv
│   │   └── Customers.xlsx
│   └── user_456/
│       └── HR_Data.csv

# Option 2: Database + flat storage
data/
├── files/
│   ├── abc123def456.csv  # Hashed filename
│   └── xyz789ghi012.xlsx
# Database tracks: user_id, original_filename, hash, upload_date
```

#### 2. **File Size Limits & Validation**
**Problem:** No limits, could fill disk space
**Solution:**
- Add configurable file size limits (e.g., 100MB default)
- Validate file types before upload
- Check available disk space

**Implementation:**
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.txt', '.parquet'}

def validate_file(file):
    if file.size > MAX_FILE_SIZE:
        raise ValueError("File too large")
    if not file.filename.endswith(ALLOWED_EXTENSIONS):
        raise ValueError("File type not allowed")
```

#### 3. **File Deduplication**
**Problem:** Same file uploaded multiple times wastes space
**Solution:**
- Calculate file hash (MD5/SHA256)
- Store hash in database
- If file exists, reuse instead of storing duplicate

**Implementation:**
```python
import hashlib

def get_file_hash(file_content):
    return hashlib.sha256(file_content).hexdigest()

# Check if hash exists in database
# If exists, return existing file path
# If not, save and store hash
```

#### 4. **File Metadata & Database Tracking**
**Problem:** No metadata about files (who uploaded, when, size, etc.)
**Solution:**
- Add SQLite/PostgreSQL database
- Store file metadata: user_id, filename, hash, size, upload_date, last_used
- Enable search and filtering

**Database Schema:**
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    original_filename TEXT,
    stored_filename TEXT,
    file_hash TEXT UNIQUE,
    file_size INTEGER,
    file_type TEXT,
    upload_date TIMESTAMP,
    last_used TIMESTAMP,
    access_count INTEGER,
    tags TEXT,
    description TEXT
);
```

#### 5. **Automatic Cleanup & Retention Policies**
**Problem:** Files accumulate forever, filling disk
**Solution:**
- Configurable retention policies (e.g., delete after 90 days of no use)
- Automatic cleanup job
- User-configurable retention

**Implementation:**
```python
# Cleanup old unused files
def cleanup_old_files(days=90):
    cutoff = datetime.now() - timedelta(days=days)
    old_files = db.query("SELECT * FROM files WHERE last_used < ?", cutoff)
    for file in old_files:
        delete_file(file.id)
```

---

### Priority 2: Enhanced Features (Important)

#### 6. **File Versioning**
**Problem:** Uploading same filename overwrites previous file
**Solution:**
- Keep version history
- Allow users to access previous versions
- Auto-increment version numbers

**Implementation:**
```python
# Store as: filename_v1.csv, filename_v2.csv
# Or: files/{hash}/v1, files/{hash}/v2
```

#### 7. **Storage Quotas**
**Problem:** Users could fill entire disk
**Solution:**
- Per-user storage limits (e.g., 1GB per user)
- Track usage in database
- Block uploads when quota exceeded

**Implementation:**
```python
def check_quota(user_id, file_size):
    current_usage = get_user_storage_usage(user_id)
    quota = get_user_quota(user_id)  # e.g., 1GB
    if current_usage + file_size > quota:
        raise QuotaExceededError("Storage quota exceeded")
```

#### 8. **File Organization & Tags**
**Problem:** Hard to find files when many are uploaded
**Solution:**
- Allow users to organize files in folders
- Add tags to files
- Search functionality

**Implementation:**
```python
# Database schema addition
CREATE TABLE file_tags (
    file_id INTEGER,
    tag TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id)
);

CREATE TABLE file_folders (
    file_id INTEGER,
    folder_path TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

#### 9. **File Preview & Validation**
**Problem:** Users don't know if file is valid until analysis
**Solution:**
- Preview first few rows
- Validate file structure
- Show file statistics (rows, columns, data types)

**Implementation:**
```python
def preview_file(filepath, rows=5):
    df = pd.read_csv(filepath, nrows=rows)
    return {
        'preview': df.to_dict('records'),
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.to_dict(),
        'row_count': get_total_rows(filepath)
    }
```

---

### Priority 3: Advanced Features (Future)

#### 10. **Cloud Storage Integration**
**Problem:** Limited to local storage
**Solution:**
- Support AWS S3, Google Cloud Storage, Azure Blob
- Hybrid: frequently used files local, old files in cloud
- Automatic cloud backup

**Implementation:**
```python
# Config option
STORAGE_BACKEND = "local"  # or "s3", "gcs", "azure"

if STORAGE_BACKEND == "s3":
    upload_to_s3(file, bucket, key)
elif STORAGE_BACKEND == "local":
    save_locally(file)
```

#### 11. **File Encryption**
**Problem:** Sensitive data stored in plain text
**Solution:**
- Encrypt files at rest
- User-specific encryption keys
- Decrypt on-the-fly when needed

**Implementation:**
```python
from cryptography.fernet import Fernet

def encrypt_file(file_content, user_key):
    f = Fernet(user_key)
    return f.encrypt(file_content)

def decrypt_file(encrypted_content, user_key):
    f = Fernet(user_key)
    return f.decrypt(encrypted_content)
```

#### 12. **File Sharing & Collaboration**
**Problem:** Users can't share files with others
**Solution:**
- Generate shareable links
- Set permissions (read-only, read-write)
- Time-limited access

**Implementation:**
```python
CREATE TABLE file_shares (
    id INTEGER PRIMARY KEY,
    file_id INTEGER,
    share_token TEXT UNIQUE,
    shared_by TEXT,
    shared_with TEXT,  # user_id or "public"
    permission TEXT,  # "read" or "write"
    expires_at TIMESTAMP,
    created_at TIMESTAMP
);
```

#### 13. **Backup & Restore**
**Problem:** No backup system, data loss risk
**Solution:**
- Scheduled backups
- Point-in-time recovery
- Export/import functionality

---

## 📋 Recommended Implementation Plan

### Phase 1: Essential Improvements (Week 1-2)
1. ✅ Add file size limits and validation
2. ✅ Implement file deduplication (hash-based)
3. ✅ Add SQLite database for file metadata
4. ✅ Basic user isolation (directory-based or DB-based)

### Phase 2: Core Features (Week 3-4)
5. ✅ Automatic cleanup job
6. ✅ Storage quotas per user
7. ✅ File preview functionality
8. ✅ Better error handling

### Phase 3: Enhanced Features (Month 2)
9. ✅ File versioning
10. ✅ File organization (folders/tags)
11. ✅ Search functionality
12. ✅ Usage statistics dashboard

### Phase 4: Advanced Features (Month 3+)
13. ✅ Cloud storage integration
14. ✅ File encryption
15. ✅ File sharing
16. ✅ Backup system

---

## 💡 Recommended Storage Architecture

### Option A: Simple (Current + Database)
```
data/
├── files/
│   ├── abc123def456.csv  # Hashed filenames
│   └── xyz789ghi012.xlsx
└── database.db  # SQLite for metadata
```

**Pros:**
- Simple to implement
- No user directories needed
- Easy to backup
- File deduplication built-in

**Cons:**
- All files in one directory (but hash prevents conflicts)

### Option B: User-Based Directories
```
data/
├── users/
│   ├── user_123/
│   │   └── files/
│   │       ├── Sales.csv
│   │       └── Customers.xlsx
│   └── user_456/
│       └── files/
│           └── HR_Data.csv
└── database.db
```

**Pros:**
- Clear user separation
- Easy to delete user data
- Better for multi-tenant

**Cons:**
- More complex
- Harder to deduplicate across users

### Option C: Hybrid (Recommended)
```
data/
├── files/
│   ├── abc123def456.csv  # Hash-based, shared
│   └── xyz789ghi012.xlsx
└── database.db  # Tracks ownership, metadata
```

**Pros:**
- Deduplication across users
- User isolation via database
- Efficient storage
- Best of both worlds

**Cons:**
- Requires database management

---

## 🛠️ Quick Wins (Can Implement Now)

### 1. Add File Size Limit
```python
# In app.py
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    file = request.files['file']
    if file.content_length > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large. Max size: {MAX_FILE_SIZE/1024/1024}MB', 'success': False}), 400
    # ... rest of code
```

### 2. Add File Type Validation
```python
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.txt', '.parquet'}

def allowed_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed', 'success': False}), 400
```

### 3. Add File Hash for Deduplication
```python
import hashlib

def get_file_hash(file_content):
    return hashlib.sha256(file_content).hexdigest()

# Store hash in database, check before saving
```

### 4. Add Basic Metadata
```python
# Store in JSON file or SQLite
{
    "filename": "Sales.csv",
    "size": 1024000,
    "upload_date": "2024-12-10T10:00:00",
    "hash": "abc123...",
    "type": "csv"
}
```

---

## 📊 Storage Statistics Tracking

Add endpoint to track storage usage:
```python
@app.route('/api/storage/stats', methods=['GET'])
def get_storage_stats():
    total_files = count_files()
    total_size = get_total_size()
    return jsonify({
        'total_files': total_files,
        'total_size': total_size,
        'total_size_mb': total_size / 1024 / 1024
    })
```

---

## 🔐 Security Considerations

1. **File Validation** - Check file content, not just extension
2. **Path Traversal Protection** - Prevent `../` in filenames
3. **File Scanning** - Scan for malicious content
4. **Access Control** - Users can only access their files
5. **Encryption** - Encrypt sensitive files at rest

---

## 💾 Database Schema (Recommended)

```sql
-- Files table
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,
    file_size INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1
);

-- File tags
CREATE TABLE file_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    tag TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id)
);

-- File access log
CREATE TABLE file_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    user_id TEXT,
    access_type TEXT,  -- 'read', 'delete', 'download'
    access_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

---

## 🎯 Next Steps

1. **Decide on storage architecture** (Option A, B, or C)
2. **Implement file size limits** (quick win)
3. **Add SQLite database** for metadata
4. **Implement file deduplication** (hash-based)
5. **Add user isolation** (if multi-user needed)
6. **Create cleanup job** for old files

Would you like me to implement any of these improvements?

