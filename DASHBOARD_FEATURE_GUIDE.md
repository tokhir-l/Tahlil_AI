# Dashboard Generation Feature - Implementation Guide

## Answer: **YES** ✅

The platform **CAN** create full dashboards based on data sources. Here's how and in which ways:

---

## Current Capabilities (Already Working)

### What You Already Have:
1. ✅ **Plotly Support** - Can generate interactive HTML charts
2. ✅ **Multiple Chart Types** - Bar, line, pie, scatter, histogram
3. ✅ **HTML File Generation** - Saves to `final_output/` directory
4. ✅ **Frontend Display** - Shows HTML files in iframes
5. ✅ **Multiple Visualizations** - Can create multiple charts in one run

---

## How to Create Dashboards (3 Ways)

### **Way 1: Single Query Dashboard** (Easiest - Already Possible)

**How it works:**
- User asks: *"Create a dashboard with sales trends, top products, and regional breakdown"*
- AI generates Python code that creates multiple Plotly charts
- All charts saved as one HTML file or multiple files
- Frontend displays them together

**Example Query:**
```
"Create a complete dashboard showing:
1. Sales trends over time (line chart)
2. Top 10 products by revenue (bar chart)
3. Sales by region (pie chart)
4. Monthly comparison (bar chart)
Save everything in an interactive HTML dashboard"
```

**What AI Generates:**
```python
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load data
df = pd.read_excel('data/sales.xlsx')

# Create dashboard with subplots
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Sales Trends', 'Top Products', 'By Region', 'Monthly Comparison'),
    specs=[[{"type": "scatter"}, {"type": "bar"}],
           [{"type": "pie"}, {"type": "bar"}]]
)

# Chart 1: Sales trends
fig.add_trace(go.Scatter(x=df['Date'], y=df['Sales'], name='Sales'), row=1, col=1)

# Chart 2: Top products
top_products = df.nlargest(10, 'Revenue')
fig.add_trace(go.Bar(x=top_products['Product'], y=top_products['Revenue']), row=1, col=2)

# Chart 3: By region
region_sales = df.groupby('Region')['Sales'].sum()
fig.add_trace(go.Pie(labels=region_sales.index, values=region_sales.values), row=2, col=1)

# Chart 4: Monthly comparison
monthly = df.groupby('Month')['Sales'].sum()
fig.add_trace(go.Bar(x=monthly.index, y=monthly.values), row=2, col=2)

# Update layout
fig.update_layout(height=800, title_text="Sales Dashboard", showlegend=False)
fig.write_html('runs/{run_id}/final_output/dashboard.html')
print("Dashboard created with 4 interactive charts")
```

**Result:** Single HTML file with multiple interactive charts displayed together.

---

### **Way 2: Multi-Query Dashboard** (Moderate - Needs Enhancement)

**How it works:**
- User runs multiple queries, each creating a chart
- System combines all charts into one dashboard
- Uses a "dashboard builder" mode

**Implementation:**
1. Add "Dashboard Mode" toggle in frontend
2. When enabled, all queries add charts to a dashboard
3. Final query: "Generate dashboard" combines everything

**Example Flow:**
```
Query 1: "Show sales trends as line chart" → Chart 1 saved
Query 2: "Show top products as bar chart" → Chart 2 saved
Query 3: "Generate dashboard with all previous charts" → Combined dashboard
```

**What Needs to be Added:**
- Dashboard state tracking (which charts to include)
- Dashboard template generator
- Chart combination logic

---

### **Way 3: Auto-Dashboard Generation** (Advanced - Needs New Feature)

**How it works:**
- User uploads data
- System automatically analyzes data structure
- Generates comprehensive dashboard with:
  - Key metrics/KPIs
  - Most important visualizations
  - Data summaries
  - Insights

**Example Query:**
```
"Automatically create a complete dashboard for this sales data with all key insights"
```

**What AI Would Generate:**
- Automatically detects important columns
- Creates relevant chart types
- Calculates key metrics
- Generates comprehensive HTML dashboard

---

## Implementation Approaches

### **Approach 1: Enhance Prompt System** (Easiest)

**Modify `prompt.yaml` to add dashboard-specific prompts:**

```yaml
dashboard_generator: |
  You are an expert data analyst creating a comprehensive dashboard.
  # Data: {summaries}
  # User Request: {query}
  
  Your task:
  Create a complete interactive dashboard using Plotly that includes:
  1. Key metrics/KPIs at the top
  2. Multiple relevant visualizations (4-6 charts)
  3. Data summaries
  4. Interactive elements (filters, hover tooltips)
  
  Requirements:
  - Use plotly.graph_objects or plotly.express
  - Create subplots using make_subplots
  - Save as single HTML file: 'runs/{run_id}/final_output/dashboard.html'
  - Make it visually appealing with proper titles and labels
  - Include data tables for key metrics
  - Use appropriate chart types for each data type
  
  Output: Python code that generates the dashboard
```

**Modify `tahlil.py` to detect dashboard requests:**

```python
def _generate_output_guidelines(self, query: str) -> str:
    query_lower = query.lower()
    
    # Check if user wants a dashboard
    if any(word in query_lower for word in ['dashboard', 'complete dashboard', 'full dashboard', 'comprehensive dashboard']):
        return f"""Generate code that creates a comprehensive interactive dashboard.
- Use Plotly to create multiple charts in a single HTML file
- Use make_subplots to arrange 4-6 charts in a grid layout
- Include key metrics/KPIs at the top
- Save to 'runs/{self.config.run_id}/final_output/dashboard.html'
- Make it interactive with hover tooltips and filters
- Use appropriate chart types (bar, line, pie, scatter) based on data
- Print: "Dashboard created with X charts showing [summary]"
"""
    # ... rest of existing code
```

---

### **Approach 2: Add Dashboard Builder Agent** (More Robust)

**Create new agent in the pipeline:**

```python
def create_dashboard(self, data_desc: str, charts: List[Dict], query: str) -> str:
    """Create comprehensive dashboard from multiple charts."""
    self.progress.add_step("PHASE 3", "Creating dashboard", "in_progress")
    
    prompt = f"""Create a comprehensive dashboard HTML file that includes:
    
    Data Summary: {data_desc}
    Charts to Include: {json.dumps(charts, indent=2)}
    User Request: {query}
    
    Generate Python code using Plotly that:
    1. Creates a dashboard layout with subplots
    2. Includes all specified charts
    3. Adds key metrics summary
    4. Makes it interactive and visually appealing
    5. Saves to 'runs/{self.config.run_id}/final_output/dashboard.html'
    """
    
    result = self.controller.execute_step(
        "dashboard_builder",
        step_func=lambda prompt=prompt, **kwargs: self._call_model("DASHBOARD_BUILDER", prompt),
        prompt=prompt
    )
    
    return self._extract_code_block(result)
```

---

### **Approach 3: Frontend Dashboard View** (Best UX)

**Add new dashboard view in frontend:**

1. **New Route:** `/dashboard` or dashboard tab
2. **Dashboard Builder UI:**
   - List of available charts from past runs
   - Drag-and-drop to add charts
   - Preview dashboard
   - Generate button

3. **Backend Endpoint:**
   ```python
   @app.route('/api/dashboard/create', methods=['POST'])
   def create_dashboard():
       data = request.json
       chart_ids = data.get('chart_ids', [])
       layout = data.get('layout', 'grid')  # grid, tabs, etc.
       
       # Combine charts into dashboard
       # Generate HTML
       # Return dashboard URL
   ```

---

## Specific Dashboard Types You Can Create

### 1. **Business Intelligence Dashboard**
- Sales metrics
- Revenue trends
- Product performance
- Regional breakdowns
- Time-series analysis

### 2. **Analytics Dashboard**
- User behavior
- Conversion funnels
- Traffic sources
- Engagement metrics
- Cohort analysis

### 3. **Financial Dashboard**
- Revenue vs expenses
- Profit margins
- Cash flow
- Budget vs actual
- Financial KPIs

### 4. **Operational Dashboard**
- Process metrics
- Efficiency indicators
- Resource utilization
- Performance tracking
- Operational KPIs

### 5. **Custom Dashboard**
- Any combination based on data
- User-defined metrics
- Custom visualizations
- Industry-specific views

---

## Technical Implementation Details

### **Using Plotly Dashboards (Recommended)**

**Advantages:**
- ✅ Interactive (zoom, pan, hover)
- ✅ Professional appearance
- ✅ Multiple chart types
- ✅ Responsive design
- ✅ Export options

**Example Code Structure:**
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Create subplot grid
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Chart 1', 'Chart 2', 'Chart 3', 'Chart 4'),
    specs=[[{"type": "scatter"}, {"type": "bar"}],
           [{"type": "pie"}, {"type": "bar"}]]
)

# Add charts
fig.add_trace(go.Scatter(...), row=1, col=1)
fig.add_trace(go.Bar(...), row=1, col=2)
# ... more charts

# Update layout
fig.update_layout(
    title_text="Complete Dashboard",
    height=1000,
    showlegend=True
)

# Save
fig.write_html('dashboard.html')
```

---

### **Using Dash Framework (Advanced Option)**

**If you want more control:**
- Install Dash: `pip install dash`
- Create Dash app
- More customization options
- Better for complex dashboards

**Trade-off:** More complex, but more powerful

---

## Frontend Display Enhancements

### **Current State:**
- HTML files displayed in iframes ✅
- Can show single Plotly chart ✅

### **Enhancements Needed:**

1. **Full-Screen Dashboard View:**
   ```javascript
   // Add to app.js
   showDashboard(runId) {
       const dashboardUrl = `/api/run/${runId}/file/dashboard.html`;
       window.open(dashboardUrl, '_blank', 'fullscreen=yes');
   }
   ```

2. **Dashboard Gallery:**
   - List all dashboards created
   - Preview thumbnails
   - Quick access

3. **Dashboard Customization:**
   - User can select which charts to include
   - Choose layout (grid, tabs, accordion)
   - Customize colors/themes

---

## Example User Queries That Create Dashboards

### **Simple Dashboard:**
```
"Create a dashboard with sales trends and top products"
```

### **Comprehensive Dashboard:**
```
"Generate a complete business dashboard showing:
- Revenue trends over time
- Top 10 products by sales
- Sales by region and category
- Monthly comparisons
- Key performance indicators"
```

### **Auto Dashboard:**
```
"Automatically create a dashboard for this dataset with all important insights"
```

### **Custom Dashboard:**
```
"Build a financial dashboard with:
- Revenue vs expenses chart
- Profit margin trends
- Top expense categories
- Cash flow visualization
Make it interactive and professional"
```

---

## Implementation Priority

### **Phase 1: Basic Dashboard (1-2 weeks)**
- ✅ Enhance prompts to detect "dashboard" keyword
- ✅ Generate multi-chart Plotly HTML
- ✅ Display in existing iframe
- **Who:** AI Engineer (prompts) + Backend Engineer (code execution)

### **Phase 2: Dashboard Builder (2-3 weeks)**
- Add dashboard mode toggle
- Track charts across queries
- Combine charts into dashboard
- **Who:** Backend Engineer + Frontend Engineer

### **Phase 3: Auto-Dashboard (3-4 weeks)**
- Auto-analyze data structure
- Generate relevant charts automatically
- Smart chart type selection
- **Who:** AI Engineer + Data Scientist

### **Phase 4: Advanced Features (4-6 weeks)**
- Dashboard templates
- Custom layouts
- Export options
- Sharing capabilities
- **Who:** Full team

---

## Cost Considerations

**No Additional Costs:**
- Plotly is free (open source)
- HTML generation is free
- No new dependencies needed

**Optional Enhancements:**
- Dash framework (free)
- Custom dashboard templates (development time)

---

## Summary

### **YES, it's possible!** ✅

**Current State:**
- ✅ Can generate single charts
- ✅ Can generate multiple charts
- ✅ Can create Plotly HTML files
- ✅ Frontend can display HTML

**What's Needed:**
1. **Enhance prompts** to detect dashboard requests
2. **Modify finalizer** to generate multi-chart layouts
3. **Optional:** Add dashboard builder UI
4. **Optional:** Add auto-dashboard generation

**Easiest Path:**
1. Update `_generate_output_guidelines()` in `tahlil.py`
2. Add dashboard detection logic
3. Enhance prompts in `prompt.yaml`
4. Test with dashboard queries

**Result:**
Users can ask: *"Create a complete dashboard"* and get a professional, interactive HTML dashboard with multiple charts, metrics, and insights!

---

## Next Steps

1. **Test Current Capability:**
   - Try query: "Create a dashboard with multiple charts showing [your data insights]"
   - See if AI generates multi-chart code

2. **Enhance if Needed:**
   - Add dashboard-specific prompts
   - Improve chart combination logic

3. **Add Frontend Support:**
   - Full-screen dashboard view
   - Dashboard gallery

4. **Iterate:**
   - Get user feedback
   - Add more dashboard types
   - Improve auto-generation

---

**The platform already has 90% of what's needed - it just needs to be directed to create dashboards instead of single charts!** 🚀

