# Analysis Output Format - How Tahlil Delivers Results

## What Happens When You Ask for "5 Top Sales in Bar Chart"

### 📊 How It Works

**Step 1: You Submit Query**
- You ask: "Show me 5 top sales in a bar chart"
- File: OtherSales.xlsx

**Step 2: System Generates Python Code**
- ANALYZER: Reads your file, creates Python code to:
  - Load the Excel file
  - Process the data
  - Create the bar chart visualization
- CODER: Generates matplotlib/plotly Python code
- Code example:
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_excel('data/OtherSales.xlsx')
top_5 = df.nlargest(5, 'Sales')
top_5.plot(kind='bar', figsize=(10, 6))
plt.title('Top 5 Sales')
plt.savefig('output/chart.png')
plt.show()
```

**Step 3: Code Executes**
- Python code runs in the backend
- Creates chart image file (PNG/HTML)
- Outputs any printed messages

**Step 4: Results Displayed**
- Image/Chart is saved in `final_output/` directory
- Results shown in modal:
  - Code that was generated
  - Output text
  - Chart image (if generated)

---

## Current Output Types

### Text Output ✅
- Print statements from code execution
- Data summaries
- Statistics
- Lists

Example:
```
Top 5 Sales:
Product A: $50,000
Product B: $45,000
Product C: $40,000
Product D: $35,000
Product E: $30,000
```

### Chart/Image Output ✅
- Matplotlib PNG images
- Plotly HTML interactive charts
- Excel charts
- Any visualizations the code generates

Currently shown as:
- **Image files** in `final_output/chart.png`
- **HTML files** that can be embedded
- **SVG files** for vector graphics

---

## Where Results Are Saved

```
runs/
└── 20251208_061422_abd704/
    ├── final_output/
    │   ├── result.json          ← Final output text
    │   ├── chart.png            ← Generated image
    │   └── report.html          ← Generated HTML report
    ├── steps/
    │   ├── 000_analyzer/
    │   │   └── result.txt       ← Analysis code
    │   ├── 001_planner/
    │   ├── 002_coder/
    │   │   └── result.txt       ← Generated Python code
    │   └── ...
    └── logs/
        └── pipeline.log         ← Execution logs
```

---

## Frontend Display

### Modal Shows:
1. **Run Metadata**
   - Status, Model, File name
   - Start/End times

2. **Original Question**
   - Your exact query

3. **Analysis Steps** (collapsible)
   - Step 1: Analyzer prompt + response
   - Step 2: Coder prompt + generated code
   - Step 3: Execution result
   - ...

4. **Final Results**
   - Text output from execution
   - Charts/images embedded
   - Error messages if any

---

## Types of Output Generated

### 1. Text Analysis 📋
**Request**: "Show me top 5 sales"
**Output**: 
```
Top 5 Sales:
1. Product A: $50,000
2. Product B: $45,000
...
```

### 2. Chart Visualization 📊
**Request**: "Show me top 5 sales in bar chart"
**Output**: 
```
Generates and saves: chart.png
Shows matplotlib/plotly bar chart
```

### 3. Statistical Report 📈
**Request**: "Analyze sales trends"
**Output**:
```
Generates: report.html
Shows: Interactive Plotly dashboard
Includes: Trends, patterns, forecasts
```

### 4. Data Export 📥
**Request**: "Give me top sales as CSV"
**Output**:
```
Generates: output.csv
Available for download
```

### 5. Multiple Charts 🎨
**Request**: "Compare sales by region in charts"
**Output**:
```
Generates: chart1.png (region A)
           chart2.png (region B)
           chart3.png (region C)
All displayed in results modal
```

---

## Image/Chart Display

### Current Implementation
- Charts/images saved in `final_output/` folder
- Frontend fetches them via `/api/run/{id}/results` endpoint
- Displayed in modal as:
  - **Embedded images** `<img src="...">`
  - **Embedded HTML** `<iframe>`
  - **Text with syntax highlighting**

### Enhanced Display (Future)
Could show:
- Side-by-side code + result
- Expandable chart views
- Download buttons
- Chart interactions

---

## Example: Bar Chart Flow

### You Submit:
```json
{
  "query": "Show me 5 top sales in bar chart",
  "files": ["OtherSales.xlsx"],
  "model": "gemini-2.0-flash"
}
```

### System Generates Code:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_excel('data/OtherSales.xlsx')

# Get top 5 sales
top_5 = df.nlargest(5, 'Sales')[['Product', 'Sales']]

# Create bar chart
plt.figure(figsize=(10, 6))
plt.bar(top_5['Product'], top_5['Sales'], color='skyblue')
plt.title('Top 5 Sales')
plt.xlabel('Product')
plt.ylabel('Sales ($)')
plt.xticks(rotation=45)

# Save and show
plt.savefig('final_output/chart.png', dpi=300, bbox_inches='tight')
print("Chart saved to final_output/chart.png")
plt.show()
```

### System Executes Code:
- Loads file ✓
- Creates dataframe ✓
- Generates chart ✓
- Saves as `final_output/chart.png` ✓
- Prints: "Chart saved to final_output/chart.png"

### Frontend Shows:
```
[Modal Opens]
┌─────────────────────────────────────┐
│ Run ID: 20251208_061422_abd704      │
│ Status: COMPLETED                   │
├─────────────────────────────────────┤
│ Analysis Steps                      │
│ ▼ Step 1: ANALYZER                 │
│   Code: [Shows python code]         │
│                                     │
│ ▼ Step 2: CODER                    │
│   Generated Code: [Shows code]      │
│   Result: [Shows output]            │
│                                     │
│ ▼ Step 3: Execution Result         │
│   [Shows bar chart image]           │
│   "Chart saved to final_output..."  │
│                                     │
└─────────────────────────────────────┘
```

---

## What Gets Returned

**Text Only**:
- Printed output from code
- Statistics and summaries
- Error messages

**Images**:
- PNG files from matplotlib
- SVG files from vector graphics
- PNG/JPG from other plotting libraries

**Interactive**:
- HTML files from Plotly
- Interactive dashboards
- Embedded visualizations

**Files**:
- CSV exports
- Excel files
- JSON data
- Any files the code generates

---

## Why Both Code + Results?

1. **Transparency** - See exactly what was generated
2. **Learning** - Understand how analysis was done
3. **Verification** - Confirm the logic is correct
4. **Reproducibility** - Run the code yourself
5. **Modification** - Edit and re-run if needed

---

## Summary

When you ask for a **"bar chart of top 5 sales"**:

✅ **You'll get:**
- The Python code that creates the chart
- The executed output (print statements)
- The actual chart image/visualization
- Stored in `final_output/` directory
- Displayed in the results modal

❌ **You won't get:**
- Raw data CSV (unless you ask for it)
- Interactive download (yet - could add)
- Multiple format options (yet - could add)

The system is **code-first**: it generates Python code, executes it, and shows you both the code and results together.
