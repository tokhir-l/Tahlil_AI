# Tahlil Web Interface - Visual Overview

## 🎨 User Interface Layout

### Header (Navigation)
```
┌─────────────────────────────────────────────────────────────┐
│  🤖 Tahlil                       [Home] [History] [Settings]  │
│  Data Science Agent Framework                               │
└─────────────────────────────────────────────────────────────┘
```

### Home Page - Query Builder
```
┌─────────────────────────────────────────────────────────────┐
│ 📝 Ask Your Data Science Question                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. Select or Upload Data Files                              │
│    ┌─────────────────────────────────────────────────────┐  │
│    │  📁 Drag files here or click to select             │  │
│    │  Supported: CSV, Excel, JSON, TXT, Parquet        │  │
│    │                                                    │  │
│    │  [sales.csv] [✕] [customers.xlsx] [✕]            │  │
│    └─────────────────────────────────────────────────────┘  │
│                                                             │
│ 2. Ask Your Question                                        │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ What are the top 5 products by revenue?           │  │
│    │ ___________________________________________________ │  │
│    └─────────────────────────────────────────────────────┘  │
│                                                             │
│ 3. Choose AI Model                                          │
│    ┌──────────────────────────────────┐                     │
│    │ Gemini 2.5 Flash (Recommended) ▼ │                     │
│    └──────────────────────────────────┘                     │
│                                                             │
│                    [▶ Start Analysis]                      │
│            The analysis will run in the background...      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Active Run Monitor
```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 Current Analysis                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Status: [🔵 RUNNING]                                        │
│                                                             │
│ Run ID: 20240107_143022_a1b2c3                             │
│ Model: gemini-2.5-flash                                   │
│ Max Rounds: 3                                              │
│ Started: 2024-01-07 14:30:22                               │
│                                                             │
│ Progress:                                                   │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 35%        │
│                                                             │
│ Question: "What are the top 5 products by revenue?"       │
│                                                             │
│                      [View Details]                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### History Page - Run List
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Analysis History                                         │
│ View past analyses and their results                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 20240107_143022_a1b2c3        [✅ COMPLETED]            │ │
│ │ 2024-01-07 14:30:22                                    │ │
│ │                                                        │ │
│ │ "What are the top 5 products by revenue?"             │ │
│ │                                                        │ │
│ │ Model: gemini-2.5-flash  Duration: 45s  Files: 2      │ │
│ │                             [View] [Delete]            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 20240106_082154_x9y8z7        [🔴 FAILED]             │ │
│ │ 2024-01-06 08:21:54                                    │ │
│ │                                                        │ │
│ │ "Calculate customer lifetime value by segment"        │ │
│ │                                                        │ │
│ │ Model: gpt-4  Duration: 120s  Files: 1                │ │
│ │                             [View] [Delete]            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Load More...]                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Results Detail Modal - Steps View
```
┌──────────────────────────────────────────────────────────────┐
│ Run Details                          [✅ COMPLETED]      [×]   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Run ID: 20240107_143022_a1b2c3                              │
│ Model: gemini-2.5-flash                                    │
│ Max Rounds: 3                                               │
│ Files: sales.csv, customers.xlsx                           │
│                                                              │
│ Original Question:                                          │
│ "What are the top 5 products by revenue?"                 │
│                                                              │
│ Analysis Steps                                              │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 1: Data Analysis [▼]                                │ │
│ └──────────────────────────────────────────────────────────┘ │
│   Prompt:                                                    │
│   Analyze the data and create a summary...                 │
│                                                              │
│   Generated Code:                                           │
│   ┌──────────────────────────────────────────────────────┐  │
│   │ import pandas as pd                                 │  │
│   │ df = pd.read_csv('sales.csv')                       │  │
│   │ print(df.describe())                                │  │
│   │ print(df.info())                                    │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
│   Result:                                                    │
│   ┌──────────────────────────────────────────────────────┐  │
│   │ Index: 1000 entries, 0 to 999                      │  │
│   │ Columns: product, revenue, quantity, region        │  │
│   │ Data types: object, float64, int64, object         │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 2: Analysis & Planning [►]                          │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Step 3: Code Generation & Execution [►]                 │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Diagram

```
┌──────────────┐
│ User Browser │
└──────┬───────┘
       │ Opens http://localhost:5000
       ↓
┌────────────────────────────────────┐
│   Frontend (HTML/CSS/JavaScript)   │
│  • File Upload Form                │
│  • Query Input                     │
│  • Real-time Status Updates        │
│  • Results Display                 │
└──────┬───────────────────────┬─────┘
       │ REST API Calls        │
       ↓                       ↓
  [POST /api/run/start]   [GET /api/run/<id>/status]
       │                       │
       ↓                       ↑
┌─────────────────────────────────────┐
│     Backend (Flask Server)          │
│  • Route Handlers                   │
│  • File Management                  │
│  • Background Tasks                 │
│  • Status Tracking                  │
└──────┬──────────────────────────────┘
       │ Spawns background thread
       ↓
┌─────────────────────────────────────┐
│     Tahlil Pipeline                │
│  • Data Analysis                    │
│  • Planning                         │
│  • Code Generation                  │
│  • Execution                        │
│  • Debugging                        │
│  • Results Formatting               │
└──────┬──────────────────────────────┘
       │ Stores artifacts
       ↓
┌─────────────────────────────────────┐
│    Artifact Storage                 │
│    runs/<run_id>/                   │
│    ├── steps/                       │
│    │   ├── step_1/                  │
│    │   ├── step_2/                  │
│    │   └── step_3/                  │
│    └── final_output/                │
└─────────────────────────────────────┘
       │ Frontend polls for updates
       ↓
    [Results Displayed]
```

## 🎭 Component Architecture

```
Frontend Layer (Browser)
├── index.html (Structure)
├── styles.css (Presentation)
└── app.js (Behavior)
    ├── File Management
    ├── Query Submission
    ├── Status Polling
    ├── Results Display
    └── Settings Management

API Layer (Express Routes)
├── /api/run/start
├── /api/run/<id>/status
├── /api/run/<id>/results
├── /api/run/<id>/steps
├── /api/data/upload
└── /api/data/list

Business Logic Layer
├── Run Management
├── File Handling
├── Status Tracking
└── Background Execution

Data Layer
├── data/ (Uploaded files)
└── runs/ (Results & artifacts)
```

## 📱 Responsive Design Breakpoints

```
Desktop (1200px+)        Tablet (768px-1199px)    Mobile (< 768px)
│                        │                        │
│ Full layout            │ Optimized layout       │ Single column
│ Side by side           │ Adjusted spacing       │ Stacked elements
│ Multiple columns       │ Readable text          │ Touch-friendly
│ Hover effects          │ Touch-friendly buttons │ Large buttons
│                        │                        │
```

## 🎯 User Journey Map

```
                            Start
                             │
                             ↓
                    Open http://localhost:5000
                             │
                             ↓
                     ┌──────────────┐
                     │   Home Page  │
                     └──────┬───────┘
                            │
                ┌───────────┼───────────┐
                ↓           ↓           ↓
          Upload Files   Type Query   Select Model
                │           │           │
                └───────────┼───────────┘
                            │
                            ↓
                   Click "Start Analysis"
                            │
                            ↓
              ┌─────────────────────────┐
              │  Real-time Monitor     │
              │  - Progress Bar        │
              │  - Status Updates      │
              │  - Auto-refresh        │
              └────────────┬────────────┘
                           │
                    ┌──────┴──────┐
                    ↓             ↓
              Running         Completed
                    │             │
                    │             ↓
                    │      Click "View Details"
                    │             │
                    │             ↓
                    │      ┌──────────────┐
                    │      │ Results Modal│
                    │      │ - Step List  │
                    │      │ - Prompts    │
                    │      │ - Code       │
                    │      │ - Results    │
                    │      └──────┬───────┘
                    │             │
                    │             ↓
                    │      Explore Steps
                    │             │
                    └─────┬───────┘
                          │
                          ↓
                    Run History or
                    New Analysis
```

## 🎨 Color Scheme

```
Primary: Blue (#2563eb)
├── Dark: #1e40af (hover)
├── Light: #3b82f6 (active)
└── Pale: #f0f7ff (background)

Success: Green (#10b981)
├── Dark: #166534
└── Pale: #dcfce7

Warning: Amber (#f59e0b)
├── Dark: #b45309
└── Pale: #fef3c7

Error: Red (#ef4444)
├── Dark: #991b1b
└── Pale: #fee2e2

Neutral:
├── Text: #1f2937
├── Border: #d1d5db
└── Background: #f9fafb
```

## 📊 Status Indicators

```
Running:   🔵 [RUNNING]   - Blue badge, spinning animation
Completed: ✅ [COMPLETED] - Green badge, checkmark
Failed:    ❌ [FAILED]    - Red badge, error icon
Error:     ⚠️  [ERROR]     - Red badge, warning icon
```

## 🔔 Toast Notifications

```
Success (Green):
┌─────────────────────────────────┐
│ ✅ File uploaded successfully!  │
└─────────────────────────────────┘

Error (Red):
┌─────────────────────────────────┐
│ ❌ Error uploading file         │
└─────────────────────────────────┘

Warning (Amber):
┌─────────────────────────────────┐
│ ⚠️  Please select a data file    │
└─────────────────────────────────┘
```

## 📂 Directory Structure Visualization

```
Tahlil/
│
├── 📄 app.py                    ← Flask backend
├── 📄 dsstar.py                 ← Core engine
├── 📄 provider.py               ← Model providers
├── 📄 config.yaml               ← Settings
├── 📄 prompt.yaml               ← AI prompts
├── 📄 pyproject.toml            ← Dependencies
│
├── 📁 frontend/                 ← Web interface
│   ├── index.html              ← HTML structure
│   ├── styles.css              ← Styling
│   └── app.js                  ← Logic
│
├── 📁 data/                     ← User uploads
│   ├── sales.csv
│   └── customers.xlsx
│
├── 📁 runs/                     ← Analysis results
│   ├── 20240107_143022_a1b2c3/
│   │   ├── steps/
│   │   ├── final_output/
│   │   └── metadata.json
│   └── 20240106_082154_x9y8z7/
│
├── 📄 run_web.bat               ← Windows startup
├── 📄 run_web.sh                ← Linux/Mac startup
│
└── 📚 Documentation/
    ├── START_HERE.md
    ├── QUICKSTART.md
    ├── FRONTEND_GUIDE.md
    ├── WEBAPP_SETUP.md
    ├── FRONTEND_IMPLEMENTATION.md
    └── DELIVERABLES.md
```

## 🎬 Typical Session Timeline

```
Time    Event                           UI Display
────────────────────────────────────────────────────
00:00   User opens browser              Home page loads
00:02   Uploads data file               File listed
00:05   Types question                  Text in textarea
00:10   Selects model                   Model selected
00:12   Clicks "Start Analysis"         Confirmation toast
00:15   Active run appears              Progress bar: 10%
00:20   Analysis running                Progress bar: 30%
00:30   Analysis running                Progress bar: 60%
00:45   Analysis complete               Status: COMPLETED
00:50   User clicks "View Details"      Results modal opens
01:00   User explores steps             Steps displayed
01:30   User closes modal               Back to home
01:35   User clicks "History"           Run history shown
```

---

**Visual Overview Complete!** 🎨

For more details, see:
- QUICKSTART.md (quick reference)
- FRONTEND_GUIDE.md (detailed guide)
- WEBAPP_SETUP.md (setup help)
