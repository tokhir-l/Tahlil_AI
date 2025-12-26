# Pre-Run Checklist - Tahlil Platform

## ✅ Verification Status

### 1. **Python Environment** ✅
- Python 3.13.5 installed and working
- Core dependencies can be imported (flask, flask_cors, yaml, pandas)

### 2. **Required Files** ✅
- ✅ `app.py` - Flask backend (711 lines)
- ✅ `tahlil.py` - Core AI engine
- ✅ `provider.py` - AI model providers
- ✅ `storage.py` - File storage manager
- ✅ `prompt.yaml` - AI prompts
- ✅ `config.yaml` - Configuration
- ✅ `requirements.txt` - Dependencies list

### 3. **Frontend Files** ⚠️ **NEEDS ATTENTION**
- ✅ `frontend/app.js` - JavaScript logic (2300+ lines)
- ✅ `frontend/styles.css` - Styling
- ⚠️ `frontend/index.html` - Currently set up for React/TypeScript
  - **Issue:** The index.html references React/TypeScript files (index.tsx, App.tsx)
  - **Solution:** Need to verify which frontend setup to use

### 4. **Dependencies** ✅
All required packages listed in `requirements.txt`:
- flask, flask-cors
- google-generativeai
- pandas, openpyxl
- matplotlib, plotly, seaborn
- numpy, scipy, scikit-learn
- yaml, requests, etc.

### 5. **API Keys** ⚠️ **SECURITY NOTE**
- ⚠️ **WARNING:** Default API key is hardcoded in `app.py` line 38
- ✅ Fallback mechanism exists
- **Recommendation:** Set environment variable instead

### 6. **Directory Structure** ✅
- `data/` - Will be created automatically
- `runs/` - Will be created automatically
- `frontend/` - Exists with all files

---

## ⚠️ Issues Found

### Issue 1: Frontend Setup Confusion
**Problem:** Two frontend setups exist:
1. Original HTML/JS (app.js, styles.css)
2. React/TypeScript (index.tsx, App.tsx, components/)

**Current State:** `index.html` is configured for React/TypeScript

**Solution Options:**
- **Option A:** Use the React/TypeScript setup (requires build step)
- **Option B:** Create/use a simpler HTML file that uses app.js directly

### Issue 2: Hardcoded API Key
**Location:** `app.py` line 38
**Risk:** API key exposed in code
**Fix:** Use environment variable only

---

## ✅ Ready to Run Checklist

Before running, ensure:

- [ ] **Dependencies installed:**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **API Key set (recommended):**
  ```bash
  # Windows PowerShell
  $env:GEMINI_API_KEY = "your-key-here"
  
  # Windows CMD
  set GEMINI_API_KEY=your-key-here
  
  # Linux/Mac
  export GEMINI_API_KEY="your-key-here"
  ```

- [ ] **Frontend issue resolved:**
  - Decide which frontend to use (React or plain HTML/JS)
  - If React: Need to build/compile first
  - If plain HTML/JS: Need simpler index.html

- [ ] **Port 5000 available:**
  - Check if anything is running on port 5000
  - Can change port in `app.py` line 710 if needed

---

## 🚀 Quick Start Commands

### Option 1: Direct Run
```bash
python app.py
```

### Option 2: Using Startup Script (Windows)
```bash
run_web.bat
```

### Option 3: Using Startup Script (Linux/Mac)
```bash
chmod +x run_web.sh
./run_web.sh
```

---

## 🔍 What to Check After Starting

1. **Server starts without errors:**
   ```
   * Running on http://127.0.0.1:5000
   * Debug mode: on
   ```

2. **Frontend loads:**
   - Open http://localhost:5000
   - Should see the Tahlil interface

3. **File upload works:**
   - Try uploading a CSV/Excel file
   - Should see file in the list

4. **API endpoints respond:**
   - Check browser console (F12) for errors
   - Test a simple query

---

## 🛠️ Quick Fixes

### If Frontend Doesn't Load:
1. Check browser console (F12) for errors
2. Verify `frontend/index.html` exists and is correct
3. Check if React build is needed

### If Import Errors:
```bash
pip install -r requirements.txt
```

### If Port Already in Use:
Edit `app.py` line 710:
```python
app.run(debug=True, port=5001)  # Change to different port
```

### If API Key Issues:
- Set environment variable (see above)
- Or the default key will be used (not recommended for production)

---

## 📝 Next Steps

1. **Resolve frontend setup** - Choose React or plain HTML/JS
2. **Set API key** - Use environment variable
3. **Install dependencies** - `pip install -r requirements.txt`
4. **Run the app** - `python app.py`
5. **Test in browser** - http://localhost:5000

---

## ✅ Summary

**Status:** Mostly ready, but frontend setup needs clarification

**Critical:** 
- ✅ Backend files all present
- ✅ Dependencies can be imported
- ⚠️ Frontend setup unclear (React vs plain HTML/JS)
- ⚠️ API key hardcoded (works but not secure)

**Action Required:**
1. Decide on frontend approach
2. Set API key as environment variable (recommended)
3. Install dependencies if not already done
4. Run and test

