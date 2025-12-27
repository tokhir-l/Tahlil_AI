# Tahlil Setup Guide

Get started with Tahlil in 5 minutes.

---

## 🚀 Quick Start

### Step 1: Get Your API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy the key (starts with `AIza...`)

### Step 2: Set the API Key

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY = "AIza...your-key-here"
```

**Windows CMD:**
```cmd
set GEMINI_API_KEY=AIza...your-key-here
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="AIza...your-key-here"
```

### Step 3: Install Dependencies

```bash
# Using uv (recommended - 10x faster)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Step 4: Start the Server

```bash
python app.py
```

### Step 5: Open the App

Navigate to: **http://localhost:5000**

---

## 📁 Your First Analysis

1. **Upload a file** - Drag & drop a CSV or Excel file
2. **Ask a question** - Type naturally: "What are the trends in this data?"
3. **Wait 2-5 minutes** - Watch the AI work step-by-step
4. **Get your answer** - Humanized insights with visualizations

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
model_name: "gemini-2.0-flash"    # AI model
max_refinement_rounds: 3          # Analysis depth
auto_debug: false                 # Auto-fix errors
preserve_artifacts: true          # Save all steps
```

---

## 🔧 Alternative API Key Setup

### Option A: Permanent (Recommended)

**Windows:**
1. Press `Win + X` → "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Add new User variable:
   - Name: `GEMINI_API_KEY`
   - Value: Your API key
5. Restart terminal

**Linux/Mac:**
```bash
echo 'export GEMINI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

### Option B: File-based

Create `gemini_api_key.txt` in the project root:
```
AIza...your-key-here
```

---

## 🐛 Troubleshooting

### "API Key not set"
- Make sure you set the environment variable
- Restart your terminal after setting it
- Verify: `python -c "import os; print(os.getenv('GEMINI_API_KEY'))"`

### Analysis taking too long
- Check your internet connection
- Try a simpler query first
- Reduce `max_refinement_rounds` in config.yaml

### File upload fails
- Check file size (max 100MB)
- Supported formats: CSV, Excel, JSON, Parquet
- Avoid special characters in filenames

### Port 5000 already in use
```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
kill -9 $(lsof -t -i:5000)
```

---

## 📊 Supported Data Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Most common |
| Excel | `.xlsx`, `.xls` | Multiple sheets supported |
| JSON | `.json` | Arrays or objects |
| Parquet | `.parquet` | Columnar format |
| Text | `.txt` | Plain text |

---

## 🔗 Google Sheets Import

1. Open your Google Sheet
2. Click **Share** → **Anyone with the link** → **Viewer**
3. Copy the link
4. Paste in Tahlil's "Import from Google Sheets" section

---

## ✅ Checklist

Before your first analysis:

- [ ] Got API key from Google AI Studio
- [ ] Set `GEMINI_API_KEY` environment variable
- [ ] Installed dependencies (`uv sync` or `pip install -r requirements.txt`)
- [ ] Started server (`python app.py`)
- [ ] Opened http://localhost:5000
- [ ] Uploaded test file
- [ ] Asked a test question

---

## 🎉 You're Ready!

Start analyzing your data with AI. Just upload and ask!
