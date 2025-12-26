# Tahlil Web Interface - User Guide

## Overview

The Tahlil Web Interface provides a user-friendly, modern web application for interacting with the Tahlil data science agent framework. It simplifies the process of uploading data, asking questions, and analyzing results without requiring command-line knowledge.

## Features

### 🏠 Home Page

**Interactive Query Builder**
- **Upload Data Files**: Drag-and-drop or click to upload CSV, Excel, JSON, TXT, or Parquet files
- **Ask Questions**: Write natural language questions about your data
- **Choose AI Model**: Select from available models (Gemini, GPT-4, etc.)
- **Start Analysis**: Submit your query and monitor progress in real-time

**Active Run Monitor**
- Track the progress of the current analysis
- View status (Running, Completed, Failed)
- See which model is being used and configuration details
- Access detailed results with one click

### 📊 History Page

**Run History**
- View all past analyses in chronological order
- See the query, model, number of files, and duration for each run
- Quick status indicators (color-coded)
- Click "View" to see detailed results and all generated artifacts

**Run Details**
- Complete run metadata (ID, timestamp, configuration)
- Step-by-step breakdown of the analysis pipeline
- For each step, view:
  - **Prompt**: The AI instruction sent to the model
  - **Generated Code**: The Python code created to solve the step
  - **Result**: The execution output
- Expandable/collapsible step cards for easy navigation

### ⚙️ Settings Page

**Configuration Options**
- **Maximum Refinement Rounds**: How many times Tahlil will refine its analysis (1-10)
- **Execution Timeout**: Maximum time allowed for code execution in seconds
- Settings are saved to your browser's local storage

## How to Use

### Starting an Analysis

1. **Go to Home Tab**
   - Click the "Home" button in the navigation menu

2. **Upload Data Files**
   - Click the file upload area or drag files directly
   - Supported formats: CSV, Excel, JSON, TXT, Parquet
   - You can upload multiple files

3. **Ask Your Question**
   - Type a natural language question about your data
   - Examples:
     - "What is the average sales by region?"
     - "Identify trends in customer behavior"
     - "Which products have the highest profit margins?"

4. **Choose a Model**
   - Select from available AI models
   - Recommended: "Gemini 2.5 Flash" (fastest and most capable)

5. **Click "Start Analysis"**
   - The system will begin processing
   - You'll see a confirmation toast notification
   - The active run card will appear below

6. **Monitor Progress**
   - Watch the progress bar as the analysis runs
   - The status updates automatically every 2 seconds
   - When complete, click "View Details" to see results

### Viewing Results

1. **Access History**
   - Click the "History" tab
   - Scroll through past analyses

2. **Open Run Details**
   - Click the "View" button on any run
   - A modal window will open showing:
     - Run metadata
     - Original question
     - All analysis steps
     - Generated code and results

3. **Explore Steps**
   - Click on any step to expand/collapse it
   - Review the AI's thought process
   - Examine generated code for accuracy
   - Check results for correctness

### Managing Data

**Uploaded Files**
- Files are stored in the `data/` directory
- Accessible to all future analyses
- Can be reused across multiple runs

**Run Artifacts**
- All artifacts stored in `runs/<run_id>/`
- Includes: prompts, code, results, metadata
- Organized by step for easy navigation

**Delete Runs**
- Click "Delete" on any run in the history
- Removes all associated artifacts
- Action cannot be undone

## Understanding the Analysis Pipeline

Tahlil executes a multi-agent pipeline:

1. **Analyzer**: Inspects your data and creates summaries
2. **Planner**: Creates an initial plan to answer your question
3. **Coder**: Writes Python code to execute the current step
4. **Executor**: Runs the code and captures results
5. **Debugger**: Fixes code errors automatically
6. **Verifier**: Checks if results answer the question
7. **Router**: Decides next steps (refine or finalize)
8. **Finalizer**: Formats final results in user-friendly format

## Latest Features

### User-Friendly Output Formatting
- **Automatic Table Detection**: When you ask questions with keywords like "show", "find", "identify", "give", the system automatically formats results as tables
- **Chart/Graph Display**: Visualizations are displayed inline with download options
- **AI-Powered Humanization**: Technical output is converted to natural, easy-to-understand language
- **Smart Formatting**: Output adapts to your question type (table, chart, or text explanation)

### Real-Time Progress Updates
- **Dynamic Status Messages**: See what's happening in real-time:
  - "Analyzing your data..."
  - "Planning analysis..."
  - "Generating code..."
  - "Executing code..."
- **Progress Tracking**: Visual indicators show which phase is active
- **Stop/Cancel**: Cancel active analyses if needed

### Feedback System
- **Quality Improvement**: Provide feedback on results (helpful/not helpful)
- **Issue Reporting**: Report specific problems (formatting, accuracy, etc.)
- **Continuous Learning**: Your feedback helps improve the platform

### Enhanced Results Display
- **Expandable Process Details**: View detailed step-by-step process (minimized by default)
- **Code Visibility**: See all generated code for transparency
- **Download Options**: Download charts, graphs, and result files
- **Table Formatting**: Beautiful HTML tables with explanations below

## Tips & Best Practices

### Writing Good Questions

✅ **Good Examples:**
- "What are the top 5 products by revenue?"
- "Calculate the monthly growth rate over the past year"
- "Identify outliers in the dataset"
- "Compare performance metrics across regions"

❌ **Avoid:**
- Vague questions: "What's interesting about this data?"
- Questions needing external data: "Compare to market averages"
- Questions about non-existent columns
- Overly complex multi-step analyses (break them down)

### Data Preparation

Before uploading:
- Ensure consistent formatting (no mixed types in columns)
- Include headers in the first row
- Remove or document missing values
- Use standard date formats (YYYY-MM-DD)

### Performance Tips

- Smaller datasets analyze faster
- Simple questions complete in seconds
- Complex analyses may take several rounds
- Use reasonable timeout values (60-120 seconds)
- Lower refinement rounds for quicker results (1-2 vs. 5)

## API Endpoints (For Developers)

The web interface uses a REST API:

```
POST /api/run/start              - Start new analysis
GET  /api/run/<run_id>/status    - Get run status
GET  /api/run/<run_id>/progress  - Get detailed progress
GET  /api/run/<run_id>/results   - Get final results
GET  /api/run/<run_id>/steps     - Get all steps
POST /api/run/<run_id>/cancel   - Cancel active run
GET  /api/run/<run_id>/file/<filename> - Download result file
GET  /api/runs/list              - List all runs
DELETE /api/runs/delete/<run_id> - Delete a run
POST /api/data/upload            - Upload file
GET  /api/data/list              - List data files
DELETE /api/data/delete/<file>   - Delete file
POST /api/humanize               - Humanize technical data
POST /api/feedback               - Submit user feedback
GET  /api/config/models          - Get available models
```

## Troubleshooting

### Analysis Takes Too Long

- The run is still executing (check status)
- Try a simpler question
- Increase execution timeout in settings
- Reduce maximum refinement rounds

### Analysis Failed

- Check that data file format is correct
- Verify question is answerable with provided data
- Ensure required columns exist in data
- Try splitting complex analyses into simpler steps

### Files Not Uploading

- Check file size (very large files may take time)
- Verify file format is supported
- Ensure disk space is available
- Try uploading one file at a time

### Data Not Processing

- Confirm file was successfully uploaded
- Check that filenames are correct
- Verify data format matches file extension
- Look at step details for parsing errors

## Configuration

### Environment Variables

```
GEMINI_API_KEY=your_key     # For Gemini models
OPENAI_API_KEY=your_key     # For GPT models
OLLAMA_HOST=http://...      # For Ollama models (optional)
```

### Directories

```
data/          - Upload data files here
runs/          - Stores analysis artifacts
frontend/      - Web interface files
```

## Running the Web Application

### Installation

```bash
# Install dependencies
pip install flask flask-cors google-generativeai openai ollama pyyaml pandas

# Or with uv
uv pip install flask flask-cors
```

### Starting the Server

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Development Mode

For development with auto-reload:

```bash
python -m flask --app app run --debug
```

## Browser Compatibility

- Chrome/Edge: ✅ Recommended
- Firefox: ✅ Supported
- Safari: ✅ Supported
- Mobile: ✅ Responsive design

## Storage & Privacy

- **Local Storage**: Settings saved in browser
- **Server Storage**: Analysis artifacts stored in `runs/` directory
- **Data Files**: Stored in `data/` directory
- **Privacy**: No data sent to external servers except AI APIs

## Support & Documentation

- **Backend Docs**: See `README.md` for Tahlil framework details
- **Code Examples**: View generated code in step details
- **Error Messages**: Check browser console (F12) for details

---

**Version**: 1.0.0  
**Last Updated**: December 2024
